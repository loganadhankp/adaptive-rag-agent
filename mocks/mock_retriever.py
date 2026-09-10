def mock_retrieve(question: str, k: int = 4):
    """Return a deterministic set of documents for TEST_MODE.

    Each document is a dict with `page_content` and `metadata` similar to langchain's Document.
    """
    q = question.strip().lower()
    docs = []
    # Known fixture for work from home
    if "work from home" in q or "workfromhome" in q:
        content = (
            "Work From Home Policy:\nEmployees may work remotely three days per week."
        )
        docs.append(
            {
                "page_content": content,
                "metadata": {
                    "source": "sample_company_policy.pdf",
                    "page": 1,
                    "chunk_id": "chunk_1",
                    "relevance_score": 0.92,
                    "source_type": "knowledge_base",
                },
            }
        )
    else:
        # generic fallback document
        # If test requests tavily fallback, return no docs so web search is used
        if "use tavily" in q or "use_tavily" in q:
            return []

        docs.append(
            {
                "page_content": "Generic company policy content for testing.",
                "metadata": {
                    "source": "sample_company_policy.pdf",
                    "page": 1,
                    "chunk_id": "chunk_1",
                    "relevance_score": 0.5,
                },
            }
        )

    # replicate expected structure for similarity_search_with_relevance_scores
    results = []
    for d in docs[:k]:
        # return tuple (doc_like, score)
        results.append(
            (
                type(
                    "Doc",
                    (),
                    {"page_content": d["page_content"], "metadata": d["metadata"]},
                ),
                d["metadata"].get("relevance_score", 0.5),
            )
        )

    return results
