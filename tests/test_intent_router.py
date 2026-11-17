import unittest
from unittest.mock import MagicMock, patch

from backend.workflow.graph import create_rag_graph
from backend.workflow.nodes.general_chat import generate_general_chat
from backend.workflow.nodes.intent_classifier import classify_intent
from backend.prompts.grading import QueryIntentRoute


class TestIntentRouter(unittest.TestCase):
    def test_fast_path_greetings(self):
        greetings = ["Hi", "hello", "Hey!", "Good morning", "how are you?", "thanks", "Bye"]
        for g in greetings:
            state = {"question": g}
            res = classify_intent(state)
            self.assertEqual(res["query_route"], "GENERAL_CHAT")
            self.assertEqual(res["question_intent"], "general_chat")

    @patch("backend.workflow.nodes.intent_classifier.get_llm")
    def test_general_programming_classified_as_general_chat(self, mock_get_llm):
        mock_llm_instance = MagicMock()
        mock_get_llm.return_value.with_structured_output.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value = QueryIntentRoute(
            intent="GENERAL_CHAT",
            reasoning="General programming question not referencing uploaded documents.",
        )

        queries = [
            "Explain Python OOP",
            "What is recursion?",
            "What is FastAPI?",
        ]
        for q in queries:
            state = {"question": q, "provider": "gemini"}
            res = classify_intent(state)
            self.assertEqual(res["query_route"], "GENERAL_CHAT")
            self.assertEqual(res["question_intent"], "general_chat")

    @patch("backend.workflow.nodes.intent_classifier.get_llm")
    def test_document_queries_classified_as_knowledge_base_query(self, mock_get_llm):
        mock_router_llm = MagicMock()
        mock_intent_llm = MagicMock()
        mock_get_llm.return_value.with_structured_output.side_effect = [
            mock_router_llm,
            mock_intent_llm,
        ]

        mock_router_llm.invoke.return_value = QueryIntentRoute(
            intent="KNOWLEDGE_BASE_QUERY",
            reasoning="Refers to uploaded documents/resume.",
        )
        mock_sub_intent = MagicMock()
        mock_sub_intent.intent = "fact_extraction"
        mock_intent_llm.invoke.return_value = mock_sub_intent

        state = {"question": "What phone number is in my uploaded resume?", "provider": "gemini"}
        res = classify_intent(state)
        self.assertEqual(res["query_route"], "KNOWLEDGE_BASE_QUERY")
        self.assertEqual(res["question_intent"], "fact_extraction")

    @patch("backend.workflow.nodes.general_chat.get_llm")
    def test_generate_general_chat_node(self, mock_get_llm):
        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm
        mock_resp = MagicMock()
        mock_resp.content = "FastAPI is a modern, fast web framework for building APIs with Python."
        mock_llm.invoke.return_value = mock_resp

        state = {
            "question": "What is FastAPI?",
            "conversation_history": [],
            "provider": "gemini",
        }
        res = generate_general_chat(state)
        self.assertEqual(res["query_route"], "GENERAL_CHAT")
        self.assertEqual(res["answerability_status"], "GENERAL_CHAT")
        self.assertIn("FastAPI is a modern", res["generation"])
        self.assertEqual(res["documents"], [])
        self.assertEqual(res["sources"], [])

    def test_graph_compilation_with_intent_routing(self):
        graph = create_rag_graph()
        self.assertIsNotNone(graph)
        self.assertIn("general_chat", graph.nodes)
        self.assertIn("classify_intent", graph.nodes)
        self.assertIn("retrieve", graph.nodes)
        self.assertIn("check_sufficiency", graph.nodes)


if __name__ == "__main__":
    unittest.main()
