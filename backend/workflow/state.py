import operator
from typing import Annotated, TypedDict


class RAGState(TypedDict):
    question: str  # Current question (may be rewritten)
    original_question: str  # Original user question
    query_route: str  # 'GENERAL_CHAT' | 'KNOWLEDGE_BASE_QUERY'
    question_intent: str  # Classified intent: fact_extraction | summarization | analysis | recommendation | comparison | general_chat
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
    answerability_status: str  # 'SUFFICIENT' | 'PARTIALLY_SUFFICIENT' | 'INSUFFICIENT' | 'IRRELEVANT'
    relevance_score: int  # Evidence relevance percentage 0-100
    coverage_score: int  # Evidence coverage percentage 0-100
    knowledge_gap_reason: str  # Reason: NONE | OUTSIDE_KNOWLEDGE_BASE | MISSING_DOCUMENT | PARTIAL_CONTEXT | MISSING_NUMERIC_DATA | AMBIGUOUS_QUERY
    available_information: str  # Factual info present in context
    missing_information: list[str]  # List of missing pieces of info
    clarification_request: str  # Request explaining abstention/missing info
    context_assessment: dict | None  # Serialized ContextSufficiencyAssessment
