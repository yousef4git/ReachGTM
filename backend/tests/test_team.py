"""Tests for the team RBAC endpoints (issue #30).

Network-free: the asyncpg connection is faked with a small scripted class so the
endpoints run without a real database. Deterministic.
"""
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import backend.app.api.team as team_api
from backend.app.db.connection import get_db
from backend.app.middleware.tenant import TenantMiddleware
from backend.app.services.auth_service import create_access_token


# ── Fake asyncpg connection ──────────────────────────────────────────────────

COMPANY_ID = uuid.uuid4()
OTHER_COMPANY_ID = uuid.uuid4()

OWNER_ID = uuid.uuid4()
ADMIN_ID = uuid.uuid4()
MEMBER_ID = uuid.uuid4()
OTHER_COMPANY_USER_ID = uuid.uuid4()


def _members():
    """Fresh seed each test so role mutations don't leak across cases."""
    return {
        str(OWNER_ID): {
            "id": OWNER_ID, "company_id": COMPANY_ID, "email": "owner@acme.test",
            "role": "owner", "is_active": True, "created_at": "2026-01-01T00:00:00",
        },
        str(ADMIN_ID): {
            "id": ADMIN_ID, "company_id": COMPANY_ID, "email": "admin@acme.test",
            "role": "admin", "is_active": True, "created_at": "2026-01-02T00:00:00",
        },
        str(MEMBER_ID): {
            "id": MEMBER_ID, "company_id": COMPANY_ID, "email": "member@acme.test",
            "role": "member", "is_active": True, "created_at": "2026-01-03T00:00:00",
        },
        str(OTHER_COMPANY_USER_ID): {
            "id": OTHER_COMPANY_USER_ID, "company_id": OTHER_COMPANY_ID,
            "email": "stranger@other.test", "role": "member", "is_active": True,
            "created_at": "2026-01-04T00:00:00",
        },
    }


def _company():
    """Fresh company row each test so name/plan mutations don't leak."""
    return {"id": COMPANY_ID, "name": "Acme Inc", "plan": "free"}


class FakeConn:
    """Minimal asyncpg.Connection stand-in driven by the seeded member rows.

    Endpoints use plain `row["col"]` access which works against the dicts here.
    """

    def __init__(self, members: dict, company: dict | None = None):
        self.members = members
        self.company = company if company is not None else _company()

    async def execute(self, query, *args):
        # Used by get_db for set_config and by the UPDATE path.
        q = query.strip().upper()
        if q.startswith("UPDATE USERS"):
            new_role, user_id, company_id = args
            row = self.members.get(str(user_id))
            if row and str(row["company_id"]) == str(company_id):
                row["role"] = new_role
        return "OK"

    async def fetch(self, query, *args):
        # GET members list: WHERE company_id = $1
        (company_id,) = args
        rows = [
            m for m in self.members.values()
            if str(m["company_id"]) == str(company_id)
        ]
        rows.sort(key=lambda m: ({"owner": 0, "admin": 1, "member": 2}[m["role"]], m["email"]))
        return rows

    async def fetchrow(self, query, *args):
        q = query.strip().upper()
        if "COMPANIES" in q:
            if q.startswith("UPDATE COMPANIES"):
                # Partial UPDATE: company_id is always the last arg; the leading
                # args are the SET values in (name, plan) order as built.
                set_clause = q.split("SET", 1)[1].split("WHERE", 1)[0]
                idx = 0
                if "NAME =" in set_clause:
                    self.company["name"] = args[idx]
                    idx += 1
                if "PLAN =" in set_clause:
                    self.company["plan"] = args[idx]
                    idx += 1
                company_id = args[-1]
                if str(self.company["id"]) != str(company_id):
                    return None
                return self.company
            # SELECT id, name, plan FROM companies WHERE id = $1
            (company_id,) = args
            if str(self.company["id"]) != str(company_id):
                return None
            return self.company
        if "RETURNING" in q:  # UPDATE users ... RETURNING
            new_role, user_id, company_id = args
            row = self.members.get(str(user_id))
            if row and str(row["company_id"]) == str(company_id):
                row["role"] = new_role
                return row
            return None
        # SELECT a single user by id (no company filter — endpoint checks scope)
        (user_id,) = args
        return self.members.get(str(user_id))

    async def fetchval(self, query, *args):
        # COUNT of active users in the company (seat usage).
        (company_id,) = args
        return sum(
            1
            for m in self.members.values()
            if str(m["company_id"]) == str(company_id) and m["is_active"]
        )


