# Production smoke tests

End-to-end smoke checks that run against **deployed** ReachGTM URLs
(production or staging). They are intentionally separate from the unit suites:

- They live in the top-level `smoke/` directory, **not** under
  `backend/tests/` or `agents/tests/`.
- The root `pyproject.toml` restricts `testpaths` to the two unit-test
  directories, so a bare `pytest` from the repo root **never collects** these.
- Every test is marked `@pytest.mark.smoke` and **skips** (never fails) when the
  URL/credentials it needs are not set. Safe to run anywhere.

## Environment-variable contract

| Variable              | Required for                                  |
| --------------------- | --------------------------------------------- |
| `SMOKE_BACKEND_URL`   | backend health, auth contract, SSE guard, zero-downtime |
| `SMOKE_AGENTS_URL`    | agents health                                 |
| `SMOKE_FRONTEND_URL`  | frontend HTML check                           |
| `SMOKE_TEST_EMAIL`    | authenticated flow (with `SMOKE_TEST_PASSWORD`) |
| `SMOKE_TEST_PASSWORD` | authenticated flow (with `SMOKE_TEST_EMAIL`)  |
| `SMOKE_HTTP_TIMEOUT`  | optional; per-request timeout in seconds (default 30) |

When a variable is unset, the tests that depend on it skip with a clear reason.
With **no** variables set, the whole suite skips and exits 0.

## Running locally

Install the pinned deps and run with the project venv:

```bash
.venv/bin/python -m pip install -r smoke/requirements.txt

# All checks against staging/prod:
SMOKE_BACKEND_URL=https://reachgtm-backend.railway.app \
SMOKE_AGENTS_URL=https://reachgtm-agents.railway.app \
SMOKE_FRONTEND_URL=https://reachgtm.pages.dev \
  .venv/bin/python -m pytest smoke/ -v -m smoke

# Just the agents health check against a local instance:
SMOKE_AGENTS_URL=http://localhost:8011 \
  .venv/bin/python -m pytest smoke/ -v -m smoke -k agents_health
```

To also exercise the authenticated flow, set `SMOKE_TEST_EMAIL` and
`SMOKE_TEST_PASSWORD` for a real (seeded) account on the target environment.

## CI

`.github/workflows/smoke.yml` runs this suite on `workflow_dispatch` and via
`workflow_call`. The deploy workflows (`deploy.yml`, `deploy-frontend.yml`) call
it post-deploy (`needs: <deploy job>`) for zero-downtime verification.
