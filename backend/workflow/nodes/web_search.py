import logging
import os
from langchain_community.tools.tavily_search import TavilySearchResults

from backend.config import get_settings
from backend.workflow.state import RAGState

logger = logging.getLogger(__name__)


def web_search(state: RAGState) -> dict:
    """Execute a web search via Tavily using the original user question."""
    query = state.get("original_question") or state.get("question", "")
    logger.info(f"[WebSearch] Fallback triggered using original user question: '{query}'")
    try:
        settings = get_settings()
        api_key = os.environ.get("TAVILY_API_KEY") or getattr(
            settings, "TAVILY_API_KEY", None
        )

        if not api_key:
            logger.info("[WebSearch] TAVILY_API_KEY not configured; skipping web search fallback")
            return {
                "question": query,
                "web_results": [],
                "workflow_steps": [
                    {
                        "step": "web_search",
                        "status": "skipped",
                        "detail": "TAVILY_API_KEY not configured for web search fallback",
                    }
                ],
                "current_step": "web_search",
            }

        os.environ["TAVILY_API_KEY"] = api_key
        try:
            tool = TavilySearchResults(max_results=3, tavily_api_key=api_key)
        except TypeError:
            tool = TavilySearchResults(max_results=3)
        results = tool.invoke({"query": query})
        logger.info(f"[WebSearch] Tavily returned {len(results) if isinstance(results, list) else 0} results")

        web_results = []
        if isinstance(results, list):
            for r in results:
                if isinstance(r, dict):
                    web_results.append(
                        {
                            "title": r.get("title", "Web Result"),
                            "url": r.get("url", ""),
                            "content": r.get("content", ""),
                            "source_type": "web_search",
                        }
                    )

        # Discard irrelevant local documents, keep only verified relevant local docs + web results
        docs = [
            d for d in state.get("documents", [])
            if d.get("metadata", {}).get("source_type") == "knowledge_base" and d.get("metadata", {}).get("is_relevant") is True
        ]
        for wr in web_results:
            docs.append(
                {
                    "content": wr["content"],
                    "metadata": {
                        "source": wr["url"],
                        "title": wr["title"],
                        "source_type": "web_search",
                        "url": wr["url"],
                    },
                }
            )

        return {
            "question": query,
            "web_results": web_results,
            "used_web_search": True,
            "documents": docs,
            "workflow_steps": [
                {
                    "step": "web_search",
                    "status": "completed",
                    "detail": f"Retrieved {len(web_results)} web search results",
                }
            ],
            "current_step": "web_search",
        }
    except Exception as e:
        logger.error(f"[WebSearch] Error executing web search: {e}", exc_info=True)
        return {
            "web_results": [],
            "error": str(e),
            "workflow_steps": [
                {"step": "web_search", "status": "error", "detail": str(e)}
            ],
            "current_step": "web_search",
        }
