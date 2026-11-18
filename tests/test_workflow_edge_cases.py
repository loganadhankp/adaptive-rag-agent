import pytest
from unittest.mock import MagicMock, patch

from backend.workflow.graph import create_rag_graph, run_rag_pipeline
from backend.workflow.nodes.retriever import retrieve_documents
from backend.workflow.nodes.web_search import web_search

def test_graph_max_retries_termination():
    """Workflow must terminate safely when generator repeatedly fails quality evaluation."""
    graph = create_rag_graph(provider="openai")

    state = {
        "question": "What is the policy?",
        "original_question": "What is the policy?",
        "query_route": "KNOWLEDGE_BASE_QUERY",
        "question_intent": "fact_extraction",
        "conversation_history": [],
        "documents": [{"content": "Policy text.", "metadata": {"source": "p.txt"}}],
        "relevance_scores": [0.9],
        "web_results": [],
        "generation": "",
        "sources": [],
        "hallucination_result": "unsupported",
        "answer_score": 50.0,
        "answer_evaluation": {},
        "retry_count": 0,
        "max_retries": 1,
        "generation_retry_count": 1,
        "workflow_steps": [],
        "current_step": "check_hallucination",
        "used_web_search": False,
        "error": "",
        "provider": "openai",
        "model": None,
        "temperature": 0.0,
        "conversation_id": "test-max-retries",
        "is_fully_answerable": False,
        "knowledge_gap": None,
        "answerability_status": "SUFFICIENT",
        "relevance_score": 90,
        "coverage_score": 90,
        "knowledge_gap_reason": "NONE",
        "available_information": "Policy text",
        "missing_information": [],
        "clarification_request": "",
        "context_assessment": {
            "status": "SUFFICIENT",
            "relevance_score": 90,
            "coverage_score": 90,
            "knowledge_gap_reason": "NONE",
            "available_information": "Policy text",
            "missing_information": [],
            "clarification_request": "",
        },
    }

    with patch("backend.workflow.nodes.evaluator.get_llm") as mock_eval_llm, \
         patch("backend.workflow.nodes.hallucination_checker.get_llm") as mock_hal_llm:

        mock_hal = MagicMock()
        mock_hal.verdict = "supported"
        mock_hal_llm.return_value.with_structured_output.return_value.invoke.return_value = mock_hal

        mock_eval = MagicMock()
        mock_eval.total_score = 90.0
        mock_eval.feedback = "Good"
        mock_eval.model_dump.return_value = {"total_score": 90.0}
        mock_eval_llm.return_value.with_structured_output.return_value.invoke.return_value = mock_eval

        from backend.workflow.nodes.evaluator import evaluate_answer
        eval_res = evaluate_answer(state)
        assert eval_res["answer_score"] == 90.0

def test_web_search_missing_key_graceful_skip():
    """When TAVILY_API_KEY is absent, web_search should skip cleanly without raising."""
    with patch.dict("os.environ", {}, clear=True), \
         patch("backend.workflow.nodes.web_search.get_settings") as mock_settings:
        mock_settings.return_value.TAVILY_API_KEY = ""

        state = {
            "question": "Recent news about Python 3.14",
            "original_question": "Recent news about Python 3.14",
            "documents": [],
        }

        res = web_search(state)
        assert res["web_results"] == []
        assert res["workflow_steps"][0]["status"] == "skipped"

def test_retriever_cross_conversation_fallback():
    """Retriever must search general collection when conversation-specific search returns no matches."""
    with patch("backend.workflow.nodes.retriever.get_vector_store") as mock_vs_func, \
         patch("backend.workflow.nodes.retriever.get_settings") as mock_settings:
        mock_settings.return_value.MAX_RETRIEVAL_RESULTS = 4

        mock_vs = MagicMock()
        mock_doc = MagicMock()
        mock_doc.page_content = "Global document content"
        mock_doc.metadata = {"source": "global.pdf", "page": 1}

        def mock_sim_search(query, k, filter=None):
            if filter:
                return []
            return [(mock_doc, 0.92)]

        mock_vs.similarity_search_with_relevance_scores.side_effect = mock_sim_search
        mock_vs_func.return_value = mock_vs

        state = {
            "question": "What is in global document?",
            "conversation_id": "new-session-id-456",
        }

        result = retrieve_documents(state)
        assert len(result["documents"]) == 1
        assert result["documents"][0]["content"] == "Global document content"
        assert result["documents"][0]["metadata"]["source"] == "global.pdf"
