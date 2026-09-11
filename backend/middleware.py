import logging
import time

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.database.redis import redis_client

logger = logging.getLogger("app.http")

RATE_LIMIT = 100
RATE_WINDOW = 60
AUTH_RATE_LIMIT = 10
AUTH_RATE_WINDOW = 60

SKIP_PATHS = ("/docs", "/redoc", "/openapi.json", "/health")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = (time.perf_counter() - start) * 1000

        logger.info(
            "%s %s -> %s (%.1f ms)",
            request.method,
            request.url.path,
            response.status_code,
            duration
        )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in SKIP_PATHS or request.url.path.startswith("/docs"):
            return await call_next(request)

        client = request.client.host if request.client else "unknown"
        is_auth = request.url.path.startswith("/auth")

        limit = AUTH_RATE_LIMIT if is_auth else RATE_LIMIT
        window = AUTH_RATE_WINDOW if is_auth else RATE_WINDOW

        now = int(time.time())
        key = f"rl:{client}:{'auth' if is_auth else 'api'}:{now // window}"

        try:
            count = await redis_client.incr(key)
            await redis_client.expire(key, window + 5)
        except Exception:
            return await call_next(request)

        if count > limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"}
            )

        return await call_next(request)