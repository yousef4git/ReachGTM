"""Pytest bootstrap for the repo root.

`backend/app/config.py` and `agents/app/config.py` build a pydantic
`Settings()` at import time, which requires several env vars to be present.
Without them, simply importing the app (and therefore collecting the tests)
raises a validation error on a fresh clone.

We set safe dummy defaults here, before any test module imports the app.
`os.environ.setdefault` means a real environment (e.g. CI, or a developer's
`.env`) always wins — these only fill the gaps so `pytest` works out of the box.
These are NOT real secrets and must never be used outside tests.
"""

import os

os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:password@localhost:5432/reachgtm_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("JWT_SECRET", "test-secret-do-not-use-in-prod")
