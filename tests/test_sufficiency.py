import unittest
from unittest.mock import MagicMock, patch

from backend.workflow.graph import create_rag_graph
from backend.workflow.nodes.sufficiency_checker import check_sufficiency
from backend.prompts.sufficiency import (
    ContextSufficiencyAssessment,
    format_context_assessment_output,
)


class TestSufficiency(unittest.TestCase):
    def test_output_format_consistency_sufficient(self):
        assessment = ContextSufficiencyAssessment(
            status="SUFFICIENT",
            relevance_score=95,
            coverage_score=100,
            knowledge_gap_reason="NONE",
            available_information="Complete policy details found.",
            missing_information=["None"],
            clarification_request="",
        )
        formatted = format_context_assessment_output(assessment, final_answer="The policy allows 25 days.")
        self.assertEqual(formatted, "The policy allows 25 days.")

    def test_output_format_consistency_partially_sufficient(self):
        assessment = ContextSufficiencyAssessment(
            status="PARTIALLY_SUFFICIENT",
            relevance_score=80,
            coverage_score=50,
            knowledge_gap_reason="PARTIAL_CONTEXT",
            available_information="Employee name and start date are present.",
            missing_information=["Current salary", "Annual bonus"],
            clarification_request="Please provide compensation details.",
        )
        formatted = format_context_assessment_output(assessment)
        self.assertIn("**Available Information:**\nEmployee name and start date are present.", formatted)
        self.assertIn("**Missing Information / Issues:**\n* Current salary\n* Annual bonus", formatted)
        self.assertIn("**What is needed from you:**\nPlease provide compensation details.", formatted)
        self.assertNotIn("Final Answer:", formatted)

    def test_knowledge_gap_reasons_classification(self):
        reasons = [
            "NONE",
            "OUTSIDE_KNOWLEDGE_BASE",
            "MISSING_DOCUMENT",
            "PARTIAL_CONTEXT",
            "MISSING_NUMERIC_DATA",
            "AMBIGUOUS_QUERY",
        ]
        for reason in reasons:
            assessment = ContextSufficiencyAssessment(
                status="SUFFICIENT" if reason == "NONE" else "INSUFFICIENT",
                relevance_score=90 if reason == "NONE" else 20,
                coverage_score=90 if reason == "NONE" else 10,
                knowledge_gap_reason=reason,
                available_information="Sample info",
                missing_information=["None"] if reason == "NONE" else ["Sample gap"],
            )
            self.assertEqual(assessment.knowledge_gap_reason, reason)

    def test_check_sufficiency_empty_documents_yields_irrelevant(self):
        state = {
            "question": "What is the annual leave policy?",
            "documents": [],
            "conversation_history": [],
            "provider": "gemini",
        }
        res = check_sufficiency(state)
        self.assertEqual(res["answerability_status"], "IRRELEVANT")
        self.assertEqual(res["relevance_score"], 0)
        self.assertEqual(res["coverage_score"], 0)
        self.assertEqual(res["knowledge_gap_reason"], "OUTSIDE_KNOWLEDGE_BASE")
        self.assertFalse(res["is_fully_answerable"])
        self.assertIn("The uploaded document(s) do not contain enough information", res["generation"])
        self.assertIn("What is needed from you:", res["generation"])

    @patch("backend.workflow.nodes.sufficiency_checker.get_llm")
    def test_partially_sufficient_abstains_without_generation(self, mock_get_llm):
        mock_llm_instance = MagicMock()
        mock_get_llm.return_value.with_structured_output.return_value = mock_llm_instance

        mock_llm_instance.invoke.return_value = ContextSufficiencyAssessment(
            status="PARTIALLY_SUFFICIENT",
            relevance_score=75,
            coverage_score=50,
            knowledge_gap_reason="MISSING_NUMERIC_DATA",
            available_information="Employee role is Lead Engineer.",
            missing_information=["Exact base salary", "Equity compensation"],
            clarification_request="Please upload the official compensation schedule.",
        )

        state = {
            "question": "What is Logan's salary and role?",
            "documents": [{"content": "Logan is a Lead Engineer who joined in 2021.", "metadata": {"source": "doc1"}}],
            "conversation_history": [],
            "provider": "gemini",
        }

        res = check_sufficiency(state)
        self.assertEqual(res["answerability_status"], "PARTIALLY_SUFFICIENT")
        self.assertEqual(res["knowledge_gap_reason"], "MISSING_NUMERIC_DATA")
        self.assertFalse(res["is_fully_answerable"])
        self.assertIn("**Missing Information / Issues:**\n* Exact base salary\n* Equity compensation", res["generation"])

    @patch("backend.workflow.nodes.sufficiency_checker.get_llm")
    def test_graph_routing_sufficient_reaches_generation(self, mock_get_llm):
        mock_llm_instance = MagicMock()
        mock_get_llm.return_value.with_structured_output.return_value = mock_llm_instance

        mock_llm_instance.invoke.return_value = ContextSufficiencyAssessment(
            status="SUFFICIENT",
            relevance_score=95,
            coverage_score=100,
            knowledge_gap_reason="NONE",
            available_information="Full leave policy details present.",
            missing_information=["None"],
            clarification_request="",
        )

        graph = create_rag_graph()
        self.assertIsNotNone(graph)

        initial_state = {
            "question": "What is the policy?",
            "original_question": "What is the policy?",
            "question_intent": "fact_extraction",
            "conversation_history": [],
            "documents": [{"content": "Policy permits 25 days annual leave.", "metadata": {"source": "policy.pdf"}}],
            "relevance_scores": [],
            "web_results": [],
            "generation": "",
            "sources": [],
            "hallucination_result": "supported",
            "answer_score": 90.0,
            "answer_evaluation": {},
            "retry_count": 0,
            "max_retries": 1,
            "generation_retry_count": 0,
            "workflow_steps": [],
            "current_step": "",
            "used_web_search": False,
            "error": "",
            "provider": "gemini",
            "model": "gemini-3.5-flash-lite",
            "temperature": 0.0,
            "conversation_id": "test-conv",
            "is_fully_answerable": False,
            "knowledge_gap": None,
            "answerability_status": "",
            "relevance_score": 0,
            "coverage_score": 0,
            "knowledge_gap_reason": "",
            "available_information": "",
            "missing_information": [],
            "clarification_request": "",
            "context_assessment": None,
        }

        # Mock generator and hallucination/evaluator
        with patch("backend.workflow.nodes.generator.get_llm") as mock_gen_llm, \
             patch("backend.workflow.nodes.hallucination_checker.get_llm") as mock_hal_llm, \
             patch("backend.workflow.nodes.evaluator.get_llm") as mock_eval_llm, \
             patch("backend.workflow.graph.retrieve_documents") as mock_retrieve, \
             patch("backend.workflow.graph.classify_intent") as mock_classify:

            mock_classify.return_value = {"question_intent": "fact_extraction"}

            mock_retrieve.return_value = {
                "documents": [
                    {"content": "Policy permits 25 days annual leave.", "metadata": {"source": "policy.pdf"}}
                ],
                "workflow_steps": [{"step": "retrieve", "status": "completed"}],
                "current_step": "retrieve",
            }

            mock_gen_llm.return_value.invoke.return_value = "The policy permits 25 days of annual leave."

            mock_hal_res = MagicMock()
            mock_hal_res.verdict = "supported"
            mock_hal_res.reasoning = "grounded"
            mock_hal_llm.return_value.with_structured_output.return_value.invoke.return_value = mock_hal_res

            mock_eval_res = MagicMock()
            mock_eval_res.total_score = 92
            mock_eval_res.feedback = "Accurate"
            mock_eval_res.model_dump.return_value = {"total_score": 92}
            mock_eval_llm.return_value.with_structured_output.return_value.invoke.return_value = mock_eval_res

            graph = create_rag_graph()
            result = graph.invoke(initial_state)

            self.assertEqual(result["answerability_status"], "SUFFICIENT")
            self.assertTrue(result["is_fully_answerable"])
            self.assertEqual(result["generation"], "The policy permits 25 days of annual leave.")
            self.assertNotIn("Final Answer:", result["generation"])

    @patch("backend.workflow.nodes.sufficiency_checker.get_llm")
    def test_graph_routing_non_sufficient_never_calls_generator(self, mock_get_llm):
        for non_suff_status, reason in [
            ("PARTIALLY_SUFFICIENT", "PARTIAL_CONTEXT"),
            ("INSUFFICIENT", "MISSING_DOCUMENT"),
            ("IRRELEVANT", "OUTSIDE_KNOWLEDGE_BASE"),
        ]:
            mock_llm_instance = MagicMock()
            mock_get_llm.return_value.with_structured_output.return_value = mock_llm_instance

            mock_llm_instance.invoke.return_value = ContextSufficiencyAssessment(
                status=non_suff_status,
                relevance_score=30,
                coverage_score=10,
                knowledge_gap_reason=reason,
                available_information="Limited data.",
                missing_information=["Missing specific details"],
                clarification_request="Please upload required documentation.",
            )

            initial_state = {
                "question": "What is the secret formula?",
                "original_question": "What is the secret formula?",
                "question_intent": "fact_extraction",
                "conversation_history": [],
                "documents": [{"content": "Unrelated content", "metadata": {"source": "misc.pdf"}}],
                "relevance_scores": [],
                "web_results": [],
                "generation": "",
                "sources": [],
                "hallucination_result": "",
                "answer_score": 0.0,
                "answer_evaluation": {},
                "retry_count": 0,
                "max_retries": 1,
                "generation_retry_count": 0,
                "workflow_steps": [],
                "current_step": "",
                "used_web_search": False,
                "error": "",
                "provider": "gemini",
                "model": "gemini-3.5-flash-lite",
                "temperature": 0.0,
                "conversation_id": "test-conv",
                "is_fully_answerable": False,
                "knowledge_gap": None,
                "answerability_status": "",
                "relevance_score": 0,
                "coverage_score": 0,
                "knowledge_gap_reason": "",
                "available_information": "",
                "missing_information": [],
                "clarification_request": "",
                "context_assessment": None,
            }

            with patch("backend.workflow.nodes.generator.generate_answer") as mock_generate_node, \
                 patch("backend.workflow.graph.retrieve_documents") as mock_retrieve, \
                 patch("backend.workflow.graph.classify_intent") as mock_classify:

                mock_classify.return_value = {"question_intent": "fact_extraction"}

                mock_retrieve.return_value = {
                    "documents": [{"content": "Unrelated content", "metadata": {"source": "misc.pdf"}}],
                    "workflow_steps": [{"step": "retrieve", "status": "completed"}],
                    "current_step": "retrieve",
                }

                graph = create_rag_graph()
                result = graph.invoke(initial_state)

                # CRITICAL VERIFICATION: generator must NEVER be called
                mock_generate_node.assert_not_called()
                self.assertEqual(result["answerability_status"], non_suff_status)
                self.assertFalse(result["is_fully_answerable"])
                self.assertNotIn("Final Answer:", result["generation"])
                self.assertIn("What is needed from you:", result["generation"])


if __name__ == "__main__":
    unittest.main()
