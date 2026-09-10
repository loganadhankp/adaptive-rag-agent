import logging
import os
import uuid
from typing import List

from fastapi import HTTPException, UploadFile
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from agents.llm_factory import get_vector_store
from backend.models import DocumentResponse

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    def __init__(self, settings, repository, vector_store=None):
        self.settings = settings
        self.repository = repository
        self.vector_store = vector_store

    def _get_vector_store(self):
        if not self.vector_store:
            try:
                self.vector_store = get_vector_store()
            except Exception as e:
                logger.error(f"[KnowledgeBase] Error initializing vector store: {e}")
        return self.vector_store

    async def upload_document(
        self, file: UploadFile, conversation_id: str | None = None
    ) -> DocumentResponse:
        """Uploads a document, processes it, and adds it to the vector store."""
        logger.info(
            f"[KnowledgeBase] Starting upload for file: {file.filename} (conversation_id={conversation_id})"
        )
        allowed_extensions = {".pdf", ".docx", ".txt"}
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_extensions:
            logger.warning(f"[KnowledgeBase] Rejected unsupported file type: {ext}")
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

        # Save file
        os.makedirs(self.settings.DOCUMENTS_DIR, exist_ok=True)
        doc_id = str(uuid.uuid4())
        safe_filename = f"{doc_id}_{file.filename}"
        file_path = os.path.join(self.settings.DOCUMENTS_DIR, safe_filename)

        with open(file_path, "wb") as f:
            f.write(await file.read())
        logger.info(f"[KnowledgeBase] File saved to disk at {file_path}")

        # Load document
        try:
            if ext == ".pdf":
                loader = PyPDFLoader(file_path)
            elif ext == ".docx":
                loader = Docx2txtLoader(file_path)
            elif ext == ".txt":
                loader = TextLoader(file_path)
            docs = loader.load()
            logger.info(f"[KnowledgeBase] Loaded {len(docs)} raw pages/sections from {file.filename}")
        except Exception as e:
            logger.error(f"[KnowledgeBase] Error loading document {file.filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to parse document: {e}")

        # Split document
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.CHUNK_SIZE,
            chunk_overlap=self.settings.CHUNK_OVERLAP,
        )
        splits = text_splitter.split_documents(docs)
        logger.info(f"[KnowledgeBase] Split document into {len(splits)} chunks (chunk_size={self.settings.CHUNK_SIZE})")

        # Add to ChromaDB with conversation scoping
        for i, split in enumerate(splits):
            split.metadata.update(
                {
                    "source": file.filename,
                    "document_id": doc_id,
                    "chunk_id": f"{doc_id}_chunk_{i}",
                    "page": split.metadata.get("page", 0),
                    "source_type": "knowledge_base",
                    "conversation_id": conversation_id or "global",
                }
            )

        vstore = self._get_vector_store()
        if vstore:
            try:
                vstore.add_documents(splits)
                logger.info(f"[KnowledgeBase] Successfully stored {len(splits)} chunks into ChromaDB")
            except Exception as e:
                logger.error(f"[KnowledgeBase] Error storing chunks into ChromaDB: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to index document in vector store: {e}")
        else:
            logger.warning("[KnowledgeBase] Vector store not initialized; chunks not indexed")

        # Record in DB
        doc_record = self.repository.add_document_record(
            id=doc_id,
            filename=file.filename,
            file_type=ext.replace(".", ""),
            chunk_count=len(splits),
            conversation_id=conversation_id,
        )
        logger.info(f"[KnowledgeBase] Recorded document {doc_id} in SQLite repository")

        return DocumentResponse(
            id=doc_id,
            filename=file.filename,
            file_type=ext.replace(".", ""),
            chunk_count=len(splits),
            uploaded_at=doc_record["uploaded_at"] if isinstance(doc_record, dict) else str(doc_record),
            conversation_id=conversation_id,
        )

    async def list_documents(self, conversation_id: str | None = None) -> List[DocumentResponse]:
        """Lists all uploaded documents, optionally filtered by conversation_id."""
        docs = self.repository.get_documents(conversation_id=conversation_id)
        return [
            DocumentResponse(
                id=doc["id"] if isinstance(doc, dict) else doc.id,
                filename=doc["filename"] if isinstance(doc, dict) else doc.filename,
                file_type=doc["file_type"] if isinstance(doc, dict) else doc.file_type,
                chunk_count=doc["chunk_count"] if isinstance(doc, dict) else doc.chunk_count,
                uploaded_at=doc["uploaded_at"] if isinstance(doc, dict) else doc.uploaded_at,
                conversation_id=doc.get("conversation_id") if isinstance(doc, dict) else getattr(doc, "conversation_id", None),
            )
            for doc in docs
        ]

    async def delete_document(self, document_id: str) -> bool:
        """Deletes a document from the vector store, DB, and disk."""
        logger.info(f"[KnowledgeBase] Deleting document {document_id}")
        doc = self.repository.get_document(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        vstore = self._get_vector_store()
        try:
            if vstore:
                vstore.delete(where={"document_id": document_id})
                logger.info(f"[KnowledgeBase] Deleted chunks for {document_id} from vector store")
        except Exception as e:
            logger.warning(f"[KnowledgeBase] Warning deleting chunks from vector store: {e}")

        # Delete file from disk
        doc_filename = doc["filename"] if isinstance(doc, dict) else doc.filename
        file_path = os.path.join(
            self.settings.DOCUMENTS_DIR, f"{document_id}_{doc_filename}"
        )
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"[KnowledgeBase] Deleted file from disk at {file_path}")

        # Delete from SQLite
        self.repository.delete_document_record(document_id)
        logger.info(f"[KnowledgeBase] Deleted document record {document_id} from SQLite")
        return True
