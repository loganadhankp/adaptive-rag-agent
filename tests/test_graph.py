import unittest
from unittest.mock import MagicMock, patch

from langgraph_workflow.graph import create_rag_graph, run_rag_pipeline


class TestGraph(unittest.IsolatedAsyncioTestCase):
    def test_compile_graph(self):
        graph = create_rag_graph()
        self.assertIsNotNone(graph)

    @patch("langgraph_workflow.graph.create_rag_graph")
    async def test_run_rag_pipeline_invocation(self, mock_create):
        mock_graph = MagicMock()
        mock_create.return_value = mock_graph
        mock_graph.invoke.return_value = {
            "answer_score": 90,
            "generation": "Test answer",
        }

        result = await run_rag_pipeline("Test query?")
        self.assertEqual(result["answer_score"], 90)
        self.assertEqual(result["generation"], "Test answer")


if __name__ == "__main__":
    unittest.main()
