import json
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

def test_payload_length_validation():
    """Prompts exceeding max_length (50000 chars) must be rejected with HTTP 422."""
    huge_message = "A" * 50001
    resp = client.post(
        "/api/chat/stream",
        json={"message": huge_message},
    )
    assert resp.status_code == 422

def test_temperature_range_validation():
    """Negative temperature or temperature > 2.0 must be rejected with HTTP 422."""
    resp1 = client.post(
        "/api/chat/stream",
        json={"message": "hello", "temperature": -0.5},
    )
    assert resp1.status_code == 422

    resp2 = client.post(
        "/api/chat/stream",
        json={"message": "hello", "temperature": 2.5},
    )
    assert resp2.status_code == 422

@patch("backend.services.chat_service.run_rag_pipeline")
def test_sse_event_structure_and_no_duplicate_done(mock_pipeline):
    """SSE stream must emit sequential events without duplicate completion tokens or done events."""
    mock_pipeline.return_value = {
        "generation": "FastAPI is a modern web framework.",
        "documents": [],
        "sources": [],
        "answer_score": 90.0,
        "query_route": "GENERAL_CHAT",
        "answerability_status": "GENERAL_CHAT",
        "workflow_steps": [{"step": "classify_intent", "status": "completed"}],
    }

    resp = client.post(
        "/api/chat/stream",
        json={"message": "What is FastAPI?"},
    )
    assert resp.status_code == 200

    lines = resp.text.split("\r\n\r\n") if "\r\n\r\n" in resp.text else resp.text.split("\n\n")

    events = []
    tokens = []
    done_count = 0

    for block in lines:
        if not block.strip():
            continue
        ev_name = None
        ev_data = None
        for line in block.split("\n"):
            line = line.strip()
            if line.startswith("event: "):
                ev_name = line[7:]
            elif line.startswith("data: "):
                ev_data = line[6:]
        if ev_name:
            events.append(ev_name)
            if ev_name == "token" and ev_data:
                try:
                    d = json.loads(ev_data)
                    tokens.append(d.get("token", ""))
                except Exception:
                    pass
            elif ev_name == "done":
                done_count += 1

    assert "conversation_id" in events
    assert "token" in events
    assert "metadata" in events
    assert "done" in events
    assert done_count == 1

    reconstructed = "".join(tokens)
    assert reconstructed == "FastAPI is a modern web framework."

def test_concurrent_health_and_metrics_calls():
    """Concurrent calls to health and metrics should return 200 OK consistently."""
    import concurrent.futures

    def call_health():
        return client.get("/health").status_code

    def call_metrics():
        return client.get("/metrics").status_code

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        health_futures = [executor.submit(call_health) for _ in range(20)]
        metrics_futures = [executor.submit(call_metrics) for _ in range(10)]

        for f in concurrent.futures.as_completed(health_futures + metrics_futures):
            assert f.result() == 200
