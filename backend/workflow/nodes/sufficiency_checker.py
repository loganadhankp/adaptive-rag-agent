import logging

from backend.agents.llm_factory import get_llm
from backend.workflow.state import RAGState
from backend.prompts.sufficiency import (
    CONTEXT_SUFFICIENCY_PROMPT,
    ContextSufficiencyAssessment,
    format_context_assessment_output,
)

logger = logging.getLogger(__name__)

def check_sufficiency(state: RAGState) -> dict:
    """Evaluates whether retrieved documents contain sufficient evidence before answer generation."""
    question = state.get("question", "")
    documents = state.get("documents", [])
    history = state.get("conversation_history", [])

    logger.info(
        f"[SufficiencyChecker] Assessing context sufficiency for query: '{question}' "
        f"across {len(documents)} retrieved chunk(s)..."
    )

    if not documents:
        logger.info("[SufficiencyChecker] No documents retrieved. Classifying as IRRELEVANT.")
        assessment = ContextSufficiencyAssessment(
            status="IRRELEVANT",
            relevance_score=0,
            coverage_score=0,
            knowledge_gap_reason="OUTSIDE_KNOWLEDGE_BASE",
            available_information="None",
            missing_information=["All factual evidence required to answer this inquiry"],
            clarification_request=(
                "No relevant information was found in the Knowledge Base regarding your inquiry. "
                "Please upload relevant documents covering this topic or provide the required information."
            ),
        )
        formatted_output = format_context_assessment_output(assessment)

        return {
            "answerability_status": assessment.status,
            "relevance_score": assessment.relevance_score,
            "coverage_score": assessment.coverage_score,
            "knowledge_gap_reason": assessment.knowledge_gap_reason,
            "available_information": assessment.available_information,
            "missing_information": assessment.missing_information,
            "clarification_request": assessment.clarification_request,
            "context_assessment": assessment.model_dump(),
            "is_fully_answerable": False,
            "generation": formatted_output,
            "sources": [],
            "workflow_steps": [
                {
                    "step": "check_sufficiency",
                    "status": "completed",
                    "detail": "Context Assessment: IRRELEVANT (0% coverage, reason: OUTSIDE_KNOWLEDGE_BASE)",
                }
            ],
            "current_step": "check_sufficiency",
        }

    try:
        llm = get_llm(
            provider=state.get("provider"),
            model=state.get("model"),
            temperature=0.0,
        ).with_structured_output(ContextSufficiencyAssessment)

        context_parts = []
        sources = []
        for idx, doc in enumerate(documents):
            meta = doc.get("metadata", {})
            src_name = meta.get("source") or meta.get("title") or f"Document #{idx+1}"
            context_parts.append(f"--- Document [{src_name}]:\n{doc.get('content', '')}")
            sources.append(
                {
                    "document_name": src_name,
                    "page_number": meta.get("page", 1),
                    "chunk_id": meta.get("chunk_id", ""),
                    "relevance_score": meta.get("relevance_score"),
                    "content_preview": doc.get("content", "")[:120] + "...",
                    "source_type": meta.get("source_type", "knowledge_base"),
                    "url": meta.get("url", ""),
                    "title": meta.get("title", ""),
                }
            )

        context_str = "\n\n".join(context_parts)
        history_str = "\n".join([f"{m.get('role')}: {m.get('content')}" for m in history]) if history else "None"

        prompt = CONTEXT_SUFFICIENCY_PROMPT.format(
            question=question,
            context=context_str,
            conversation_history=history_str,
        )

        assessment: ContextSufficiencyAssessment = llm.invoke(prompt)

        logger.info(
            f"[SufficiencyChecker] Evaluation Result: status={assessment.status} | "
            f"relevance={assessment.relevance_score}% | coverage={assessment.coverage_score}% | "
            f"reason={assessment.knowledge_gap_reason}"
        )

        status = assessment.status.upper()
        if status not in ["SUFFICIENT", "PARTIALLY_SUFFICIENT", "INSUFFICIENT", "IRRELEVANT"]:
            status = "INSUFFICIENT"

        if status == "SUFFICIENT":
            return {
                "answerability_status": "SUFFICIENT",
                "relevance_score": assessment.relevance_score,
                "coverage_score": assessment.coverage_score,
                "knowledge_gap_reason": "NONE",
                "available_information": assessment.available_information,
                "missing_information": assessment.missing_information or ["None"],
                "clarification_request": "",
                "context_assessment": assessment.model_dump(),
                "is_fully_answerable": True,
                "sources": sources,
                "workflow_steps": [
                    {
                        "step": "check_sufficiency",
                        "status": "completed",
                        "detail": (
                            f"Context Assessment: SUFFICIENT ({assessment.coverage_score}% coverage, "
                            f"{assessment.relevance_score}% relevance)"
                        ),
                    }
                ],
                "current_step": "check_sufficiency",
            }

        formatted_output = format_context_assessment_output(assessment)

        return {
            "answerability_status": status,
            "relevance_score": assessment.relevance_score,
            "coverage_score": assessment.coverage_score,
            "knowledge_gap_reason": assessment.knowledge_gap_reason,
            "available_information": assessment.available_information,
            "missing_information": assessment.missing_information,
            "clarification_request": assessment.clarification_request,
            "context_assessment": assessment.model_dump(),
            "is_fully_answerable": False,
            "generation": formatted_output,
            "sources": sources,
            "workflow_steps": [
                {
                    "step": "check_sufficiency",
                    "status": "completed",
                    "detail": (
                        f"Context Assessment: {status} ({assessment.coverage_score}% coverage, "
                        f"reason: {assessment.knowledge_gap_reason})"
                    ),
                }
            ],
            "current_step": "check_sufficiency",
        }

    except Exception as e:
        logger.error(f"[SufficiencyChecker] Error during sufficiency evaluation: {e}", exc_info=True)
        fallback_assessment = ContextSufficiencyAssessment(
            status="INSUFFICIENT",
            relevance_score=30,
            coverage_score=10,
            knowledge_gap_reason="PARTIAL_CONTEXT",
            available_information="Evaluation error encountered while parsing evidence.",
            missing_information=["Verified factual corroboration"],
            clarification_request=(
                f"The system encountered an error while assessing evidence: {e}. "
                "To prevent hallucinations, the system will not answer until evidence can be verified."
            ),
        )
        return {
            "answerability_status": "INSUFFICIENT",
            "relevance_score": fallback_assessment.relevance_score,
            "coverage_score": fallback_assessment.coverage_score,
            "knowledge_gap_reason": fallback_assessment.knowledge_gap_reason,
            "available_information": fallback_assessment.available_information,
            "missing_information": fallback_assessment.missing_information,
            "clarification_request": fallback_assessment.clarification_request,
            "context_assessment": fallback_assessment.model_dump(),
            "is_fully_answerable": False,
            "generation": format_context_assessment_output(fallback_assessment),
            "workflow_steps": [
                {
                    "step": "check_sufficiency",
                    "status": "error",
                    "detail": f"Sufficiency check error: {e}",
                }
            ],
            "current_step": "check_sufficiency",
        }
