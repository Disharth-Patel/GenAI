import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.ollama_service import ollama_service
from backend.services.ai_service import ai_service


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_ollama_service_health_probe():
    """Verify that Ollama health probing returns structured status without raising exceptions."""
    health = ollama_service.check_health()
    assert isinstance(health, dict)
    assert "available" in health
    assert "status" in health
    assert "active_model" in health
    assert health["active_model"] == ollama_service.model_name
    assert "instruction" in health


def test_llm_status_api_endpoint(client):
    """Verify that GET /api/llm/status returns health, active model, and hardware info."""
    res = client.get("/api/llm/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "provider" in data
    assert "health" in data
    assert "hardware" in data
    assert "ram_total_mb" in data["hardware"]
    assert "setup_guide" in data
    assert "pull_command" in data["setup_guide"]


def test_ollama_chat_integration_and_free_cost(client):
    """
    Verify chat response generation under Ollama provider:
    - Must return 200 OK.
    - Zero API cost ($0.00).
    - Preserves answer and verified sources.
    """
    res = client.post("/api/chat", json={
        "message": "What is the foreign scholarship scheme for OBC students in Maharashtra?",
        "language": "en"
    })
    assert res.status_code == 200
    data = res.json()
    assert len(data["answer"]) > 0
    assert len(data["sources"]) > 0
    metrics = data.get("metrics", {})
    assert metrics.get("cost_est_usd") == 0.0
    assert metrics.get("total_tokens_est", 0) > 0
    assert metrics.get("latency_ms", 0) > 0


def test_ollama_offline_graceful_recovery(client):
    """
    Verify that if Ollama is unavailable, the API reports an actionable
    service error instead of silently using a simulated or cloud fallback.
    """
    orig_url = ollama_service.base_url
    try:
        # Intentionally point to an unreachable port
        ollama_service.base_url = "http://127.0.0.1:59999"

        res = client.post("/api/chat", json={
            "message": "How many seats are available in OBC hostels?",
            "language": "en"
        })
        assert res.status_code == 503
        data = res.json()
        assert "Ollama" in data["detail"]
    finally:
        ollama_service.base_url = orig_url