def _make_app(members: dict, company: dict | None = None) -> FastAPI:
    app = FastAPI()
    app.add_middleware(TenantMiddleware)
    app.include_router(team_api.router, prefix="/api/v1")

    async def _override_db():
        yield FakeConn(members, company)

    app.dependency_overrides[get_db] = _override_db
    return app


def _client(members: dict, company: dict | None = None) -> TestClient:
    return TestClient(_make_app(members, company))


def _auth(user_id, role):
    token = create_access_token(user_id, COMPANY_ID, role)
    return {"Authorization": f"Bearer {token}"}


# ── GET /team/members ────────────────────────────────────────────────────────

def test_members_list_returns_company_members_for_owner():
    members = _members()
    resp = _client(members).get("/api/v1/team/members", headers=_auth(OWNER_ID, "owner"))
    assert resp.status_code == 200
    body = resp.json()
    emails = {m["email"] for m in body}
    assert emails == {"owner@acme.test", "admin@acme.test", "member@acme.test"}
    # other company's user must not leak across the tenant boundary
    assert "stranger@other.test" not in emails
    # shape check
    assert set(body[0].keys()) >= {"id", "email", "role", "is_active", "created_at"}


def test_members_list_allows_admin():
    members = _members()
    resp = _client(members).get("/api/v1/team/members", headers=_auth(ADMIN_ID, "admin"))
    assert resp.status_code == 200
    assert len(resp.json()) == 3


def test_members_list_forbidden_for_member():
    members = _members()
    resp = _client(members).get("/api/v1/team/members", headers=_auth(MEMBER_ID, "member"))
    assert resp.status_code == 403


def test_members_list_requires_auth():
    members = _members()
    resp = _client(members).get("/api/v1/team/members")
    assert resp.status_code == 401


# ── PATCH /team/members/{id}/role ────────────────────────────────────────────

