from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError
from backend.app.config import settings

AUTH_ROUTES = {"/api/v1/auth/login", "/api/v1/auth/register", "/health"}


def _unauthorized(detail: str) -> JSONResponse:
    # NOTE: return (not raise) — this is a BaseHTTPMiddleware, so a raised
    # HTTPException bypasses FastAPI's exception handler and becomes a 500.
    return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": detail})


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in AUTH_ROUTES or not request.url.path.startswith("/api/v1/"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return _unauthorized("Missing token")

        token = auth_header.removeprefix("Bearer ")
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        except JWTError:
            return _unauthorized("Invalid token")

        company_id: str = payload.get("company_id")
        if not company_id:
            return _unauthorized("Invalid token")

        request.state.company_id = company_id
        request.state.user_id = payload.get("sub")
        request.state.role = payload.get("role", "member")

        return await call_next(request)
