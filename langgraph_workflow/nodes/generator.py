import logging

from agents.llm_factory import get_llm
from langgraph_workflow.state import RAGState
from prompts.generation import ANALYTICAL_PROMPT, FACTUAL_PROMPT
from prompts.grading import ANALYTICAL_INTENTS

logger = logging.getLogger(__name__)


def generate_answer(state: RAGState) -> dict:
    context_docs = state.get("documents", [])
    used_web_search = state.get("used_web_search", False)
    logger.info(
        f"[Generator] Generating answer with {len(context_docs)} context chunks (used_web_search={used_web_search}) for: '{state.get('question')}'"
    )

    if not context_docs and not used_web_search:
        logger.info("[Generator] No documents uploaded and no web search performed; returning notice")
        return {
            "generation": "No documents have been uploaded.",
            "sources": [],
            "generation_retry_count": state.get("generation_retry_count", 0),
            "workflow_steps": [
                {
                    "step": "generate_answer",
                    "status": "completed",
                    "detail": "No documents available to generate answer",
                }
            ],
            "current_step": "generate_answer",
        }

    try:
        llm = get_llm(
            provider=state.get("provider"),
            model=state.get("model"),
            temperature=state.get("temperature", 0.7),
        )

        context_str = "\n\n".join([d["content"] for d in context_docs])

        history_str = "\n".join(
            [
                f"{msg['role']}: {msg['content']}"
                for msg in state.get("conversation_history", [])
            ]
        )

        # Select prompt based on question intent
        intent = state.get("question_intent", "fact_extraction")
        is_analytical = intent in ANALYTICAL_INTENTS
        prompt_template = ANALYTICAL_PROMPT if is_analytical else FACTUAL_PROMPT
        logger.info(f"[Generator] Using {'ANALYTICAL' if is_analytical else 'FACTUAL'} prompt (intent='{intent}')")

        prompt = prompt_template.format(
            question=state["question"],
            context=context_str,
            conversation_history=history_str,
        )

        response = llm.invoke(prompt)
        if hasattr(response, "content"):
            if isinstance(response.content, list):
                generation = "".join([c.get("text", "") if isinstance(c, dict) else str(c) for c in response.content])
            else:
                generation = str(response.content)
        else:
            generation = str(response)

        logger.info(f"[Generator] Generated answer length: {len(generation)} characters. Preview: {generation[:100]}...")

        sources = []
        for d in context_docs:
            meta = d.get("metadata", {})
            src_type = meta.get("source_type", "knowledge_base")
            sources.append(
                {
                    "document_name": meta.get("source") or meta.get("title", "Unknown Document"),
                    "page_number": meta.get("page", 0),
                    "chunk_id": meta.get("chunk_id", ""),
                    "relevance_score": meta.get("relevance_score"),
                    "content_preview": d.get("content", "")[:120] + "...",
                    "source_type": src_type,
                    "url": meta.get("url", ""),
                    "title": meta.get("title", ""),
                }
            )

        generation_retry_count = state.get("generation_retry_count", 0)
        # Increment if this is a retry from hallucination check, evaluation, or explicit regenerate
        if state.get("current_step") in [
            "evaluate_answer",
            "check_hallucination",
            "regenerate",
        ]:
            generation_retry_count += 1

        return {
            "generation": generation,
            "sources": sources,
            "generation_retry_count": generation_retry_count,
            "workflow_steps": [
                {
                    "step": "generate_answer",
                    "status": "completed",
                    "detail": "Generated answer",
                }
            ],
            "current_step": "generate_answer",
        }
    except Exception as e:
        logger.error(f"[Generator] Error generating answer: {e}", exc_info=True)
        generation_retry_count = state.get("generation_retry_count", 0) + 1
        return {
            "generation": f"Error: Unable to generate answer ({e})",
            "sources": [],
            "error": str(e),
            "generation_retry_count": generation_retry_count,
            "workflow_steps": [
                {"step": "generate_answer", "status": "error", "detail": str(e)}
            ],
            "current_step": "generate_answer",
        }
