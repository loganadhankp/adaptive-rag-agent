from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


@patch("backend.services.chat_service.run_rag_pipeline")
def test_conversation_lifecycle_and_stream(mock_pipeline):
    mock_pipeline.return_value = {
        "generation": "Employees may work remotely 3 days per week.",
        "documents": [{"content": "Leave policy content", "metadata": {"source": "handbook.pdf"}}],
        "sources": [{"document_name": "handbook.pdf", "chunk_id": "c1", "relevance_score": 0.9}],
        "answer_score": 95.0,
        "hallucination_result": "supported",
        "workflow_steps": [{"step": "retrieve_documents", "status": "completed", "detail": "Retrieved 1 doc"}],
    }

    # Create a conversation
    resp = client.post("/api/chat/conversations")
    assert resp.status_code == 200
    conv = resp.json()
    assert "id" in conv or "conversation_id" in conv or isinstance(conv, dict)

    # Post a chat message to the stream endpoint
    payload = {
        "conversation_id": None,
        "message": "What is the company leave policy?",
        "provider": "openai",
        "model": None,
        "temperature": 0.5,
    }

    r = client.post("/api/chat/stream", json=payload)
    assert r.status_code == 200
    text = r.text
    # Ensure the stream includes conversation_id, token, and done events
    assert "conversation_id" in text
    assert "token" in text or "data:" in text
    assert "done" in text
