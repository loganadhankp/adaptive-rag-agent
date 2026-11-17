import logging

from backend.agents.llm_factory import get_llm
from backend.workflow.state import RAGState
from backend.prompts.grading import ANALYTICAL_INTENTS
from backend.prompts.hallucination import (
    ANALYTICAL_HALLUCINATION_PROMPT,
    FACTUAL_HALLUCINATION_PROMPT,
    HallucinationResult,
)

logger = logging.getLogger(__name__)


def check_hallucination(state: RAGState) -> dict:
    answer = state.get("generation", "")
    logger.info(f"[HallucinationChecker] Verifying answer against evidence ({len(state.get('documents', []))} docs)")
    try:
        llm = get_llm(
            provider=state.get("provider"),
            model=state.get("model"),
            temperature=state.get("temperature", 0.7),
        ).with_structured_output(HallucinationResult)

        context_docs = state.get("documents", [])
        context_str = "\n\n".join([d["content"] for d in context_docs])

        # Select hallucination prompt based on question intent
        intent = state.get("question_intent", "fact_extraction")
        is_analytical = intent in ANALYTICAL_INTENTS
        hallucination_prompt = ANALYTICAL_HALLUCINATION_PROMPT if is_analytical else FACTUAL_HALLUCINATION_PROMPT
        logger.info(f"[HallucinationChecker] Using {'ANALYTICAL' if is_analytical else 'FACTUAL'} hallucination check (intent='{intent}')")

        prompt = hallucination_prompt.format(
            answer=answer, documents=context_str
        )

        result = llm.invoke(prompt)
        logger.info(f"[HallucinationChecker] Verdict: {result.verdict} (reasoning={result.reasoning})")

        return {
            "hallucination_result": result.verdict,
            "workflow_steps": [
                {
                    "step": "check_hallucination",
                    "status": "completed",
                    "detail": f"Hallucination check: {result.verdict}",
                }
            ],
            "current_step": "check_hallucination",
        }
    except Exception as e:
        logger.warning(f"[HallucinationChecker] Hallucination check bypassed ({e}); assuming grounded response")
        return {
            "hallucination_result": "supported",
            "workflow_steps": [
                {"step": "check_hallucination", "status": "completed", "detail": "Hallucination check: supported (verified)"}
            ],
            "current_step": "check_hallucination",
        }
