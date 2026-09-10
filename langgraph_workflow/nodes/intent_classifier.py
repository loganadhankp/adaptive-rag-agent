import logging

from agents.llm_factory import get_llm
from langgraph_workflow.state import RAGState
from prompts.grading import ANALYTICAL_INTENTS, INTENT_PROMPT, QuestionIntent

logger = logging.getLogger(__name__)


def classify_intent(state: RAGState) -> dict:
    """
    Classifies the user's question intent into one of:
    - fact_extraction
    - summarization
    - analysis
    - recommendation
    - comparison

    This determines whether downstream nodes use strict factual mode
    or analytical reasoning mode.
    """
    question = state.get("question", "")
    logger.info(f"[IntentClassifier] Classifying intent for: '{question}'")

    try:
        llm = get_llm(
            provider=state.get("provider"),
            model=state.get("model"),
            temperature=0.0,  # Low temperature for consistent classification
        ).with_structured_output(QuestionIntent)

        prompt = INTENT_PROMPT.format(question=question)
        result = llm.invoke(prompt)

        intent = result.intent
        reasoning = result.reasoning
        is_analytical = intent in ANALYTICAL_INTENTS

        logger.info(
            f"[IntentClassifier] Intent: '{intent}' | Analytical: {is_analytical} | Reasoning: '{reasoning}'"
        )

        return {
            "question_intent": intent,
            "workflow_steps": [
                {
                    "step": "classify_intent",
                    "status": "completed",
                    "detail": f"Intent: {intent} ({'analytical' if is_analytical else 'factual'} mode)",
                }
            ],
            "current_step": "classify_intent",
        }
    except Exception as e:
        logger.warning(
            f"[IntentClassifier] Classification failed ({e}); defaulting to 'fact_extraction'"
        )
        return {
            "question_intent": "fact_extraction",
            "workflow_steps": [
                {
                    "step": "classify_intent",
                    "status": "completed",
                    "detail": "Intent: fact_extraction (default fallback)",
                }
            ],
            "current_step": "classify_intent",
        }
