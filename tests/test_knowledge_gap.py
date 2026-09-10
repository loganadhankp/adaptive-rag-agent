import unittest
from unittest.mock import MagicMock, patch

from langgraph_workflow.nodes.knowledge_gap import (
    analyze_knowledge_gap,
    build_gap_explanation,
)
from prompts.knowledge_gap import KnowledgeGapAnalysis


class TestKnowledgeGap(unittest.TestCase):
    def test_example_1_completely_unrelated(self):
        NL = chr(10)
        analysis = KnowledgeGapAnalysis(
            answerable=False,
            relevance='irrelevant',
            requested_information='the company annual revenue',
            available_information='employee leave policies',
            missing_information=['annual revenue figures and financial statements'],
            required_information=['annual revenue figures', 'financial statements', 'annual reports'],
            recommended_document_type=['financial statements', 'annual reports'],
            reason='Knowledge Base contains leave policy, but no financial/revenue information.',
            abstention_type='irrelevant',
            supported_answer='',
            gap_explanation=(
                f'?? Knowledge Base Mismatch{NL}{NL}'
                f'Your question asks about the company annual revenue, but the uploaded Knowledge Base '
                f'contains information about employee leave policies and does not contain revenue data.{NL}{NL}'
                f'To answer this question correctly, annual revenue figures are required.{NL}{NL}'
                'Please upload a relevant document containing this information.'
            ),
        )
        self.assertFalse(analysis.answerable)
        self.assertEqual(analysis.abstention_type, 'irrelevant')
        explanation = build_gap_explanation(analysis)
        self.assertIn('Knowledge Base Mismatch', explanation)
        self.assertIn('annual revenue', explanation.lower())
        self.assertIn('leave', explanation.lower())

    def test_example_2_related_but_insufficient(self):
        NL = chr(10)
        analysis = KnowledgeGapAnalysis(
            answerable=False,
            relevance='partially_relevant',
            requested_information='number of annual leave days',
            available_information='employee annual leave eligibility',
            missing_information=['the specific number of leave days'],
            required_information=['specific annual leave entitlement containing the number of days'],
            recommended_document_type=['official leave policy addendum'],
            reason='Document discusses leave eligibility, but does not state the number of days.',
            abstention_type='insufficient',
            supported_answer='',
            gap_explanation=(
                f'?? Insufficient Knowledge Base Information{NL}{NL}'
                f'The uploaded document discusses employee annual leave, but does not specify leave days.{NL}{NL}'
                f'To answer this question correctly, leave details with number of days are required.{NL}{NL}'
                'Please upload or provide the relevant policy information.'
            ),
        )
        self.assertFalse(analysis.answerable)
        self.assertEqual(analysis.abstention_type, 'insufficient')
        explanation = build_gap_explanation(analysis)
        self.assertIn('Insufficient Knowledge Base Information', explanation)
        self.assertIn('leave', explanation.lower())

    def test_example_3_partial_information(self):
        NL = chr(10)
        analysis = KnowledgeGapAnalysis(
            answerable=False,
            relevance='partially_relevant',
            requested_information='Employee A salary and total compensation',
            available_information='Employee A as a Senior Software Engineer who joined in 2022',
            missing_information=['base salary', 'bonuses', 'benefits', 'stock/equity', 'total compensation'],
            required_information=['base salary', 'bonuses', 'benefits', 'stock/equity compensation'],
            recommended_document_type=['compensation or salary document'],
            reason='Document lists role and joining year, but contains no compensation data.',
            abstention_type='insufficient',
            supported_answer='',
            gap_explanation=(
                f'?? Insufficient Information{NL}{NL}'
                f'The Knowledge Base identifies Employee A as a Senior Software Engineer who joined in 2022, '
                f'but it does not contain salary or compensation information.{NL}{NL}'
                f'To calculate total compensation accurately, information about base salary is required.{NL}{NL}'
                'Please provide a relevant compensation or salary document.'
            ),
        )
        self.assertFalse(analysis.answerable)
        explanation = build_gap_explanation(analysis)
        self.assertIn('Insufficient Information', explanation)
        self.assertIn('Senior Software Engineer', explanation)
        self.assertIn('compensation', explanation.lower())

    def test_example_4_multipart_supported_and_missing(self):
        NL = chr(10)
        analysis = KnowledgeGapAnalysis(
            answerable=False,
            relevance='partially_relevant',
            requested_information='founding year, founders, and current revenue',
            available_information='company founded year (2010)',
            missing_information=['identifying the founders or the company current revenue'],
            required_information=['Founder information', 'Current/recent revenue or financial information'],
            recommended_document_type=['company or financial documents'],
            reason='Founded year is present, but founder names and current revenue are absent.',
            abstention_type='insufficient',
            supported_answer='Based on the uploaded Knowledge Base, the company was founded in 2010.',
            gap_explanation=(
                f'Based on the uploaded Knowledge Base, the company was founded in 2010.{NL}{NL}'
                f'However, the uploaded documents do not contain information identifying founders or revenue.{NL}{NL}'
                f'To answer the remaining parts correctly, the Knowledge Base needs:{NL}'
                f'* Founder information{NL}'
                f'* Current/recent revenue or financial information{NL}{NL}'
                'Please upload relevant company or financial documents containing these details.'
            ),
        )
        self.assertFalse(analysis.answerable)
        explanation = build_gap_explanation(analysis)
        self.assertIn('company was founded in 2010', explanation)
        self.assertIn('Founder information', explanation)
        self.assertIn('revenue', explanation.lower())

    def test_example_5_lexical_similarity_without_answerability(self):
        NL = chr(10)
        analysis = KnowledgeGapAnalysis(
            answerable=False,
            relevance='partially_relevant',
            requested_information='average salary of a Python developer',
            available_information='Python use in data science and machine learning',
            missing_information=['salary information for Python developers'],
            required_information=['salary data such as compensation surveys or relevant pay reports'],
            recommended_document_type=['compensation surveys', 'salary reports'],
            reason='Context mentions Python for ML, not developer salary.',
            abstention_type='unsupported',
            supported_answer='',
            gap_explanation=(
                f'The uploaded Knowledge Base discusses Python in data science and machine learning, '
                f'but it does not contain salary information for Python developers.{NL}{NL}'
                'To answer this question correctly, compensation survey data is required.'
            ),
        )
        self.assertFalse(analysis.answerable)
        self.assertEqual(analysis.abstention_type, 'unsupported')
        explanation = build_gap_explanation(analysis)
        self.assertIn('data science and machine learning', explanation)
        self.assertIn('salary', explanation.lower())

    def test_empty_documents_gap(self):
        state = {
            'question': 'What is the annual leave policy?',
            'documents': [],
            'conversation_history': [],
        }
        result = analyze_knowledge_gap(state)
        self.assertFalse(result['is_fully_answerable'])
        self.assertIn('Knowledge Base Mismatch', result['generation'])
        self.assertEqual(result['knowledge_gap']['abstention_type'], 'irrelevant')

    @patch('langgraph_workflow.nodes.knowledge_gap.get_llm')
    def test_fully_answerable_case(self, mock_get_llm):
        mock_llm_instance = MagicMock()
        mock_get_llm.return_value.with_structured_output.return_value = mock_llm_instance

        mock_llm_instance.invoke.return_value = KnowledgeGapAnalysis(
            answerable=True,
            relevance='relevant',
            requested_information='remote work allowance',
            available_information='Employees receive 3 days remote work per week with budget.',
            missing_information=[],
            required_information=[],
            recommended_document_type=[],
            reason='All requested information is fully present in the document.',
            abstention_type='none',
            supported_answer='',
            gap_explanation='',
        )

        state = {
            'question': 'How many days can employees work remotely?',
            'documents': [
                {
                    'content': 'Employees are eligible to work remotely up to 3 days per week.',
                    'metadata': {'source': 'handbook.pdf', 'page': 1, 'chunk_id': 'c1'},
                }
            ],
            'conversation_history': [],
        }

        result = analyze_knowledge_gap(state)
        self.assertTrue(result['is_fully_answerable'])
        self.assertEqual(result['knowledge_gap']['abstention_type'], 'none')


if __name__ == '__main__':
    unittest.main()
