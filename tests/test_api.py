from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Greek Real Estate" in response.json()["service"]

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_api_areas():
    response = client.get("/api/areas")
    assert response.status_code == 200
    assert response.json()["success"] is True

def test_api_price_indices():
    response = client.get("/api/price-indices?areaIds=athens")
    assert response.status_code == 200
    assert response.json()["success"] is True

def test_api_metrics_summary():
    response = client.get("/api/metrics/summary?areaIds=athens")
    assert response.status_code == 200
    assert response.json()["success"] is True
