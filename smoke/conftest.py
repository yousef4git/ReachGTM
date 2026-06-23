"""Pytest fixtures and helpers for the production smoke-test suite.

This suite is intentionally NOT part of the normal `pytest backend/tests/` /
`pytest agents/tests/` runs (the root `pyproject.toml` restricts `testpaths` to
those two directories). It is meant to be run explicitly against deployed
(production/staging) URLs:

    SMOKE_BACKEND_URL=https://... .venv/bin/python -m pytest smoke/ -v

Environment-variable contract:
    SMOKE_BACKEND_URL    Base URL of the deployed FastAPI backend.
    SMOKE_AGENTS_URL     Base URL of the deployed agents service.
    SMOKE_FRONTEND_URL   Base URL of the deployed static frontend.
    SMOKE_TEST_EMAIL     (optional) Credentials for the authenticated flow.
    SMOKE_TEST_PASSWORD  (optional) Credentials for the authenticated flow.

When a required URL (or credential) is unset, the corresponding fixture calls
``pytest.skip(...)`` with a clear reason so the suite NEVER fails in normal CI
where these env vars are absent.
"""

from __future__ import annotations

import os
import time

import httpx
import pytest

# Default request timeout (seconds) for smoke HTTP calls.
SMOKE_HTTP_TIMEOUT = float(os.environ.get("SMOKE_HTTP_TIMEOUT", "30"))


def _require_url(var_name: str) -> str:
    """Return the URL from ``var_name`` or skip the test if it is unset."""
    value = os.environ.get(var_name, "").strip()
    if not value:
        pytest.skip(
            f"{var_name} is not set; skipping smoke test "
            f"(set {var_name} to a deployed URL to run it)."
        )
    return value.rstrip("/")


@pytest.fixture(scope="session")
def backend_url() -> str:
    """Base URL of the deployed backend; skips if SMOKE_BACKEND_URL is unset."""
    return _require_url("SMOKE_BACKEND_URL")


@pytest.fixture(scope="session")
def agents_url() -> str:
    """Base URL of the deployed agents service; skips if SMOKE_AGENTS_URL unset."""
    return _require_url("SMOKE_AGENTS_URL")


@pytest.fixture(scope="session")
def frontend_url() -> str:
    """Base URL of the deployed frontend; skips if SMOKE_FRONTEND_URL is unset."""
    return _require_url("SMOKE_FRONTEND_URL")


@pytest.fixture(scope="session")
def smoke_credentials() -> tuple[str, str]:
    """(email, password) for the authenticated flow.

    Skips when either SMOKE_TEST_EMAIL or SMOKE_TEST_PASSWORD is unset, so the
    authenticated-flow tests only run when real credentials are provided.
    """
    email = os.environ.get("SMOKE_TEST_EMAIL", "").strip()
    password = os.environ.get("SMOKE_TEST_PASSWORD", "").strip()
    if not email or not password:
        pytest.skip(
            "SMOKE_TEST_EMAIL / SMOKE_TEST_PASSWORD are not set; skipping "
            "authenticated smoke flow (set both to run it)."
        )
    return email, password


@pytest.fixture(scope="session")
def http_client() -> httpx.Client:
    """A sync httpx client with a sensible default timeout and redirects on."""
    with httpx.Client(timeout=SMOKE_HTTP_TIMEOUT, follow_redirects=True) as client:
        yield client


@pytest.fixture(scope="session")
def wait_for_healthy():
    """Return the :func:`wait_for_healthy` polling helper (as a fixture).

    Exposed as a fixture rather than a module-level import so the smoke tests
    don't have to import this ``conftest`` by name (the repo root has its own
    ``conftest.py``, which would shadow it under ``--import-mode=importlib``).
    """
    return _wait_for_healthy


def _wait_for_healthy(
    url: str,
    timeout: float = 60.0,
    interval: float = 2.0,
    expected_status: int = 200,
) -> httpx.Response:
    """Poll ``url`` until it returns ``expected_status`` or ``timeout`` elapses.

    Used for zero-downtime verification: after a deploy we keep polling the
    health endpoint until the new revision is serving. Returns the successful
    response; raises ``AssertionError`` (failing the test) if the endpoint never
    becomes healthy within ``timeout`` seconds.

    Args:
        url: Full URL to poll (e.g. ``https://api.example.com/health``).
        timeout: Maximum number of seconds to keep retrying.
        interval: Seconds to sleep between attempts.
        expected_status: HTTP status code that counts as healthy.
    """
    deadline = time.monotonic() + timeout
    last_error: str | None = None
    with httpx.Client(timeout=SMOKE_HTTP_TIMEOUT, follow_redirects=True) as client:
        while True:
            try:
                resp = client.get(url)
                if resp.status_code == expected_status:
                    return resp
                last_error = f"status {resp.status_code}"
            except httpx.HTTPError as exc:  # network blip during rollout
                last_error = repr(exc)

            if time.monotonic() >= deadline:
                raise AssertionError(
                    f"{url} did not become healthy within {timeout}s "
                    f"(last result: {last_error})."
                )
            time.sleep(interval)
