from datetime import datetime, timedelta
from uuid import UUID
from passlib.context import CryptContext
from jose import jwt
import asyncpg
from backend.app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(user_id: UUID, company_id: UUID, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "company_id": str(company_id),
        "role": role,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def create_refresh_token(user_id: UUID, company_id: UUID) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": str(user_id),
        "company_id": str(company_id),
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def create_invite_token(company_id: UUID, invited_by: UUID, role: str = "member") -> str:
    expire = datetime.utcnow() + timedelta(days=7)
    payload = {
        "company_id": str(company_id),
        "invited_by": str(invited_by),
        "role": role,
        "exp": expire,
        "type": "invite",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

async def register_company_and_user(
    conn: asyncpg.Connection, email: str, password: str, company_name: str
) -> dict:
    async with conn.transaction():
        company = await conn.fetchrow(
            "INSERT INTO companies (name) VALUES ($1) RETURNING id", company_name
        )
        user = await conn.fetchrow(
            """INSERT INTO users (company_id, email, hashed_password, role)
               VALUES ($1, $2, $3, 'owner') RETURNING id, company_id, role""",
            company["id"], email, hash_password(password),
        )
    return dict(user)

async def authenticate_user(conn: asyncpg.Connection, email: str, password: str) -> dict | None:
    row = await conn.fetchrow(
        "SELECT id, company_id, hashed_password, role FROM users WHERE email = $1 AND is_active = TRUE",
        email,
    )
    if not row or not verify_password(password, row["hashed_password"]):
        return None
    return dict(row)
