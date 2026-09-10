import logging

from agents.llm_factory import get_llm
from langgraph_workflow.state import RAGState
from prompts.grading import GRADING_PROMPT, RelevanceGrade

logger = logging.getLogger(__name__)


def grade_documents(state: RAGState) -> dict:
    documents = state.get("documents", [])
    question = state.get("question", "")
    if not documents:
        logger.info(f"[Grader] No documents to grade for question: '{question}'")
        return {
            "documents": [],
            "relevance_scores": [],
            "workflow_steps": [
                {
                    "step": "grade_documents",
                    "status": "completed",
                    "detail": "No documents to grade",
                }
            ],
            "current_step": "grade_documents",
        }

    logger.info(f"[Grader] ==================== START DOCUMENT GRADING ====================")
    logger.info(f"[Grader] User Question: '{question}'")
    logger.info(f"[Grader] Evaluating {len(documents)} retrieved document chunk(s)...")

    try:
        llm = get_llm(
            provider=state.get("provider"),
            model=state.get("model"),
            temperature=state.get("temperature", 0.7),
        ).with_structured_output(RelevanceGrade)

        relevance_scores = []
        filtered_docs = []

        for idx, doc in enumerate(documents):
            snippet = doc.get("content", "")[:100].replace("\n", " ")
            meta_src = doc.get("metadata", {}).get("source", "unknown")
            logger.info(f"[Grader] Doc #{idx+1} [Source: {meta_src}]: Snippet='{snippet}...'")

            prompt = GRADING_PROMPT.format(question=question, document=doc["content"])
            grade = llm.invoke(prompt)

            raw_score = getattr(grade, "score", "irrelevant")
            score_normalized = str(raw_score).strip().lower()
            reasoning = getattr(grade, "reasoning", "")

            logger.info(
                f"[Grader] Doc #{idx+1} Grade: score='{score_normalized}' | reasoning='{reasoning}'"
            )

            score_data = {"relevance": score_normalized, "explanation": reasoning}
            relevance_scores.append(score_data)

            if score_normalized in ["relevant", "partially_relevant", "yes"]:
                filtered_docs.append(doc)

        logger.info(
            f"[Grader] Grading Summary: {len(filtered_docs)} of {len(documents)} chunk(s) deemed relevant"
        )
        logger.info(f"[Grader] ==================== END DOCUMENT GRADING ====================")

        detail_text = (
            f"Found {len(filtered_docs)} relevant document(s)"
            if filtered_docs
            else "No relevant local documents found for query"
        )

        return {
            "documents": filtered_docs,
            "relevance_scores": relevance_scores,
            "workflow_steps": [
                {
                    "step": "grade_documents",
                    "status": "completed",
                    "detail": detail_text,
                }
            ],
            "current_step": "grade_documents",
        }
    except Exception as e:
        logger.error(f"[Grader] Error during document grading: {e}", exc_info=True)
        return {
            "documents": [],
            "relevance_scores": [],
            "workflow_steps": [
                {"step": "grade_documents", "status": "error", "detail": str(e)}
            ],
            "current_step": "grade_documents",
        }
