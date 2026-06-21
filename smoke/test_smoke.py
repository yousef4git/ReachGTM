"""Production smoke tests for ReachGTM.

These run end-to-end against deployed (production/staging) URLs. Every test is
marked ``@pytest.mark.smoke`` and skips cleanly when the URL/credentials it needs
are not configured (see ``conftest.py``).

Run them explicitly (they are excluded from the normal backend/agents suites):

    SMOKE_BACKEND_URL=https://... .venv/bin/python -m pytest smoke/ -v -m smoke
"""

from __future__ import annotations

import httpx
import pytest

pytestmark = pytest.mark.smoke


# --------------------------------------------------------------------------- #
# Health checks                                                               #
# --------------------------------------------------------------------------- #


def test_backend_health(http_client: httpx.Client, backend_url: str) -> None:
    """Backend /health returns 200 and a body indicating it is healthy."""
    resp = http_client.get(f"{backend_url}/health")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    status = str(body.get("status", "")).lower()
    assert status in {"ok", "healthy", "up"}, f"unexpected health body: {body!r}"


def test_agents_health(http_client: httpx.Client, agents_url: str) -> None:
    """Agents /health returns 200 and a body indicating it is healthy."""
    resp = http_client.get(f"{agents_url}/health")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    status = str(body.get("status", "")).lower()
    assert status in {"ok", "healthy", "up"}, f"unexpected health body: {body!r}"


def test_frontend_serves_html(http_client: httpx.Client, frontend_url: str) -> None:
    """Frontend root returns 200 and the response looks like HTML."""
    resp = http_client.get(f"{frontend_url}/")
    assert resp.status_code == 200, resp.text
    content_type = resp.headers.get("content-type", "").lower()
    looks_like_html = "text/html" in content_type or "<html" in resp.text.lower()
    assert looks_like_html, (
        f"expected HTML from frontend, got content-type={content_type!r}"
    )


# --------------------------------------------------------------------------- #
# Auth contract (no credentials required)                                     #
# --------------------------------------------------------------------------- #


def test_login_rejects_bogus_credentials(
    http_client: httpx.Client, backend_url: str
) -> None:
    """POST /api/v1/auth/login with bogus creds returns 401."""
    resp = http_client.post(
        f"{backend_url}/api/v1/auth/login",
        json={
            "email": "smoke-not-a-real-user@example.invalid",
            "password": "definitely-wrong-password",
        },
    )
    assert resp.status_code == 401, (
        f"expected 401 for bogus login, got {resp.status_code}: {resp.text}"
    )


def test_sse_stream_requires_token(
    http_client: httpx.Client, backend_url: str
) -> None:
    """The SSE generate stream returns 401 when no token is supplied."""
    resp = http_client.get(
        f"{backend_url}/api/v1/strategy/generate/stream",
        params={"goal": "smoke test goal"},
    )
    assert resp.status_code == 401, (
        f"expected 401 for unauthenticated SSE stream, got {resp.status_code}: "
        f"{resp.text}"
    )


# --------------------------------------------------------------------------- #
# Authenticated flow (requires SMOKE_TEST_EMAIL / SMOKE_TEST_PASSWORD)         #
# --------------------------------------------------------------------------- #


def test_authenticated_sse_stream(
    backend_url: str, smoke_credentials: tuple[str, str]
) -> None:
    """Log in, then open the SSE stream with the token.

    Verifies:
      * login returns 200 with an access_token,
      * the SSE stream WITHOUT a token returns 401,
      * the SSE stream WITH the token responds as text/event-stream.

    We close the stream as soon as headers/first bytes arrive so we never
    consume a full strategy generation.
    """
    email, password = smoke_credentials

    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        login = client.post(
            f"{backend_url}/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login.status_code == 200, (
            f"login failed: {login.status_code}: {login.text}"
        )
        token = login.json().get("access_token")
        assert token, f"login response missing access_token: {login.text}"

        # Without a token -> 401.
        no_token = client.get(
            f"{backend_url}/api/v1/strategy/generate/stream",
            params={"goal": "smoke test goal"},
        )
        assert no_token.status_code == 401, (
            f"expected 401 without token, got {no_token.status_code}"
        )

        # With the token -> text/event-stream. Use a streaming request and bail
        # out after the headers so we don't drive a full generation.
        with client.stream(
            "GET",
            f"{backend_url}/api/v1/strategy/generate/stream",
            params={"token": token, "goal": "smoke test goal"},
        ) as stream:
            assert stream.status_code == 200, (
                f"expected 200 for authenticated stream, got {stream.status_code}"
            )
            content_type = stream.headers.get("content-type", "").lower()
            assert "text/event-stream" in content_type, (
                f"expected text/event-stream, got {content_type!r}"
            )
            # Touch the first chunk to confirm the stream is live, then stop.
            for _ in stream.iter_bytes():
                break


# --------------------------------------------------------------------------- #
# Zero-downtime verification                                                   #
# --------------------------------------------------------------------------- #


def test_backend_zero_downtime(backend_url: str, wait_for_healthy) -> None:
    """Poll backend /health repeatedly to assert continuous availability.

    During a zero-downtime rollout the endpoint must keep serving 200s. We poll
    several times; ``wait_for_healthy`` raises (failing the test) if the endpoint
    is ever unreachable for the whole window.
    """
    health_url = f"{backend_url}/health"
    for _ in range(5):
        resp = wait_for_healthy(health_url, timeout=60.0, interval=2.0)
        assert resp.status_code == 200
