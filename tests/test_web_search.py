from unittest.mock import MagicMock, patch

from backend.workflow.nodes.web_search import web_search

def test_web_search_invokes_tavily(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "testkey")

    with patch("backend.workflow.nodes.web_search.TavilySearchResults") as MockTavily:
        mock_instance = MagicMock()
        MockTavily.return_value = mock_instance
        mock_instance.invoke.return_value = [
            {
                "title": "Result 1",
                "url": "https://example.com/1",
                "content": "Content about test query - 1",
            },
            {
                "title": "Result 2",
                "url": "https://example.com/2",
                "content": "Content about test query - 2",
            },
        ]

        state = {"question": "test query", "documents": []}
        res = web_search(state)

        assert res.get("used_web_search") is True
        assert len(res.get("web_results", [])) == 2
        assert any("Content about test query" in r["content"] for r in res["web_results"])
        assert any(d.get("metadata", {}).get("source") for d in res.get("documents", []))
