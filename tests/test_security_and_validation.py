import io
import os
import tempfile
import pytest
from fastapi import HTTPException, UploadFile
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.kb_service import KnowledgeBaseService
from backend.database.connection import DatabaseManager
from backend.database.repository import Repository
from backend.config import Settings
from backend.models import ChatRequest

client = TestClient(app)

class DummyVectorStore:
    def __init__(self):
        self.docs = []

    def add_documents(self, docs):
        self.docs.extend(docs)

    def delete(self, where=None):
        pass

@pytest.fixture
def temp_kb_service():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
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
        dummy_vs = DummyVectorStore()
        service = KnowledgeBaseService(settings, repo, vector_store=dummy_vs)
        yield service, settings, repo, tmpdir

@pytest.mark.asyncio
async def test_path_traversal_prevention_in_upload(temp_kb_service):
    """Path traversal attempt in filename must be sanitized to basename inside DOCUMENTS_DIR."""
    service, settings, repo, tmpdir = temp_kb_service

    malicious_filename = "../../evil_outside.txt"
    content = b"Harmless test content"
    upload_file = UploadFile(
        file=io.BytesIO(content),
        filename=malicious_filename,
    )

    res = await service.upload_document(upload_file)
    assert res.id is not None
    parent_of_docs = os.path.dirname(settings.DOCUMENTS_DIR)
    assert not os.path.exists(os.path.join(parent_of_docs, "evil_outside.txt"))
    saved_files = os.listdir(settings.DOCUMENTS_DIR)
    assert len(saved_files) == 1
    assert "evil_outside.txt" in saved_files[0]

@pytest.mark.asyncio
async def test_markdown_file_support(temp_kb_service):
    """Markdown (.md) files should be accepted and indexed."""
    service, settings, repo, tmpdir = temp_kb_service

    md_content = b"# Architecture Overview\n\nThis is a test markdown document for RAG indexing."
    upload_file = UploadFile(
        file=io.BytesIO(md_content),
        filename="overview.md",
    )

    res = await service.upload_document(upload_file)
    assert res.filename == "overview.md"
    assert res.file_type == "md"
    assert res.chunk_count > 0

@pytest.mark.asyncio
async def test_empty_file_rejected(temp_kb_service):
    """0-byte files should be rejected with HTTP 400."""
    service, settings, repo, tmpdir = temp_kb_service

    upload_file = UploadFile(
        file=io.BytesIO(b""),
        filename="empty.txt",
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.upload_document(upload_file)
    assert exc_info.value.status_code == 400
    assert "empty" in str(exc_info.value.detail).lower()

@pytest.mark.asyncio
async def test_oversized_file_rejected(temp_kb_service):
    """Files exceeding MAX_UPLOAD_SIZE_BYTES should be rejected with HTTP 413."""
    service, settings, repo, tmpdir = temp_kb_service
    setattr(settings, "MAX_UPLOAD_SIZE_BYTES", 1024)

    huge_content = b"A" * 2048
    upload_file = UploadFile(
        file=io.BytesIO(huge_content),
        filename="huge.txt",
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.upload_document(upload_file)
    assert exc_info.value.status_code == 413
    assert "exceeds" in str(exc_info.value.detail).lower()

@pytest.mark.asyncio
async def test_unsupported_file_extension(temp_kb_service):
    """Executable or script files (.exe, .sh) must be rejected with HTTP 400."""
    service, settings, repo, tmpdir = temp_kb_service

    upload_file = UploadFile(
        file=io.BytesIO(b"malicious script"),
        filename="payload.sh",
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.upload_document(upload_file)
    assert exc_info.value.status_code == 400

@pytest.mark.asyncio
async def test_corrupted_analytics_event_data_resilience(temp_kb_service):
    """Corrupted JSON in analytics_events table must not crash get_analytics_summary."""
    service, settings, repo, tmpdir = temp_kb_service

    with repo.db_manager.get_connection() as conn:
        conn.execute(
            "INSERT INTO analytics_events (id, conversation_id, event_type, event_data, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("evt-1", "conv-1", "answer_quality", "CORRUPTED_NOT_JSON{{", "2026-01-01T00:00:00"),
        )
        conn.commit()

    summary = repo.get_analytics_summary()
    assert summary is not None
    assert summary["avg_answer_quality"] == 0.0

def test_cors_headers_present():
    """OPTIONS request should return proper CORS headers."""
    response = client.options(
        "/api/chat/stream",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code in [200, 204]
    assert "access-control-allow-origin" in response.headers
