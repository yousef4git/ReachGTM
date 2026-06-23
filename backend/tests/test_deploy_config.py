"""Validate the Railway deploy config + migration wiring (PR #21).

These are static checks — they don't touch Railway or a database. They guard
against typos that would only surface at deploy time (wrong Dockerfile path,
hardcoded port instead of $PORT, missing healthcheck, broken migration path).
"""
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "config_rel, dockerfile_rel, app_path",
    [
        ("infra/railway/backend.json", "backend/Dockerfile", "backend.app.main:app"),
        ("infra/railway/agents.json", "agents/Dockerfile", "agents.app.main:app"),
    ],
)
def test_railway_service_config(config_rel, dockerfile_rel, app_path):
    config = json.loads((REPO_ROOT / config_rel).read_text())

    # Build: Dockerfile builder pointing at a real Dockerfile.
    assert config["build"]["builder"] == "DOCKERFILE"
    assert config["build"]["dockerfilePath"] == dockerfile_rel
    assert (REPO_ROOT / dockerfile_rel).is_file()

    deploy = config["deploy"]
    # Must bind to Railway's injected $PORT (not a hardcoded port) and run the app.
    assert "$PORT" in deploy["startCommand"]
    assert app_path in deploy["startCommand"]
    # Health + resilience.
    assert deploy["healthcheckPath"] == "/health"
    assert deploy["restartPolicyType"] == "ON_FAILURE"


def test_migration_script_targets_init_sql():
    script = (REPO_ROOT / "scripts/apply_migrations.sh").read_text()
    assert "DATABASE_URL" in script
    assert "init.sql" in script
    assert (REPO_ROOT / "backend/app/db/migrations/init.sql").is_file()


def test_init_sql_has_pgvector_and_hnsw():
    sql = (REPO_ROOT / "backend/app/db/migrations/init.sql").read_text().lower()
    assert "create extension" in sql and "vector" in sql
    assert "hnsw" in sql
