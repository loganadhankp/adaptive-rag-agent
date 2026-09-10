import logging
import os
from langgraph.graph import END, START, StateGraph

from backend.config import get_settings
from backend.graph.nodes import (
    analyze_knowledge_gap_node,
    check_hallucination_node,
    classify_intent_node,
    evaluate_answer_node,
    generate_node,
    grade_documents_node,
    retrieve_node,
    rewrite_query_node,
    web_search_node,
)
from langgraph_workflow.state import RAGState

logger = logging.getLogger(__name__)


def decide_to_generate(state: RAGState) -> str:
    """Determines whether to proceed to knowledge gap analysis, rewrite query, or fallback to web search."""
    if state.get("error"):
        logger.warning(
            f"[WorkflowRouter] State error ({state.get('error')}) -> knowledge_gap_analysis"
        )
        return "knowledge_gap_analysis"

    documents = state.get("documents", [])
    has_relevant_docs = len(documents) > 0
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)

    logger.info(
        f"[WorkflowRouter] Grading: {len(documents)} docs | Retry: {retry_count}/{max_retries}"
    )

    if has_relevant_docs:
        logger.info(
            f"[WorkflowRouter] Decision: 'knowledge_gap_analysis' ({len(documents)} chunks)"
        )
        return "knowledge_gap_analysis"
    elif retry_count < max_retries:
        logger.info(
            f"[WorkflowRouter] Decision: 'rewrite_query' (Attempting query rewrite {retry_count + 1}/{max_retries})"
        )
        return "rewrite_query"
    else:
        settings = get_settings()
        tavily_key = getattr(settings, "TAVILY_API_KEY", "") or os.environ.get("TAVILY_API_KEY", "")
        if tavily_key:
            logger.info(
                "[WorkflowRouter] Decision: 'web_search' (fallback to Tavily)"
            )
            return "web_search"
        else:
            logger.info(
                "[WorkflowRouter] Decision: 'knowledge_gap_analysis' (no docs)"
            )
            return "knowledge_gap_analysis"


def route_after_knowledge_gap(state: RAGState) -> str:
    """Routes to generation if fully answerable, or terminates with gap explanation if evidence is missing."""
    if state.get("is_fully_answerable"):
        logger.info("[WorkflowRouter] Decision: 'generate' (Evidence is fully sufficient to answer)")
        return "generate"
    else:
        logger.info("[WorkflowRouter] Decision: END (Knowledge gap identified)")
        return END


def route_after_hallucination(state: RAGState) -> str:
    """Determines whether to proceed to evaluation or regenerate if hallucination detected."""
    if state.get("error"):
        logger.warning(f"[WorkflowRouter] Error encountered ({state.get('error')}) -> routing to 'evaluate_answer'")
        return "evaluate_answer"
    hallucination = state.get("hallucination_result")
    retry_count = state.get("generation_retry_count", 0)
    max_retries = state.get("max_retries", 2)

    logger.info(
        f"[WorkflowRouter] Hallucination: '{hallucination}' | Retries: {retry_count}/{max_retries}"
    )

    if hallucination == "supported":
        logger.info("[WorkflowRouter] Decision: 'evaluate_answer' (Answer supported by context)")
        return "evaluate_answer"
    elif retry_count < max_retries:
        logger.info(
            f"[WorkflowRouter] Decision: 'regenerate' (attempt {retry_count + 1}/{max_retries})"
        )
        return "regenerate"
    else:
        logger.info(
            "[WorkflowRouter] Decision: 'evaluate_answer' (max retries reached)"
        )
        return "evaluate_answer"


