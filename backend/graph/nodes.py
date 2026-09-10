import logging
import os
from langchain_community.tools.tavily_search import TavilySearchResults

from agents.llm_factory import get_llm
from backend.config import get_settings
from langgraph_workflow.nodes.evaluator import evaluate_answer as evaluate_answer_node
from langgraph_workflow.nodes.generator import generate_answer as generate_node
from langgraph_workflow.nodes.grader import grade_documents as grade_documents_node
from langgraph_workflow.nodes.hallucination_checker import (
    check_hallucination as check_hallucination_node,
)
from langgraph_workflow.nodes.intent_classifier import classify_intent as classify_intent_node
from langgraph_workflow.nodes.knowledge_gap import (
    analyze_knowledge_gap as analyze_knowledge_gap_node,
)
from langgraph_workflow.nodes.retriever import retrieve_documents as retrieve_node
from langgraph_workflow.nodes.rewriter import rewrite_query as rewrite_query_node
from langgraph_workflow.state import RAGState

logger = logging.getLogger(__name__)


def web_search_node(state: RAGState) -> dict:
    """Execute a web search via Tavily and merge formatted results into state documents."""
    query = state.get("question", "")
    logger.info(f"[WebSearchNode] Executing Tavily web search fallback for query: '{query}'")
    try:
        settings = get_settings()
        api_key = os.environ.get("TAVILY_API_KEY") or getattr(settings, "TAVILY_API_KEY", "")

        if not api_key:
            logger.info("[WebSearchNode] TAVILY_API_KEY not configured; skipping web search fallback")
            return {
                "web_results": [],
                "used_web_search": False,
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
        logger.info(f"[WebSearchNode] Tavily returned {len(results) if isinstance(results, list) else 0} results")

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

        docs = list(state.get("documents", []))
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
            "web_results": web_results,
            "used_web_search": True,
            "documents": docs,
            "workflow_steps": [
                {
                    "step": "web_search",
                    "status": "completed",
                    "detail": f"Retrieved {len(web_results)} web search results from Tavily",
                }
            ],
            "current_step": "web_search",
        }
    except Exception as e:
        logger.error(f"[WebSearchNode] Error executing web search: {e}", exc_info=True)
        return {
            "web_results": [],
            "error": str(e),
            "workflow_steps": [{"step": "web_search", "status": "error", "detail": str(e)}],
            "current_step": "web_search",
        }
