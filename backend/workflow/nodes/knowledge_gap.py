import logging

from backend.agents.llm_factory import get_llm
from backend.workflow.state import RAGState
from backend.prompts.knowledge_gap import KNOWLEDGE_GAP_PROMPT, KnowledgeGapAnalysis

logger = logging.getLogger(__name__)


def build_gap_explanation(analysis: KnowledgeGapAnalysis) -> str:
    NL = chr(10)
    if analysis.gap_explanation and len(analysis.gap_explanation.strip()) > 20:
        return analysis.gap_explanation.strip()

    req_info_str = ', '.join(analysis.required_information) if analysis.required_information else 'relevant data'
    missing_str = ', '.join(analysis.missing_information) if analysis.missing_information else 'the requested details'
    rec_doc_str = (
        ', '.join(analysis.recommended_document_type)
        if analysis.recommended_document_type
        else 'relevant documents'
    )

    if analysis.supported_answer and analysis.supported_answer.strip():
        items = analysis.missing_information or analysis.required_information
        bullets = NL.join(['* ' + item for item in items])
        return (
            f'{analysis.supported_answer.strip()}{NL}{NL}'
            f'However, the uploaded documents do not contain information identifying {missing_str}.{NL}{NL}'
            f'To answer the remaining parts correctly, the Knowledge Base needs:{NL}{bullets}{NL}{NL}'
            f'Please upload relevant {rec_doc_str} containing these details. '
            'The system will not guess or provide unsupported estimates.'
        )

    if analysis.abstention_type == 'irrelevant' or analysis.relevance == 'irrelevant':
        avail_str = (
            analysis.available_information
            if analysis.available_information and analysis.available_information.lower() != 'none'
            else 'other topics'
        )
        return (
            f'?? Knowledge Base Mismatch{NL}{NL}'
            f'Your question asks about {analysis.requested_information}, but the uploaded Knowledge Base '
            f'contains information about {avail_str} and does not contain {missing_str}.{NL}{NL}'
            f'To answer this question correctly, information such as {req_info_str} is required.{NL}{NL}'
            f'Please upload a relevant document containing this information. '
            'The system will not guess or use unsupported external knowledge.'
        )

    if analysis.abstention_type == 'insufficient':
        return (
            f'?? Insufficient Knowledge Base Information{NL}{NL}'
            f'The uploaded document discusses {analysis.available_information}, '
            f'but it does not specify {missing_str}.{NL}{NL}'
            f'To answer this question correctly, the Knowledge Base needs {req_info_str}.{NL}{NL}'
            f'Please upload or provide the relevant {rec_doc_str}. '
            'The system will not invent numbers or extrapolate missing figures.'
        )

    return (
        f'The uploaded Knowledge Base discusses {analysis.available_information}, '
        f'but it does not contain {analysis.requested_information}.{NL}{NL}'
        f'To answer this question correctly, {req_info_str} such as {rec_doc_str} is required. '
        'The system will not answer using unsupported general knowledge.'
    )


