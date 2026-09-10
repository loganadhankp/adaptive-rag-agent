import operator
from typing import Annotated, TypedDict


class RAGState(TypedDict):
    question: str  # Current question (may be rewritten)
    original_question: str  # Original user question
    question_intent: str  # Classified intent: fact_extraction | summarization | analysis | recommendation | comparison
    conversation_history: list[dict]  # [{role, content}, ...]
    documents: list[dict]  # Retrieved docs with metadata
    relevance_scores: list[dict]  # Per-document grades
    web_results: list[dict]  # Web search results
    generation: str  # Generated answer
    sources: list[dict]  # Citation sources
    hallucination_result: str  # 'supported' | 'unsupported'
    answer_score: float  # Quality score 0-100
    answer_evaluation: dict  # Per-dimension breakdown
    retry_count: int  # Retry counter
    max_retries: int  # Max allowed retries
    generation_retry_count: int  # Generation-specific retries
    workflow_steps: Annotated[
        list[dict], operator.add
    ]  # Step log [{step, status, detail}]
    current_step: str  # Current node name
    used_web_search: bool  # Whether web search was used
    error: str  # Error message or empty string
    provider: str  # LLM provider (openai, anthropic, gemini)
    model: str  # Specific model name
    temperature: float  # Generation temperature
    conversation_id: str | None  # Session / conversation scope
    is_fully_answerable: bool  # Whether evidence is sufficient to fully answer
    knowledge_gap: dict | None  # Structured KnowledgeGapAnalysis result
