import logging
from langgraph.graph import END, START, StateGraph

from backend.config import get_settings
from backend.workflow.nodes import (
    analyze_knowledge_gap,
    check_hallucination,
    check_sufficiency,
    classify_intent,
    evaluate_answer,
    generate_answer,
    generate_general_chat,
    grade_documents,
    retrieve_documents,
    rewrite_query,
    web_search,
)
from backend.workflow.state import RAGState

logger = logging.getLogger(__name__)

def create_rag_graph(provider="openai", model=None, temperature=0.7):
    workflow = StateGraph(RAGState)

    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("general_chat", generate_general_chat)
    workflow.add_node("retrieve", retrieve_documents)
    workflow.add_node("check_sufficiency", check_sufficiency)
    workflow.add_node("generate", generate_answer)
    workflow.add_node("regenerate", generate_answer)
    workflow.add_node("check_hallucination", check_hallucination)
    workflow.add_node("evaluate_answer", evaluate_answer)

    workflow.add_node("grade_documents", grade_documents)
    workflow.add_node("knowledge_gap_analysis", analyze_knowledge_gap)
    workflow.add_node("rewrite_query", rewrite_query)
    workflow.add_node("web_search", web_search)

    def route_after_intent(state: RAGState) -> str:
        route = state.get("query_route", "")
        if route == "GENERAL_CHAT":
            logger.info("[WorkflowRouter] Decision: 'general_chat' (GENERAL_CHAT intent, bypassing retrieval)")
            return "general_chat"
        logger.info("[WorkflowRouter] Decision: 'retrieve' (KNOWLEDGE_BASE_QUERY intent, proceeding to retrieval)")
        return "retrieve"

    workflow.add_edge(START, "classify_intent")
    workflow.add_conditional_edges(
        "classify_intent",
        route_after_intent,
        {
            "general_chat": "general_chat",
            "retrieve": "retrieve",
        },
    )
    workflow.add_edge("general_chat", END)
    workflow.add_edge("retrieve", "check_sufficiency")

    def route_after_sufficiency(state: RAGState):
        status = str(state.get("answerability_status", "")).strip().upper()
        logger.info(f"[WorkflowRouter] Sufficiency Routing: answerability_status='{status}'")

        if status == "SUFFICIENT":
            logger.info("[WorkflowRouter] Evidence is SUFFICIENT. Proceeding to answer generation.")
            return "generate"
        else:
            logger.info(
                f"[WorkflowRouter] Evidence is {status or 'NOT SUFFICIENT'}. "
                "Halting pipeline immediately without generation."
            )
            return END

    workflow.add_conditional_edges(
        "check_sufficiency",
        route_after_sufficiency,
        {
            "generate": "generate",
            END: END,
        },
    )

    workflow.add_edge("generate", "check_hallucination")
    workflow.add_edge("regenerate", "check_hallucination")

    def route_after_hallucination(state):
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

    workflow.add_conditional_edges(
        "check_hallucination",
        route_after_hallucination,
        {"evaluate_answer": "evaluate_answer", "regenerate": "regenerate"},
    )

    def route_after_evaluation(state):
        if state.get("error"):
            return END
        if not state.get("documents") and not state.get("used_web_search"):
            return END
        score = state.get("answer_score", 0)
        retry_count = state.get("generation_retry_count", 0)
        max_retries = state.get("max_retries", 2)

        logger.info(
            f"[WorkflowRouter] Evaluation Score: {score} | Retries: {retry_count}/{max_retries}"
        )

        if score >= 80 or retry_count >= max_retries:
            logger.info(f"[WorkflowRouter] Decision: END (Score {score} >= threshold)")
            return END
        else:
            logger.info(f"[WorkflowRouter] Decision: 'regenerate' (Score {score} < 80)")
            return "regenerate"

    workflow.add_conditional_edges(
        "evaluate_answer",
        route_after_evaluation,
        {END: END, "regenerate": "regenerate"},
    )

    return workflow.compile()

async def run_rag_pipeline(
    question,
    conversation_history=None,
    provider="gemini",
    model=None,
    temperature=0.7,
    conversation_id=None,
):
    """Run the complete RAG pipeline and yield workflow steps."""
    graph = create_rag_graph(provider, model, temperature)
    initial_state = {
        "question": question,
        "original_question": question,
        "query_route": "",
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
        "answerability_status": "",
        "relevance_score": 0,
        "coverage_score": 0,
        "knowledge_gap_reason": "",
        "available_information": "",
        "missing_information": [],
        "clarification_request": "",
        "context_assessment": None,
    }

    result = graph.invoke(initial_state, config={"recursion_limit": 25})
    return result
