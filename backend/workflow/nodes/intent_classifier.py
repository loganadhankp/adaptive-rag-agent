import logging
import re

from backend.agents.llm_factory import get_llm
from backend.workflow.state import RAGState
from backend.prompts.grading import (
    ANALYTICAL_INTENTS,
    INTENT_PROMPT,
    QUERY_ROUTER_PROMPT,
    QueryIntentRoute,
    QuestionIntent,
)

logger = logging.getLogger(__name__)

# Common conversational greetings & pleasantries pattern
GREETING_PATTERN = re.compile(
    r"^\s*(hi|hello|hey|greetings|good\s+(morning|afternoon|evening|day)|howdy|sup|yo|how\s+are\s+you|who\s+are\s+you|what\s+can\s+you\s+do|thanks|thank\s+you|bye|goodbye)\b[!?.\s]*$",
    re.IGNORECASE,
)


def classify_intent(state: RAGState) -> dict:
    """
    Classifies user input into:
    1. Query Route: GENERAL_CHAT vs KNOWLEDGE_BASE_QUERY
    2. Sub-intent (if KNOWLEDGE_BASE_QUERY): fact_extraction, summarization, analysis, recommendation, comparison

    GENERAL_CHAT routes directly to conversational LLM without RAG retrieval or sufficiency checks.
    KNOWLEDGE_BASE_QUERY routes to retrieval and context sufficiency evaluation.
    """
    question = state.get("question", "").strip()
    logger.info(f"[IntentClassifier] Routing query: '{question}'")

    # Fast-path for common greetings/pleasantries
    if GREETING_PATTERN.match(question):
        logger.info(f"[IntentClassifier] Fast-path greeting detected -> GENERAL_CHAT")
        return {
            "query_route": "GENERAL_CHAT",
            "question_intent": "general_chat",
            "workflow_steps": [
                {
                    "step": "classify_intent",
                    "status": "completed",
                    "detail": "Route: GENERAL_CHAT (Conversational mode)",
                }
            ],
            "current_step": "classify_intent",
        }

    try:
        # Route query: GENERAL_CHAT vs KNOWLEDGE_BASE_QUERY
        router_llm = get_llm(
            provider=state.get("provider"),
            model=state.get("model"),
            temperature=0.0,
        ).with_structured_output(QueryIntentRoute)

        route_prompt = QUERY_ROUTER_PROMPT.format(question=question)
        route_result = router_llm.invoke(route_prompt)

        route = route_result.intent
        logger.info(f"[IntentClassifier] QueryRoute: '{route}' | Reasoning: '{route_result.reasoning}'")

        if route == "GENERAL_CHAT":
            return {
                "query_route": "GENERAL_CHAT",
                "question_intent": "general_chat",
                "workflow_steps": [
                    {
                        "step": "classify_intent",
                        "status": "completed",
                        "detail": "Route: GENERAL_CHAT (Direct conversational mode)",
                    }
                ],
                "current_step": "classify_intent",
            }

        # For KNOWLEDGE_BASE_QUERY: classify sub-intent
        intent = "fact_extraction"
        is_analytical = False
        try:
            intent_llm = get_llm(
                provider=state.get("provider"),
                model=state.get("model"),
                temperature=0.0,
            ).with_structured_output(QuestionIntent)

            intent_prompt = INTENT_PROMPT.format(question=question)
            intent_res = intent_llm.invoke(intent_prompt)
            intent = intent_res.intent
            is_analytical = intent in ANALYTICAL_INTENTS
        except Exception as e:
            logger.warning(f"[IntentClassifier] Sub-intent classification failed ({e}); default to fact_extraction")

        return {
            "query_route": "KNOWLEDGE_BASE_QUERY",
            "question_intent": intent,
            "workflow_steps": [
                {
                    "step": "classify_intent",
                    "status": "completed",
                    "detail": f"Route: KNOWLEDGE_BASE_QUERY ({intent})",
                }
            ],
            "current_step": "classify_intent",
        }

    except Exception as e:
        logger.warning(f"[IntentClassifier] Routing LLM failed ({e}); defaulting to KNOWLEDGE_BASE_QUERY")
        return {
            "query_route": "KNOWLEDGE_BASE_QUERY",
            "question_intent": "fact_extraction",
            "workflow_steps": [
                {
                    "step": "classify_intent",
                    "status": "completed",
                    "detail": "Route: KNOWLEDGE_BASE_QUERY (default fallback)",
                }
            ],
            "current_step": "classify_intent",
        }
