"""Team RBAC endpoints (issue #30).

List company members and let an owner promote/demote them. Role and tenant come
from request.state (set by TenantMiddleware from the JWT). DB access mirrors
backend/app/api/auth.py — a pooled asyncpg connection via Depends(get_db).
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
import asyncpg

from backend.app.db.connection import get_db

router = APIRouter(prefix="/team", tags=["team"])

# Roles that may be assigned via the PATCH endpoint. "owner" is intentionally
# excluded — ownership is never granted through this API.
ASSIGNABLE_ROLES = {"member", "admin"}

# Static plan → seat-limit map (issue #31). There is no `seats` column in the
# DB; seat usage is derived from the active-user count and the limit comes from
# this map. Numbers are deliberate, not billed.
PLAN_SEAT_LIMITS = {"free": 3, "pro": 10, "enterprise": 100}
DEFAULT_SEAT_LIMIT = 3  # fallback when companies.plan is unknown/legacy


def _serialize(row) -> dict:
    return {
        "id": str(row["id"]),
        "email": row["email"],
        "role": row["role"],
        "is_active": row["is_active"],
        "created_at": (
            row["created_at"].isoformat()
            if hasattr(row["created_at"], "isoformat")
            else row["created_at"]
        ),
    }


@router.get("/members")
async def list_members(request: Request, conn: asyncpg.Connection = Depends(get_db)):
    """List users in the caller's company. Owner/admin only."""
    role = getattr(request.state, "role", "member")
    if role not in {"owner", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    company_id = request.state.company_id
    rows = await conn.fetch(
        """SELECT id, email, role, is_active, created_at
           FROM users
           WHERE company_id = $1
           ORDER BY
             CASE role WHEN 'owner' THEN 0 WHEN 'admin' THEN 1 ELSE 2 END,
             email""",
        company_id,
    )
    return [_serialize(r) for r in rows]


@router.patch("/members/{user_id}/role")
async def update_member_role(
    user_id: str,
    request: Request,
    conn: asyncpg.Connection = Depends(get_db),
):
    """Change a member's role. Owner only.

    Rules:
      * caller must be an owner (403 otherwise)
      * requested role must be one of {member, admin} (400 otherwise)
      * caller cannot change their own role (400)
      * target must exist and belong to the caller's company (404 otherwise)
      * the role of an existing owner cannot be changed (403)
    """
    role = getattr(request.state, "role", "member")
    if role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can change roles")

    body = await request.json()
    new_role = body.get("role")
    if new_role not in ASSIGNABLE_ROLES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")

    company_id = request.state.company_id
    caller_id = getattr(request.state, "user_id", None)
    if caller_id is not None and str(caller_id) == str(user_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot change your own role")

    target = await conn.fetchrow(
        "SELECT id, company_id, role FROM users WHERE id = $1",
        user_id,
    )
    if target is None or str(target["company_id"]) != str(company_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if target["role"] == "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="The owner's role cannot be changed")

    updated = await conn.fetchrow(
        """UPDATE users SET role = $1
           WHERE id = $2 AND company_id = $3
           RETURNING id, email, role, is_active, created_at""",
        new_role, user_id, company_id,
    )
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return _serialize(updated)


# ── Workspace settings (issue #31) ───────────────────────────────────────────


def _seat_limit_for(plan: str) -> int:
    """Seat limit for a plan, falling back to DEFAULT_SEAT_LIMIT if unknown."""
    return PLAN_SEAT_LIMITS.get(plan, DEFAULT_SEAT_LIMIT)


async def _settings_payload(conn: asyncpg.Connection, company_id) -> dict:
    """Build the settings response: company row + derived seat usage.

    seat_count = active users in the company; seat_limit = PLAN_SEAT_LIMITS[plan].
    """
    company = await conn.fetchrow(
        "SELECT id, name, plan FROM companies WHERE id = $1",
        company_id,
    )
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    seat_count = await conn.fetchval(
        "SELECT COUNT(*) FROM users WHERE company_id = $1 AND is_active = TRUE",
        company_id,
    )
    plan = company["plan"]
    return {
        "company_id": str(company["id"]),
        "name": company["name"],
        "plan": plan,
        "seat_count": int(seat_count or 0),
        "seat_limit": _seat_limit_for(plan),
    }


@router.get("/settings")
async def get_settings(request: Request, conn: asyncpg.Connection = Depends(get_db)):
    """Workspace settings for the caller's company. Owner/admin only."""
    role = getattr(request.state, "role", "member")
    if role not in {"owner", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    return await _settings_payload(conn, request.state.company_id)


@router.patch("/settings")
async def update_settings(request: Request, conn: asyncpg.Connection = Depends(get_db)):
    """Rename the workspace and/or switch its plan. Owner only.

    Rules:
      * caller must be an owner (403 otherwise)
      * body may contain `name` (non-empty string) and/or `plan`
      * `plan`, if given, must be a key in PLAN_SEAT_LIMITS (400 otherwise)
      * `name`, if given, must be non-empty after trimming (400 otherwise)
      * a body with neither field is a 400 (no-op)

    NOTE: Real billing is NOT wired up. Switching plans only updates
    companies.plan — no Stripe, no charge, no proration. This is a stub until
    payment integration lands.
    """
    role = getattr(request.state, "role", "member")
    if role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can change settings")

    body = await request.json()
    has_name = "name" in body
    has_plan = "plan" in body
    if not has_name and not has_plan:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nothing to update")

    name = None
    if has_name:
        raw = body.get("name")
        name = raw.strip() if isinstance(raw, str) else ""
        if not name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name cannot be blank")

    plan = None
    if has_plan:
        plan = body.get("plan")
        if plan not in PLAN_SEAT_LIMITS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid plan")

    company_id = request.state.company_id

    # Build a partial UPDATE from only the provided fields.
    sets = []
    args = []
    if name is not None:
        args.append(name)
        sets.append(f"name = ${len(args)}")
    if plan is not None:
        args.append(plan)
        sets.append(f"plan = ${len(args)}")
    args.append(company_id)
    updated = await conn.fetchrow(
        f"UPDATE companies SET {', '.join(sets)} WHERE id = ${len(args)} "
        "RETURNING id, name, plan",
        *args,
    )
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    seat_count = await conn.fetchval(
        "SELECT COUNT(*) FROM users WHERE company_id = $1 AND is_active = TRUE",
        company_id,
    )
    plan_val = updated["plan"]
    return {
        "company_id": str(updated["id"]),
        "name": updated["name"],
        "plan": plan_val,
        "seat_count": int(seat_count or 0),
        "seat_limit": _seat_limit_for(plan_val),
    }
