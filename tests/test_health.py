from fastapi.testclient import TestClient
import main
from main import duolingo

def test_health():
    client = TestClient(duolingo)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_reports_dependency_failure(monkeypatch):
    async def unavailable():
        return False,{"postgres":"ok","redis":"unavailable"}

    monkeypatch.setattr(main,"collect_readiness",unavailable,raising=False)
    response = TestClient(duolingo).get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status":"not ready",
        "dependencies":{"postgres":"ok","redis":"unavailable"},
    }
