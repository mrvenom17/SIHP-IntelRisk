# tests/test_orchestrator.py
import pytest
from fastapi.testclient import TestClient
from src.orchestrator.main import app

client = TestClient(app)

def test_ingest():
    response = client.post("/api/ingest", json=["Flood in Jakarta"])
    assert response.status_code == 200
    assert "Ingested" in response.json()["message"]

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "orchestrator_ingested_total" in response.text