import json
import logging
import uuid
from typing import AsyncGenerator

from sse_starlette.sse import ServerSentEvent
from backend.models import ChatRequest
from langgraph_workflow.graph import run_rag_pipeline

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, settings, repository):
        self.settings = settings
        self.repository = repository

    async def process_message(self, request: ChatRequest) -> AsyncGenerator:
        """Processes a chat message and streams the response via SSE."""
        conversation_id = request.conversation_id
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            new_title = request.message.strip().replace("\n", " ")[:28]
            if len(request.message.strip()) > 28:
                new_title += "..."
            self.repository.create_conversation(conversation_id, title=new_title)
        else:
            conv = self.repository.get_conversation(conversation_id)
            if conv and conv.get("title") in ["New Chat", "New Conversation"]:
                new_title = request.message.strip().replace("\n", " ")[:28]
                if len(request.message.strip()) > 28:
                    new_title += "..."
                self.repository.update_conversation_title(conversation_id, new_title)

        logger.info(f"[ChatService] Incoming message in conv {conversation_id}: '{request.message}'")
        conversation_history = self.repository.get_messages(conversation_id)
        self.repository.add_message(conversation_id=conversation_id, role="user", content=request.message)

        yield ServerSentEvent(
            event="conversation_id",
            data=json.dumps({"conversation_id": conversation_id}),
        )

        try:
            # Run RAG pipeline
            provider = request.provider or getattr(self.settings, "LLM_PROVIDER", "gemini")
            model = request.model or getattr(self.settings, "LLM_MODEL", "gemini-3.5-flash-lite")

            logger.info(
                f"[ChatService] Invoking RAG ({provider}/{model}, conv={conversation_id})..."
            )
            result = await run_rag_pipeline(
                question=request.message,
                conversation_history=conversation_history,
                provider=provider,
                model=model,
                temperature=request.temperature,
                conversation_id=conversation_id,
            )

            # Yield status events for workflow steps if applicable
            for step in result.get("workflow_steps", []):
                yield ServerSentEvent(event="status", data=json.dumps({"step": step}))

            # Determine generation text
            generation = result.get("generation", "")
            if not generation:
                if result.get("error"):
                    generation = f"⚠️ An error occurred during processing: {result.get('error')}"
                else:
                    generation = (
                        "I could not find enough relevant information in the Knowledge Base to answer your query."
                    )

            # Yield generation text in responsive chunks
            chunk_size = 24
            for i in range(0, len(generation), chunk_size):
                token_chunk = generation[i : i + chunk_size]
                yield ServerSentEvent(
                    event="token",
                    data=json.dumps({"text": token_chunk, "token": token_chunk}),
                )

            # Yield sources
            sources = result.get("sources", [])
            yield ServerSentEvent(
                event="sources",
                data=json.dumps({"sources": sources}),
            )

            # Yield metadata
            metadata = {
                "question_intent": result.get("question_intent", ""),
                "answer_score": result.get("answer_score"),
                "score": result.get("answer_score"),
                "answer_evaluation": result.get("answer_evaluation"),
                "evaluation": result.get("answer_evaluation"),
                "hallucination_result": result.get("hallucination_result"),
                "retry_count": result.get("retry_count", 0),
                "used_web_search": result.get("used_web_search", False),
                "is_fully_answerable": result.get("is_fully_answerable", True),
                "knowledge_gap": result.get("knowledge_gap"),
            }
            yield ServerSentEvent(
                event="metadata",
                data=json.dumps(metadata),
            )

            yield ServerSentEvent(event="done", data="")

            # Save assistant message
            self.repository.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=generation,
                sources=sources,
                workflow_metadata=metadata,
            )

            # Log analytics
            self.repository.log_analytics_event(
                conversation_id=conversation_id,
                event_type=("retrieval_success" if result.get("documents") else "retrieval_failure"),
            )
            if result.get("used_web_search"):
                self.repository.log_analytics_event(conversation_id, "web_search")
            if result.get("retry_count", 0) > 0:
                self.repository.log_analytics_event(conversation_id, "query_rewrite")
            if result.get("hallucination_result") == "unsupported":
                self.repository.log_analytics_event(conversation_id, "hallucination_failure")
            if result.get("knowledge_gap") and not result.get("is_fully_answerable"):
                self.repository.log_analytics_event(
                    conversation_id, "knowledge_gap_abstention", result.get("knowledge_gap")
                )
            if result.get("answer_score"):
                self.repository.log_analytics_event(
                    conversation_id, "answer_quality", {"score": result.get("answer_score")}
                )
            logger.info(f"[ChatService] Completed message processing for conv {conversation_id}")
        except Exception as e:
            logger.error(f"[ChatService] Uncaught error during chat processing: {e}", exc_info=True)
            error_msg = f"⚠️ System error: {e}"
            yield ServerSentEvent(
                event="token",
                data=json.dumps({"text": error_msg, "token": error_msg}),
            )
            yield ServerSentEvent(
                event="error",
                data=json.dumps({"detail": str(e)}),
            )
            yield ServerSentEvent(event="done", data="")
            self.repository.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=error_msg,
            )

    async def get_conversations(self) -> list:
        return self.repository.get_conversations()

    async def get_messages(self, conversation_id: str) -> list:
        return self.repository.get_messages(conversation_id)

    async def create_conversation(self, title: str = "New Chat") -> dict:
        conversation_id = str(uuid.uuid4())
        return self.repository.create_conversation(conversation_id, title=title)

    async def delete_conversation(self, conversation_id: str) -> bool:
        return self.repository.delete_conversation(conversation_id)
