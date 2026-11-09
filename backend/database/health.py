import asyncio
from collections.abc import Awaitable,Callable

from sqlalchemy import text

from backend.database.db import engine
from backend.database.redis import redis_client


HealthCheck = Callable[[],Awaitable[object]]


async def check_postgres():
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
    return True


async def check_redis():
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
    redis_check = redis_check or check_redis
    postgres,redis = await asyncio.gather(
        _bounded_status(postgres_check,timeout_seconds),
        _bounded_status(redis_check,timeout_seconds),
    )
    dependencies = {"postgres":postgres,"redis":redis}
    return all(value == "ok" for value in dependencies.values()),dependencies
