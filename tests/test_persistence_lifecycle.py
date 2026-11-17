import io
import os
import tempfile
import threading
import uuid
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.database.connection import DatabaseManager
from backend.database.repository import Repository
from backend.config import Settings
from backend.services.chat_service import ChatService
from backend.services.kb_service import KnowledgeBaseService
from backend.models import ChatRequest

client = TestClient(app)


def test_auto_create_conversation_when_passed_nonexistent_id():
    """If client sends a conversation_id that does not exist in SQLite, ChatService must auto-create it."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db_manager = DatabaseManager(db_path)
        db_manager.init_db()
        repo = Repository(db_manager)
        settings = Settings(SQLITE_DB_PATH=db_path)
        chat_service = ChatService(settings, repo)

        custom_id = str(uuid.uuid4())
        # Verify it doesn't exist yet
        assert repo.get_conversation(custom_id) is None

        req = ChatRequest(
            conversation_id=custom_id,
            message="",  # Empty message tests early exit and conversation creation
        )

        async def run_gen():
            events = []
            async for ev in chat_service.process_message(req):
                events.append(ev)
            return events

        import asyncio
        events = asyncio.run(run_gen())

        # Verify conversation was automatically created in the database
        conv = repo.get_conversation(custom_id)
        assert conv is not None
        assert conv["id"] == custom_id


def test_empty_prompt_yields_graceful_response():
    """Empty or whitespace prompts must return immediately with a friendly message without errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db_manager = DatabaseManager(db_path)
        db_manager.init_db()
        repo = Repository(db_manager)
        settings = Settings(SQLITE_DB_PATH=db_path)
        chat_service = ChatService(settings, repo)

        req = ChatRequest(message="    \n   ")

        async def run_gen():
            events = []
            async for ev in chat_service.process_message(req):
                events.append(ev)
            return events

        import asyncio
        events = asyncio.run(run_gen())

        event_types = [e.event for e in events]
        assert "conversation_id" in event_types
        assert "token" in event_types
        assert "done" in event_types
        # Verify friendly message
        token_data = [e.data for e in events if e.event == "token"][0]
        assert "Please enter a message" in token_data


def test_concurrent_sqlite_writes():
    """Multiple threads writing messages concurrently should not cause database lock errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_concurrent.db")
        db_manager = DatabaseManager(db_path)
        db_manager.init_db()
        repo = Repository(db_manager)

        conv_id = "test-concurrent-conv"
        repo.create_conversation(conv_id, title="Concurrent Test")

        errors = []

        def worker(idx):
            try:
                for i in range(15):
                    repo.add_message(
                        conversation_id=conv_id,
                        role="user" if i % 2 == 0 else "assistant",
                        content=f"Message {idx}-{i}",
                    )
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        messages = repo.get_messages(conv_id)
        assert len(messages) == 5 * 15


@pytest.mark.asyncio
async def test_document_lifecycle_and_deletion():
    """Uploading and deleting a document must remove SQLite record and file from disk."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_lifecycle.db")
        docs_dir = os.path.join(tmpdir, "docs")
        chroma_dir = os.path.join(tmpdir, "chroma")
        os.makedirs(docs_dir, exist_ok=True)
        os.makedirs(chroma_dir, exist_ok=True)

        settings = Settings(
            SQLITE_DB_PATH=db_path,
            DOCUMENTS_DIR=docs_dir,
            CHROMA_PERSIST_DIR=chroma_dir,
        )
        db_manager = DatabaseManager(db_path)
        db_manager.init_db()
        repo = Repository(db_manager)

        class MockVectorStore:
            def __init__(self):
                self.deleted = []
            def add_documents(self, docs):
                pass
            def delete(self, where=None):
                self.deleted.append(where)

        mock_vs = MockVectorStore()
        kb_service = KnowledgeBaseService(settings, repo, vector_store=mock_vs)

        from fastapi import UploadFile
        upload_file = UploadFile(
            file=io.BytesIO(b"Employee handbook text for lifecycle testing."),
            filename="handbook.txt",
        )
        doc_resp = await kb_service.upload_document(upload_file)
        doc_id = doc_resp.id

        # Verify recorded in DB
        assert repo.get_document(doc_id) is not None
        # Verify file on disk
        saved_file = os.path.join(docs_dir, f"{doc_id}_handbook.txt")
        assert os.path.exists(saved_file)

        # Delete document
        deleted = await kb_service.delete_document(doc_id)
        assert deleted is True

        # Verify removed from DB
        assert repo.get_document(doc_id) is None
        # Verify removed from disk
        assert not os.path.exists(saved_file)
        # Verify vector store delete called
        assert len(mock_vs.deleted) == 1
        assert mock_vs.deleted[0] == {"document_id": doc_id}
