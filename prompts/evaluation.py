# flake8: noqa - prompt templates intentionally contain long lines
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


class AnswerEvaluation(BaseModel):
    """Evaluation of answer quality."""

    accuracy_score: int = Field(ge=0, le=25, description="Factual correctness score")
    completeness_score: int = Field(ge=0, le=25, description="Coverage score")
    groundedness_score: int = Field(ge=0, le=25, description="Source grounding score")
    relevance_score: int = Field(ge=0, le=25, description="Question relevance score")
    total_score: int = Field(ge=0, le=100, description="Total quality score")
    feedback: str = Field(description="Brief evaluation feedback")


# ──────────────────────────────────────────────────────────────────────────────
# MODE 1: Factual Evaluation
# ──────────────────────────────────────────────────────────────────────────────

FACTUAL_EVALUATION_SYSTEM_PROMPT = """You are an expert answer evaluator for a Retrieval-Augmented Generation (RAG) system.
Your task is to objectively evaluate a generated answer based on 4 dimensions, each scored from 0 to 25. The maximum total score is 100.

Dimensions:
1. Accuracy (0-25): Is the answer factually correct according to the provided sources?
2. Completeness (0-25): Does the answer cover all aspects of the user's question?
3. Groundedness (0-25): Is every claim in the answer grounded in the provided sources?
4. Relevance (0-25): Does the answer directly address the question without unnecessary tangents?

Provide a detailed evaluation and calculate the final scores. Include brief, constructive feedback on how the answer could be improved."""

# ──────────────────────────────────────────────────────────────────────────────
# MODE 2: Analytical Evaluation
# ──────────────────────────────────────────────────────────────────────────────

ANALYTICAL_EVALUATION_SYSTEM_PROMPT = """You are an expert answer evaluator for a document analysis and advisory system.
The answer is a response to an analytical, advisory, or recommendation question where the LLM uses document content as context but applies its own reasoning and expertise.

Your task is to objectively evaluate the generated answer based on 4 dimensions, each scored from 0 to 25. The maximum total score is 100.

Dimensions:
1. Accuracy (0-25): Are the factual references to document content correct? Is the LLM's domain knowledge sound?
2. Completeness (0-25): Does the answer thoroughly address the question? Does it cover multiple relevant aspects?
3. Groundedness (0-25): Does the answer reference specific content from the source documents to support its points? Note: analytical insights and recommendations beyond what's literally written are expected and should NOT be penalized.
4. Relevance (0-25): Does the answer directly address the question with actionable, constructive, and specific advice?

Provide a detailed evaluation and calculate the final scores. Include brief, constructive feedback on how the answer could be improved."""

EVALUATION_HUMAN_PROMPT = """Question: {question}

Source Documents:
{documents}

Generated Answer: {answer}"""

# Default (backward compatible)
EVALUATION_SYSTEM_PROMPT = FACTUAL_EVALUATION_SYSTEM_PROMPT

EVALUATION_PROMPT = ChatPromptTemplate.from_messages(
    [("system", EVALUATION_SYSTEM_PROMPT), ("human", EVALUATION_HUMAN_PROMPT)]
)

FACTUAL_EVALUATION_PROMPT = ChatPromptTemplate.from_messages(
    [("system", FACTUAL_EVALUATION_SYSTEM_PROMPT), ("human", EVALUATION_HUMAN_PROMPT)]
)

ANALYTICAL_EVALUATION_PROMPT = ChatPromptTemplate.from_messages(
    [("system", ANALYTICAL_EVALUATION_SYSTEM_PROMPT), ("human", EVALUATION_HUMAN_PROMPT)]
)