def route_after_evaluation(state: RAGState) -> str:
    """Determines whether to end workflow or regenerate if quality score is low."""
    if state.get("error"):
        return END
    if not state.get("documents") and not state.get("used_web_search"):
        return END
    score = state.get("answer_score", 0)
    retry_count = state.get("generation_retry_count", 0)
    max_retries = state.get("max_retries", 2)

    logger.info(f"[WorkflowRouter] Evaluation Score: {score} | Retries: {retry_count}/{max_retries}")

    if score >= 80 or retry_count >= max_retries:
        logger.info(f"[WorkflowRouter] Decision: END (Score {score} >= threshold)")
        return END
    else:
        logger.info(f"[WorkflowRouter] Decision: 'regenerate' (Score {score} < 80)")
        return "regenerate"


def create_rag_graph(provider="gemini", model=None, temperature=0.7):
    """Compiles and returns the Adaptive Self-Reflecting RAG workflow graph with Knowledge Gap Analysis."""
    workflow = StateGraph(RAGState)

    # Add all workflow nodes
    workflow.add_node("classify_intent", classify_intent_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("grade_documents", grade_documents_node)
    workflow.add_node("knowledge_gap_analysis", analyze_knowledge_gap_node)
    workflow.add_node("rewrite_query", rewrite_query_node)
    workflow.add_node("web_search", web_search_node)
    workflow.add_node("generate", generate_node)
    workflow.add_node("regenerate", generate_node)
    workflow.add_node("check_hallucination", check_hallucination_node)
    workflow.add_node("evaluate_answer", evaluate_answer_node)

    # Edges: START -> classify_intent -> retrieve -> grade_documents
    workflow.add_edge(START, "classify_intent")
    workflow.add_edge("classify_intent", "retrieve")
    workflow.add_edge("retrieve", "grade_documents")

    # Conditional routing after relevance grading
    workflow.add_conditional_edges(
        "grade_documents",
        decide_to_generate,
        {
            "knowledge_gap_analysis": "knowledge_gap_analysis",
            "rewrite_query": "rewrite_query",
            "web_search": "web_search",
        },
    )

    # Edge after query rewriting loops back to retrieval
    workflow.add_edge("rewrite_query", "retrieve")

    # Edge after web search goes directly to knowledge gap check
    workflow.add_edge("web_search", "knowledge_gap_analysis")

    # Conditional routing after knowledge gap analysis
    workflow.add_conditional_edges(
        "knowledge_gap_analysis",
        route_after_knowledge_gap,
        {
            "generate": "generate",
            END: END,
        },
    )

    # Edges after generation proceed to hallucination verification
    workflow.add_edge("generate", "check_hallucination")
    workflow.add_edge("regenerate", "check_hallucination")

    # Conditional routing after hallucination check
    workflow.add_conditional_edges(
        "check_hallucination",
        route_after_hallucination,
        {"evaluate_answer": "evaluate_answer", "regenerate": "regenerate"},
    )

    # Conditional routing after evaluation
    workflow.add_conditional_edges(
        "evaluate_answer",
        route_after_evaluation,
        {END: END, "regenerate": "regenerate"},
    )

    return workflow.compile()


async def run_rag_pipeline(
    question: str,
    conversation_history=None,
    provider="gemini",
    model=None,
    temperature=0.7,
    conversation_id=None,
):
    """Execute the complete Adaptive RAG pipeline graph."""
    graph = create_rag_graph(provider=provider, model=model, temperature=temperature)
    initial_state = {
        "question": question,
        "original_question": question,
        "question_intent": "",
        "conversation_history": conversation_history or [],
        "documents": [],
        "relevance_scores": [],
        "web_results": [],
        "generation": "",
        "sources": [],
        "hallucination_result": "",
        "answer_score": 0.0,
        "answer_evaluation": {},
        "retry_count": 0,
        "max_retries": get_settings().MAX_RETRIES,
        "generation_retry_count": 0,
        "workflow_steps": [],
        "current_step": "",
        "used_web_search": False,
        "error": "",
        "provider": provider or "gemini",
        "model": model,
        "temperature": temperature,
        "conversation_id": conversation_id,
        "is_fully_answerable": False,
        "knowledge_gap": None,
    }

    result = graph.invoke(initial_state, config={"recursion_limit": 25})
    return result
