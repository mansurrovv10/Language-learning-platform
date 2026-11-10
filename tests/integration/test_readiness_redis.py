import asyncio
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.middleware import RATE_WINDOW, RateLimitMiddleware

pytestmark = pytest.mark.integration


@pytest.mark.asyncio(loop_scope="function")
async def test_readiness_timeout_is_bounded():
    from backend.database.health import collect_readiness

    async def slow():
        await asyncio.sleep(1)

    async def healthy():
        return True

    started = time.perf_counter()
    ready,dependencies = await collect_readiness(
        postgres_check=slow,
        redis_check=healthy,
        timeout_seconds=0.01,
    )

    assert time.perf_counter() - started < 0.2
    assert ready is False
    assert dependencies == {
        "postgres":"unavailable","redis":"ok","openai":"disabled"}


@pytest.mark.asyncio(loop_scope="function")
async def test_redis_outage_is_reported_but_does_not_fail_readiness():
    """Catches optional Redis incorrectly taking the core API out of service."""
    from backend.database.health import collect_readiness

    async def healthy():
        return True

    async def broken():
        raise ConnectionError("redis unavailable")

    ready,dependencies=await collect_readiness(
        postgres_check=healthy,redis_check=broken,timeout_seconds=0.1)

    assert ready is True
    assert dependencies == {
        "postgres":"ok","redis":"unavailable","openai":"disabled"}


def rate_limited_app():
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)

    @app.get("/core")
    async def core():
        return {"status":"ok"}

    return app


def test_redis_failure_is_fail_open(monkeypatch):
    class BrokenRedis:
        async def incr(self,key):
            raise ConnectionError("redis unavailable")

    monkeypatch.setattr("backend.middleware.redis_client",BrokenRedis())

    response = TestClient(rate_limited_app()).get("/core")

    assert response.status_code == 200
    assert response.json() == {"status":"ok"}


def test_rate_limit_key_gets_expiry(monkeypatch):
    class RecordingRedis:
        def __init__(self):
            self.expirations = []

        async def incr(self,key):
            return 1

        async def expire(self,key,seconds):
            self.expirations.append((key,seconds))

    redis = RecordingRedis()
    monkeypatch.setattr("backend.middleware.redis_client",redis)

    response = TestClient(rate_limited_app()).get("/core")

    assert response.status_code == 200
    assert len(redis.expirations) == 1
    assert redis.expirations[0][1] == RATE_WINDOW + 5

