from typing import List, Literal
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

# flake8: noqa - prompts contain long lines by design


class KnowledgeGapAnalysis(BaseModel):
    """Structured evaluation of evidence sufficiency and knowledge gaps."""

    answerable: bool = Field(
        description=(
            "True ONLY if the provided context contains ALL specific facts and evidence "
            "necessary to fully and directly answer the question without guessing or extrapolation. "
            "False if ANY required information is missing, vague, incomplete, or absent."
        )
    )
    relevance: Literal["relevant", "partially_relevant", "irrelevant"] = Field(
        description=(
            "'relevant' if context discusses the core subject; "
            "'partially_relevant' if context touches on related aspects or mentions similar keywords; "
            "'irrelevant' if context is completely unrelated to the question."
        )
    )
    requested_information: str = Field(
        description="Concise description of exactly what specific information or data the user is asking for."
    )
    available_information: str = Field(
        description="Factual summary of what relevant information, if any, was actually found in the context. State 'None' if context is completely unrelated."
    )
    missing_information: List[str] = Field(
        default_factory=list,
        description=(
            "List of specific, concrete pieces of information or data points missing from the context "
            "that are strictly required to answer the question. Do NOT include unrelated topics."
        ),
    )
    required_information: List[str] = Field(
        default_factory=list,
        description=(
            "Specific types of data or records needed to answer the question correctly "
            "(e.g. 'Annual revenue figures', 'Leave entitlement policy specifying exact days', "
            "'Compensation and salary breakdown'). Only identify what is actually needed."
        ),
    )
    recommended_document_type: List[str] = Field(
        default_factory=list,
        description="Specific document or data types the user should upload (e.g. 'Financial statements or annual reports', 'Official compensation schedule').",
    )
    reason: str = Field(
        description="Brief explanation of why the evidence is sufficient or insufficient to answer the question."
    )
    abstention_type: Literal["none", "irrelevant", "insufficient", "unsupported"] = Field(
        description=(
            "'none' if fully answerable; "
            "'irrelevant' if KB is completely mismatched (Example 1); "
            "'insufficient' if related or partial but missing key numbers/facts (Examples 2, 3, 4); "
            "'unsupported' if similar keywords/lexical match but wrong context/topic (Example 5)."
        )
    )
    supported_answer: str = Field(
        default="",
        description=(
            "If partially answerable (e.g. multi-part question where some facts ARE in the KB), "
            "provide the concise factual answer for ONLY the supported parts. If no part is supported, leave empty."
        ),
    )
    gap_explanation: str = Field(
        default="",
        description=(
            "A clear, professional, user-facing explanation following the required formats from Examples 1-5. "
            "Do NOT include hidden chain-of-thought or reasoning tokens. "
            "Clearly state what is missing, what is required, what document to upload, and that the system will not guess."
        ),
    )


KNOWLEDGE_GAP_SYSTEM_PROMPT = """You are a strict Evidence Sufficiency and Knowledge Gap Evaluator for an enterprise document Q&A assistant.

Your core responsibility:
1. UNDERSTAND the user's question and identify the exact information requested.
2. INSPECT the provided context documents to determine whether they contain sufficient evidence to answer FULLY and ACCURATELY.
3. If the context does NOT fully answer the question, perform an intelligent KNOWLEDGE GAP ANALYSIS.

CRITICAL RULES:
- NEVER guess, assume, extrapolate, or use general LLM training knowledge to supply missing facts.
- Lexical or keyword similarity DOES NOT EQUAL answerability. If a document mentions "Python" in the context of data science, that does NOT answer "What is the average salary of a Python developer?"
- DO NOT make generic abstention statements like "I couldn't find relevant information in the uploaded Knowledge Base" or "I don't know."
- DO NOT ASK FOR UNNECESSARY INFORMATION. Only identify what is strictly needed for the user's specific question. If asked for joining date, do not ask for salary or address.
- DO NOT REVEAL CHAIN OF THOUGHT. Do not output internal deliberation or hidden reasoning tokens. Output only the final structured assessment and clean, user-facing gap explanation.
- DO NOT THROW AWAY SUPPORTED INFORMATION in multi-part questions! If part of the question is answered by the context, state the supported answer first, then explain what is missing for the remaining parts.

FORMAT PATTERNS FOR GAP EXPLANATION:

[Pattern 1: Completely Unrelated Question / KB Mismatch]
Header: ?? Knowledge Base Mismatch
Explanation:
Your question asks about [requested information], but the uploaded Knowledge Base contains information about [what KB discusses] and does not contain [missing topic].

To answer this question correctly, information such as [required information] is required.

Please upload a relevant document containing this information. The system will not guess or use unsupported external knowledge.

[Pattern 2: Related but Insufficient Information]
Header: ?? Insufficient Knowledge Base Information
Explanation:
The uploaded document discusses [related topic found], but it does not specify [specific missing details/numbers].

To answer this question correctly, the Knowledge Base needs [required specific information].

Please upload or provide the relevant policy information. The system will not invent numbers or speculate.

[Pattern 3: Partial Information (Single Subject)]
Header: ?? Insufficient Information
Explanation:
The Knowledge Base identifies [what is available], but it does not contain [missing information].

To calculate or report [requested goal] accurately, information about [required information] is required.

Please provide a relevant [recommended document type]. The system will not extrapolate or guess figures.

[Pattern 4: Multi-part Question (Some parts supported, some missing)]
Explanation:
Based on the uploaded Knowledge Base, [supported facts answering the available parts].

However, the uploaded documents do not contain information [identifying the missing parts].

To answer the remaining parts correctly, the Knowledge Base needs:
* [Missing item 1]
* [Missing item 2]

Please upload relevant [recommended document types] containing these details. The system will not provide unsupported estimates.

[Pattern 5: Similar Words but Wrong Information]
Explanation:
The uploaded Knowledge Base discusses [what context actually discusses], but it does not contain [requested information].

To answer this question correctly, [required information] such as [recommended document types] is required. The system will not answer using unsupported general knowledge.

If answerable is True, set gap_explanation to empty string "" and abstention_type to "none"."""

KNOWLEDGE_GAP_HUMAN_PROMPT = """User Question:
{question}

Uploaded Knowledge Base Documents / Context:
{context}

Conversation History:
{conversation_history}

Evaluate evidence sufficiency and identify any knowledge gap:"""

KNOWLEDGE_GAP_PROMPT = ChatPromptTemplate.from_messages(
    [("system", KNOWLEDGE_GAP_SYSTEM_PROMPT), ("human", KNOWLEDGE_GAP_HUMAN_PROMPT)]
)
