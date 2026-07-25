import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.cache import cache_service

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_cache():
    cache_service.clear()

def test_invalid_url():
    response = client.post("/api/v1/audit", json={"url": "not-a-valid-url"})
    assert response.status_code == 422  # FastAPI validation error

def test_valid_audit_and_caching():
    target_payload = {"url": "https://example.com"}
    
    # First request - Live fetch
    res1 = client.post("/api/v1/audit", json=target_payload)
    assert res1.status_code == 200
    assert res1.json()["source"] == "live"
    assert "X-Request-ID" in res1.headers

    # Second request - Cached fetch
    res2 = client.post("/api/v1/audit", json=target_payload)
    assert res2.status_code == 200
    assert res2.json()["source"] == "cache"