def analyze_knowledge_gap(state: RAGState) -> dict:
    NL = chr(10)
    question = state.get('question', '')
    documents = state.get('documents', [])
    history = state.get('conversation_history', [])

    logger.info(
        f"[KnowledgeGap] Evaluating evidence sufficiency for: '{question}' "
        f"with {len(documents)} context document(s)..."
    )

    if not documents:
        logger.info('[KnowledgeGap] No context documents found. Generating Knowledge Base Mismatch response.')
        gap_data = {
            'answerable': False,
            'relevance': 'irrelevant',
            'requested_information': question,
            'available_information': 'No documents available in the Knowledge Base',
            'missing_information': ['All factual evidence required to answer this question'],
            'required_information': ['Official documentation or records covering this topic'],
            'recommended_document_type': ['Relevant policy, report, or reference document'],
            'reason': 'The Knowledge Base is empty or contains no relevant documents for this question.',
            'abstention_type': 'irrelevant',
            'supported_answer': '',
            'gap_explanation': (
                f'?? Knowledge Base Mismatch{NL}{NL}'
                f'Your question asks about {question}, but the uploaded Knowledge Base contains no documents '
                f'relevant to this inquiry.{NL}{NL}'
                f'To answer this question correctly, official documentation covering this topic is required.{NL}{NL}'
                'Please upload a relevant document containing this information. '
                'The system will not guess or use unsupported external knowledge.'
            ),
        }
        return {
            'is_fully_answerable': False,
            'generation': gap_data['gap_explanation'],
            'sources': [],
            'knowledge_gap': gap_data,
            'workflow_steps': [
                {
                    'step': 'knowledge_gap_analysis',
                    'status': 'completed',
                    'detail': 'Knowledge Base Mismatch: No relevant documents found',
                }
            ],
            'current_step': 'knowledge_gap_analysis',
        }

    try:
        llm = get_llm(
            provider=state.get('provider'),
            model=state.get('model'),
            temperature=state.get('temperature', 0.0),
        ).with_structured_output(KnowledgeGapAnalysis)

        context_parts = []
        sources = []
        for idx, doc in enumerate(documents):
            meta = doc.get('metadata', {})
            src_name = meta.get('source') or meta.get('title') or f'Document #{idx+1}'
            context_parts.append(f"--- Document [{src_name}]:{NL}{doc.get('content', '')}")
            sources.append(
                {
                    'document_name': src_name,
                    'page_number': meta.get('page', 1),
                    'chunk_id': meta.get('chunk_id', ''),
                    'relevance_score': meta.get('relevance_score'),
                    'content_preview': doc.get('content', '')[:120] + '...',
                    'source_type': meta.get('source_type', 'knowledge_base'),
                    'url': meta.get('url', ''),
                    'title': meta.get('title', ''),
                }
            )

        context_str = f'{NL}{NL}'.join(context_parts)
        history_str = f'{NL}'.join([f"{m.get('role')}: {m.get('content')}" for m in history]) if history else 'None'

        prompt = KNOWLEDGE_GAP_PROMPT.format(
            question=question,
            context=context_str,
            conversation_history=history_str,
        )

        analysis = llm.invoke(prompt)

        logger.info(
            f"[KnowledgeGap] Result: answerable={analysis.answerable} | "
            f"relevance='{analysis.relevance}' | abstention_type='{analysis.abstention_type}'"
        )
        logger.info(f"[KnowledgeGap] Reason: {analysis.reason}")

        if analysis.answerable:
            return {
                'is_fully_answerable': True,
                'knowledge_gap': analysis.model_dump(),
                'workflow_steps': [
                    {
                        'step': 'knowledge_gap_analysis',
                        'status': 'completed',
                        'detail': 'Evidence sufficiency confirmed: Knowledge Base can answer question fully',
                    }
                ],
                'current_step': 'knowledge_gap_analysis',
            }

        final_explanation = build_gap_explanation(analysis)

        return {
            'is_fully_answerable': False,
            'generation': final_explanation,
            'sources': sources,
            'knowledge_gap': analysis.model_dump(),
            'workflow_steps': [
                {
                    'step': 'knowledge_gap_analysis',
                    'status': 'completed',
                    'detail': f'Knowledge gap identified ({analysis.abstention_type}): {analysis.reason}',
                }
            ],
            'current_step': 'knowledge_gap_analysis',
        }

    except Exception as e:
        logger.error(f'[KnowledgeGap] Error during knowledge gap analysis: {e}', exc_info=True)
        return {
            'is_fully_answerable': True,
            'workflow_steps': [
                {
                    'step': 'knowledge_gap_analysis',
                    'status': 'error',
                    'detail': f'Knowledge gap analysis error: {e}',
                }
            ],
            'current_step': 'knowledge_gap_analysis',
        }
