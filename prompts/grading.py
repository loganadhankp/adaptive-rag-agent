from typing import Literal

# flake8: noqa - prompt templates intentionally contain long lines
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


class RelevanceGrade(BaseModel):
    """Relevance grade for a retrieved document."""

    score: Literal["relevant", "partially_relevant", "irrelevant"] = Field(
        description="Relevance of the document to the question"
    )
    reasoning: str = Field(description="Brief explanation for the grade")


# ──────────────────────────────────────────────────────────────────────────────
# Question Intent Classification
# ──────────────────────────────────────────────────────────────────────────────

INTENT_LABELS = [
    "fact_extraction",
    "summarization",
    "analysis",
    "recommendation",
    "comparison",
]


class QuestionIntent(BaseModel):
    """Classified intent of the user's question."""

    intent: Literal[
        "fact_extraction",
        "summarization",
        "analysis",
        "recommendation",
        "comparison",
    ] = Field(description="The primary intent of the user's question")
    reasoning: str = Field(description="Brief explanation for the classification")


INTENT_SYSTEM_PROMPT = """You are a question intent classifier for a document-based Q&A system.

Classify the user's question into exactly one of these intents:

1. **fact_extraction** – The user wants a specific piece of factual information extracted verbatim from a document.
   Examples: "What is the phone number?", "When did they graduate?", "What is the leave policy?"

2. **summarization** – The user wants a condensed overview or summary of document content.
   Examples: "Summarize this PDF", "Give me the key points", "What are the main topics?"

3. **analysis** – The user wants evaluative reasoning, critique, assessment, or rating applied to document content.
   Examples: "How can this resume be improved?", "Rate this resume out of 10", "How strong is this for AI roles?", "What are the strengths and weaknesses?"

4. **recommendation** – The user wants actionable suggestions, advice, or proposals based on document content.
   Examples: "What skills should be added?", "What projects should be included?", "How should I restructure this?"

5. **comparison** – The user wants to compare, contrast, or differentiate content across documents or topics.
   Examples: "Compare these two reports", "What's different between section A and B?"

Return the single best-matching intent and a brief reasoning."""

INTENT_HUMAN_PROMPT = """Question: {question}"""

INTENT_PROMPT = ChatPromptTemplate.from_messages(
    [("system", INTENT_SYSTEM_PROMPT), ("human", INTENT_HUMAN_PROMPT)]
)

# Intents that require LLM reasoning over (not just extraction from) documents
ANALYTICAL_INTENTS = {"analysis", "recommendation", "comparison", "summarization"}


# ──────────────────────────────────────────────────────────────────────────────
# Document Relevance Grading
# ──────────────────────────────────────────────────────────────────────────────

GRADING_SYSTEM_PROMPT = """You are an expert document relevance grader.
Your task is to assess whether a given document contains information that is relevant to answering the user's question.
Focus on semantic relevance rather than keyword matching.

IMPORTANT: A document is relevant if it provides useful **context** for answering the question, even if it does not directly contain the literal answer. For example:
- If the user asks "How can this resume be improved?", a resume document IS relevant because the LLM needs its content to formulate improvement suggestions.
- If the user asks "Summarize this document", the document IS relevant because it is the subject being summarized.
- If the user asks analytical or recommendation questions about a document's content, the document IS relevant because it serves as the basis for analysis.

Assess the document based on the following criteria:
- 'relevant': The document directly answers the question, OR the document is the subject/context the question is asking about.
- 'partially_relevant': The document contains some related information that could help answer the question.
- 'irrelevant': The document does not contain information useful for answering the question AND is not the subject of the question.

Provide your reasoning before returning the final score."""

GRADING_HUMAN_PROMPT = """Question: {question}

Document: {document}"""

GRADING_PROMPT = ChatPromptTemplate.from_messages(
    [("system", GRADING_SYSTEM_PROMPT), ("human", GRADING_HUMAN_PROMPT)]
)

