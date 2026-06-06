import time
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as aioredis
from backend.app.config import settings

WINDOW_SECONDS = 60
MAX_REQUESTS = 100

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._redis: aioredis.Redis | None = None

    def _get_redis(self) -> aioredis.Redis:
        if not self._redis:
            self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        return self._redis

    async def dispatch(self, request: Request, call_next):
        company_id = getattr(request.state, "company_id", None)
        if not company_id:
            return await call_next(request)

        r = self._get_redis()
        key = f"rate:{company_id}"
        now = time.time()
        window_start = now - WINDOW_SECONDS

        pipe = r.pipeline()
        pipe.zremrangebyscore(key, "-inf", window_start)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, WINDOW_SECONDS * 2)
        results = await pipe.execute()

        request_count = results[2]
        if request_count > MAX_REQUESTS:
            retry_after = int(WINDOW_SECONDS - (now - window_start))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
