import io
import time
import tempfile
import os
import statistics
import concurrent.futures
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.kb_service import KnowledgeBaseService
from backend.database.connection import DatabaseManager
from backend.database.repository import Repository
from backend.config import Settings
from fastapi import UploadFile

client = TestClient(app)

def test_measure_ingestion_latency():
    """Benchmark document ingestion and chunking speed for realistic document size."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "bench.db")
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

        class FastVectorStore:
            def add_documents(self, docs):
                pass

        service = KnowledgeBaseService(settings, repo, vector_store=FastVectorStore())

        sample_paragraphs = (
            "Enterprise Policy Section.\n"
            "Employees are eligible for 25 annual leave days and flexible remote hours.\n"
            "All expense submissions must be finalized within thirty calendar days.\n"
        ) * 400

        upload_file = UploadFile(
            file=io.BytesIO(sample_paragraphs.encode("utf-8")),
            filename="policy_benchmark.txt",
        )

        import asyncio
        start_t = time.perf_counter()
        doc = asyncio.run(service.upload_document(upload_file))
        duration = time.perf_counter() - start_t

        print(f"\n[Benchmark] Ingested {doc.chunk_count} chunks in {duration*1000:.2f} ms")
        assert duration < 2.0
        assert doc.chunk_count > 0

def test_measure_concurrent_endpoint_latency():
    """Benchmark health and metrics endpoint throughput across concurrent threads."""
    latencies = []

    def call_health():
        t0 = time.perf_counter()
        res = client.get("/health")
        t1 = time.perf_counter()
        assert res.status_code == 200
        return (t1 - t0) * 1000

    concurrency_levels = [1, 5, 10]
    results = {}

    for c in concurrency_levels:
        c_latencies = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=c) as executor:
            futures = [executor.submit(call_health) for _ in range(30)]
            for f in concurrent.futures.as_completed(futures):
                c_latencies.append(f.result())

        p50 = statistics.median(c_latencies)
        p95 = statistics.quantiles(c_latencies, n=20)[18] if len(c_latencies) >= 20 else max(c_latencies)
        results[c] = {"p50": p50, "p95": p95, "avg": statistics.mean(c_latencies)}
        print(f"\n[Benchmark] Concurrency={c}: p50={p50:.2f}ms, p95={p95:.2f}ms, avg={results[c]['avg']:.2f}ms")

    assert results[10]["avg"] < 150.0

def test_measure_fast_path_empty_prompt_ttft():
    """Measure Time to First Token (TTFT) for empty/whitespace input early return."""
    t0 = time.perf_counter()
    resp = client.post("/api/chat/stream", json={"message": "   "})
    t1 = time.perf_counter()
    duration_ms = (t1 - t0) * 1000
    print(f"\n[Benchmark] Early guard TTFT: {duration_ms:.2f} ms")
    assert resp.status_code == 200
    assert duration_ms < 100.0
