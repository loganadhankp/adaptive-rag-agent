import operator
from typing import Annotated, TypedDict

class RAGState(TypedDict):
    question: str
    original_question: str
    query_route: str
    question_intent: str
    conversation_history: list[dict]
    documents: list[dict]
    relevance_scores: list[dict]
    web_results: list[dict]
    generation: str
    sources: list[dict]
    hallucination_result: str
    answer_score: float
    answer_evaluation: dict
    retry_count: int
    max_retries: int
    generation_retry_count: int
    workflow_steps: Annotated[
        list[dict], operator.add
    ]
    current_step: str
    used_web_search: bool
    error: str
    provider: str
    model: str
    temperature: float
    conversation_id: str | None
    is_fully_answerable: bool
    knowledge_gap: dict | None
    answerability_status: str
    relevance_score: int
    coverage_score: int
    knowledge_gap_reason: str
    available_information: str
    missing_information: list[str]
    clarification_request: str
    context_assessment: dict | None
