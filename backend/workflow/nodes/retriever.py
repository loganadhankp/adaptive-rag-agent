import logging

from backend.agents.llm_factory import get_vector_store
from backend.config import get_settings
from backend.workflow.state import RAGState

logger = logging.getLogger(__name__)


def retrieve_documents(state: RAGState) -> dict:
    """Retrieve top-K matching document chunks from ChromaDB."""
    query = state.get("question", "")
    conv_id = state.get("conversation_id")
    is_retry = state.get("retry_count", 0) > 0
    step_name = "retry_retrieval" if is_retry else "retrieve_documents"
    logger.info(
        f"[Retriever] Querying ChromaDB with: '{query}' (conversation_id={conv_id}, is_retry={is_retry})"
    )
    try:
        settings = get_settings()
        vector_store = get_vector_store()

        # 1. If conversation_id is provided, try conversation-scoped search first
        results = []
        if conv_id:
            try:
                results = vector_store.similarity_search_with_relevance_scores(
                    query,
                    k=settings.MAX_RETRIEVAL_RESULTS,
                    filter={"conversation_id": conv_id},
                )
            except Exception as fe:
                logger.info(f"[Retriever] Scoped search exception ({fe}); falling back to general search")
                results = []

        # 2. If no conversation-scoped results found (or no conv_id), search across entire collection
        if not results:
            try:
                results = vector_store.similarity_search_with_relevance_scores(
                    query, k=settings.MAX_RETRIEVAL_RESULTS
                )
            except Exception as e:
                logger.info(f"[Retriever] General relevance score search failed ({e}); falling back to standard similarity search")
                results = []

        # 3. Fallback to standard similarity_search if relevance score search returns empty
        if not results:
            try:
                docs = vector_store.similarity_search(query, k=settings.MAX_RETRIEVAL_RESULTS)
                results = [(d, 0.85) for d in docs]
            except Exception as e:
                logger.warning(f"[Retriever] Fallback similarity search failed: {e}")
                results = []

        logger.info(f"[Retriever] Vector search returned {len(results)} matches")

        documents = []
        for doc, score in results:
            meta = dict(doc.metadata) if doc.metadata else {}
            meta["relevance_score"] = float(score)
            logger.info(
                f"[Retriever] Match: source={meta.get('source')} score={score:.3f} snippet={doc.page_content[:60]}..."
            )
            documents.append(
                {
                    "content": doc.page_content,
                    "metadata": meta,
                    "relevance_score": float(score),
                }
            )

        detail_text = (
            f"Retrieved {len(documents)} document chunk(s)"
            if documents
            else "No matching documents found in Knowledge Base"
        )

        return {
            "documents": documents,
            "workflow_steps": [
                {
                    "step": step_name,
                    "status": "completed",
                    "detail": detail_text,
                }
            ],
            "current_step": step_name,
        }
    except Exception as e:
        logger.error(f"[Retriever] Error retrieving documents: {e}", exc_info=True)
        return {
            "documents": [],
            "error": str(e),
            "workflow_steps": [
                {"step": step_name, "status": "error", "detail": str(e)}
            ],
            "current_step": step_name,
        }
