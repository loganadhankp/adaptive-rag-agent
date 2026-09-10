from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    model: str | None = None
    temperature: float = 0.7
    provider: str | None = None


class ChatMessage(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    sources: list[dict] | None = None
    workflow_metadata: dict | None = None
    created_at: str


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int = 0


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    chunk_count: int
    uploaded_at: str
    conversation_id: str | None = None


class SourceCitation(BaseModel):
    document_name: str
    page_number: int | None = None
    chunk_id: str
    relevance_score: float | None = None
    content_preview: str = ""
    source_type: str = "knowledge_base"
    url: str | None = None


class WorkflowStatus(BaseModel):
    step: str
    status: str
    detail: str = ""


class AnalyticsSummary(BaseModel):
    total_conversations: int
    total_messages: int
    total_queries: int = 0
    retrieval_success_rate: float
    query_rewrites_count: int
    web_search_count: int
    hallucination_failures_count: int = 0
    avg_answer_quality: float
