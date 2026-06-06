from fastapi import APIRouter, Depends, HTTPException, status, Request
from jose import jwt, JWTError
import asyncpg
from shared.schemas import RegisterRequest, LoginRequest, TokenResponse
from backend.app.db.connection import get_db
from backend.app.services import auth_service
from backend.app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

def _build_token_response(user: dict) -> TokenResponse:
    access = auth_service.create_access_token(user["id"], user["company_id"], user["role"])
    refresh = auth_service.create_refresh_token(user["id"], user["company_id"])
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.access_token_expire_minutes * 60,
    )

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, conn: asyncpg.Connection = Depends(get_db)):
    existing = await conn.fetchval("SELECT id FROM users WHERE email = $1", body.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = await auth_service.register_company_and_user(conn, body.email, body.password, body.company_name)
    return _build_token_response(user)

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, conn: asyncpg.Connection = Depends(get_db)):
    user = await auth_service.authenticate_user(conn, body.email, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return _build_token_response(user)

@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, conn: asyncpg.Connection = Depends(get_db)):
    body = await request.json()
    token = body.get("refresh_token", "")
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await conn.fetchrow(
            "SELECT id, company_id, role FROM users WHERE id = $1",
            payload["sub"],
        )
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return _build_token_response(dict(user))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.post("/invite")
async def invite(request: Request, conn: asyncpg.Connection = Depends(get_db)):
    # TODO Epic 1 PR #4 — requires owner/admin role check
    company_id = request.state.company_id
    user_id = request.state.user_id
    body = await request.json()
    role = body.get("role", "member")
    token = auth_service.create_invite_token(company_id, user_id, role)
    return {"invite_token": token, "invite_url": f"/register?invite={token}"}

@router.post("/accept-invite", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def accept_invite(request: Request, conn: asyncpg.Connection = Depends(get_db)):
    body = await request.json()
    invite_token = body.get("invite_token", "")
    try:
        payload = jwt.decode(invite_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "invite":
            raise HTTPException(status_code=400, detail="Invalid invite token")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired invite")

    async with conn.transaction():
        user = await conn.fetchrow(
            """INSERT INTO users (company_id, email, hashed_password, role)
               VALUES ($1, $2, $3, $4) RETURNING id, company_id, role""",
            payload["company_id"], body["email"],
            auth_service.hash_password(body["password"]), payload["role"],
        )
    return _build_token_response(dict(user))
