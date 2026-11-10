import asyncio

import pytest
from fastapi.testclient import TestClient

pytestmark=pytest.mark.integration


def test_app_lifespan_starts_and_cancels_chat_subscriber(monkeypatch):
    """Catches subscriber leaks or an app that never starts remote fan-out."""
    import main

    state=[]

    async def run_forever():
        state.append("started")
        try:
            await asyncio.Event().wait()
        finally:
            state.append("stopped")

    monkeypatch.setattr(main.chat_event_broker,"run_forever",run_forever)
    with TestClient(main.duolingo) as client:
        assert client.get("/health").status_code == 200
        assert state == ["started"]
    assert state == ["started","stopped"]
