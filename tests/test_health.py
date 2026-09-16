from fastapi.testclient import TestClient
from main import duolingo

def test_health():
    client = TestClient(duolingo)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}