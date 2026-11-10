import asyncio
from collections.abc import Awaitable, Callable

from sqlalchemy import text

from backend.config import settings
from backend.database.db import engine
from backend.database.redis import redis_client

HealthCheck = Callable[[],Awaitable[object]]


async def check_postgres():
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
    return True


async def check_redis():
    if redis_client is None:
        return "disabled"
    return await redis_client.ping()


async def _bounded_status(check: HealthCheck,timeout_seconds: float) -> str:
    try:
        result = await asyncio.wait_for(check(),timeout=timeout_seconds)
        return "ok" if result is not False else "unavailable"
    except Exception:
        return "unavailable"


async def collect_readiness(
    postgres_check: HealthCheck | None = None,
    redis_check: HealthCheck | None = None,
    timeout_seconds: float = 1.0,
) -> tuple[bool,dict[str,str]]:
    postgres_check = postgres_check or check_postgres
    postgres_task=_bounded_status(postgres_check,timeout_seconds)
    if redis_check is None and redis_client is None:
        postgres=await postgres_task
        redis="disabled"
    else:
        postgres,redis=await asyncio.gather(
            postgres_task,
            _bounded_status(redis_check or check_redis,timeout_seconds))
    dependencies={"postgres":postgres,"redis":redis,
                  "openai":"configured" if settings.OPENAI_API_KEY else "disabled"}
    return postgres == "ok",dependencies