def test_owner_can_promote_member_to_admin():
    members = _members()
    resp = _client(members).patch(
        f"/api/v1/team/members/{MEMBER_ID}/role",
        json={"role": "admin"},
        headers=_auth(OWNER_ID, "owner"),
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"


def test_owner_can_demote_admin_to_member():
    members = _members()
    resp = _client(members).patch(
        f"/api/v1/team/members/{ADMIN_ID}/role",
        json={"role": "member"},
        headers=_auth(OWNER_ID, "owner"),
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "member"


def test_admin_caller_forbidden_on_patch():
    members = _members()
    resp = _client(members).patch(
        f"/api/v1/team/members/{MEMBER_ID}/role",
        json={"role": "admin"},
        headers=_auth(ADMIN_ID, "admin"),
    )
    assert resp.status_code == 403


def test_invalid_role_rejected():
    members = _members()
    resp = _client(members).patch(
        f"/api/v1/team/members/{MEMBER_ID}/role",
        json={"role": "superuser"},
        headers=_auth(OWNER_ID, "owner"),
    )
    assert resp.status_code == 400


def test_cannot_set_role_to_owner():
    members = _members()
    resp = _client(members).patch(
        f"/api/v1/team/members/{MEMBER_ID}/role",
        json={"role": "owner"},
        headers=_auth(OWNER_ID, "owner"),
    )
    assert resp.status_code == 400


def test_target_outside_company_is_not_found():
    members = _members()
    resp = _client(members).patch(
        f"/api/v1/team/members/{OTHER_COMPANY_USER_ID}/role",
        json={"role": "admin"},
        headers=_auth(OWNER_ID, "owner"),
    )
    assert resp.status_code == 404


def test_unknown_user_is_not_found():
    members = _members()
    resp = _client(members).patch(
        f"/api/v1/team/members/{uuid.uuid4()}/role",
        json={"role": "admin"},
        headers=_auth(OWNER_ID, "owner"),
    )
    assert resp.status_code == 404


def test_cannot_demote_an_owner():
    members = _members()
    resp = _client(members).patch(
        f"/api/v1/team/members/{OWNER_ID}/role",
        json={"role": "member"},
        headers=_auth(OWNER_ID, "owner"),
    )
    assert resp.status_code in (400, 403)


def test_cannot_change_own_role():
    # Use a second owner-less scenario: owner trying to change self is blocked
    # by the self-check even before the owner-protect check.
    members = _members()
    resp = _client(members).patch(
        f"/api/v1/team/members/{OWNER_ID}/role",
        json={"role": "admin"},
        headers=_auth(OWNER_ID, "owner"),
    )
    assert resp.status_code in (400, 403)


# ── GET /team/settings ───────────────────────────────────────────────────────

def test_settings_get_returns_plan_and_seats_for_owner():
    members = _members()
    resp = _client(members).get("/api/v1/team/settings", headers=_auth(OWNER_ID, "owner"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["company_id"] == str(COMPANY_ID)
    assert body["name"] == "Acme Inc"
    assert body["plan"] == "free"
    # 3 active members in COMPANY_ID (owner, admin, member); the stranger is in
    # another company and must not be counted.
    assert body["seat_count"] == 3
    assert body["seat_limit"] == team_api.PLAN_SEAT_LIMITS["free"]


def test_settings_get_allows_admin():
    members = _members()
    resp = _client(members).get("/api/v1/team/settings", headers=_auth(ADMIN_ID, "admin"))
    assert resp.status_code == 200
    assert resp.json()["plan"] == "free"


def test_settings_get_forbidden_for_member():
    members = _members()
    resp = _client(members).get("/api/v1/team/settings", headers=_auth(MEMBER_ID, "member"))
    assert resp.status_code == 403


def test_settings_get_reflects_plan_seat_limit():
    members = _members()
    company = {"id": COMPANY_ID, "name": "Acme Inc", "plan": "pro"}
    resp = _client(members, company).get("/api/v1/team/settings", headers=_auth(OWNER_ID, "owner"))
    assert resp.status_code == 200
    assert resp.json()["seat_limit"] == team_api.PLAN_SEAT_LIMITS["pro"]


# ── PATCH /team/settings ─────────────────────────────────────────────────────

def test_settings_patch_plan_updates_and_returns_new_limit():
    members = _members()
    resp = _client(members).patch(
        "/api/v1/team/settings",
        json={"plan": "pro"},
        headers=_auth(OWNER_ID, "owner"),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["plan"] == "pro"
    assert body["seat_limit"] == team_api.PLAN_SEAT_LIMITS["pro"]
    assert body["seat_count"] == 3


def test_settings_patch_name_renames_workspace():
    members = _members()
    resp = _client(members).patch(
        "/api/v1/team/settings",
        json={"name": "Globex"},
        headers=_auth(OWNER_ID, "owner"),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Globex"
    # plan unchanged
    assert body["plan"] == "free"


def test_settings_patch_forbidden_for_non_owner():
    members = _members()
    resp = _client(members).patch(
        "/api/v1/team/settings",
        json={"plan": "pro"},
        headers=_auth(ADMIN_ID, "admin"),
    )
    assert resp.status_code == 403


def test_settings_patch_invalid_plan_rejected():
    members = _members()
    resp = _client(members).patch(
        "/api/v1/team/settings",
        json={"plan": "unlimited"},
        headers=_auth(OWNER_ID, "owner"),
    )
    assert resp.status_code == 400


def test_settings_patch_blank_name_rejected():
    members = _members()
    resp = _client(members).patch(
        "/api/v1/team/settings",
        json={"name": "   "},
        headers=_auth(OWNER_ID, "owner"),
    )
    assert resp.status_code == 400


def test_settings_patch_empty_body_rejected():
    members = _members()
    resp = _client(members).patch(
        "/api/v1/team/settings",
        json={},
        headers=_auth(OWNER_ID, "owner"),
    )
    assert resp.status_code == 400
