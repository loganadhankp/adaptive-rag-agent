import logging

from agents.llm_factory import get_llm
from langgraph_workflow.state import RAGState
from prompts.rewriting import REWRITING_PROMPT, RewrittenQuery

logger = logging.getLogger(__name__)


def rewrite_query(state: RAGState) -> dict:
    original = state.get("original_question") or state.get("question", "")
    logger.info(f"[Rewriter] Rewriting query without using unrelated content: '{original}' (attempt {state.get('retry_count', 0)+1})")
    try:
        llm = get_llm(
            provider=state.get("provider"),
            model=state.get("model"),
            temperature=state.get("temperature", 0.7),
        ).with_structured_output(RewrittenQuery)

        history_str = "\n".join(
            [
                f"{msg['role']}: {msg['content']}"
                for msg in state.get("conversation_history", [])
            ]
        )
        prompt = REWRITING_PROMPT.format(
            question=original, conversation_history=history_str
        )

        result = llm.invoke(prompt)
        new_question = result.rewritten_query
        logger.info(f"[Rewriter] Query reformulated to: '{new_question}'")

        retry_count = state.get("retry_count", 0) + 1

        return {
            "question": new_question,
            "retry_count": retry_count,
            "workflow_steps": [
                {
                    "step": "rewrite_query",
                    "status": "completed",
                    "detail": f"Rewrote query from '{original}' to '{new_question}'",
                }
            ],
            "current_step": "rewrite_query",
        }
    except Exception as e:
        logger.error(f"[Rewriter] Error rewriting query: {e}", exc_info=True)
        retry_count = state.get("retry_count", 0) + 1
        return {
            "error": str(e),
            "retry_count": retry_count,
            "workflow_steps": [
                {"step": "rewrite_query", "status": "error", "detail": str(e)}
            ],
            "current_step": "rewrite_query",
        }
