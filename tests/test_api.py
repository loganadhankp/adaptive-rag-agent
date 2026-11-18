import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

try:
    from backend.main import app

    client = TestClient(app)
except ImportError:
    client = None

class TestAPI(unittest.TestCase):
    def setUp(self):
        if client is None:
            self.skipTest("FastAPI app could not be imported")

    def test_health_endpoint(self):
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)

    @patch("backend.main.app.state.chat_service.get_conversations")
    def test_get_conversations(self, mock_get):
        mock_get.return_value = [{"id": "1", "title": "Test Chat"}]
        response = client.get("/api/chat/conversations")
        self.assertEqual(response.status_code, 200)

    @patch("backend.main.app.state.analytics_service.get_summary")
    def test_get_analytics_summary(self, mock_summary):
        mock_summary.return_value = {
            "total_conversations": 10,
            "total_messages": 0,
            "total_queries": 0,
            "retrieval_success_rate": 0.0,
            "query_rewrites_count": 0,
            "web_search_count": 0,
            "hallucination_failures_count": 0,
            "avg_answer_quality": 0.0,
        }
        response = client.get("/api/analytics/summary")
        self.assertEqual(response.status_code, 200)

    @patch("backend.main.app.state.kb_service.list_documents")
    def test_get_kb_documents(self, mock_docs):
        mock_docs.return_value = [
            {
                "id": "doc1",
                "filename": "test.pdf",
                "file_type": "pdf",
                "chunk_count": 1,
                "uploaded_at": "2024-01-01T00:00:00",
                "conversation_id": None,
            }
        ]
        response = client.get("/api/kb/documents")
        self.assertEqual(response.status_code, 200)

    @patch("backend.main.app.state.analytics_service.get_summary")
    def test_metrics_endpoint(self, mock_summary):
        mock_summary.return_value = {
            "total_conversations": 10,
            "total_messages": 20,
            "total_queries": 10,
            "retrieval_success_rate": 90.0,
            "query_rewrites_count": 2,
            "web_search_count": 1,
            "hallucination_failures_count": 0,
            "avg_answer_quality": 88.5,
        }
        response = client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_conversations"], 10)
        self.assertEqual(data["retrieval_success_rate"], 90.0)

if __name__ == "__main__":
    unittest.main()
