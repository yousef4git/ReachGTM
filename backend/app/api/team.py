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
