def mock_tavily_search(query: str, max_results: int = 3):
    """Return deterministic web search results for TEST_MODE.

    This provides predictable web fallbacks when no KB hit is available.
    """
    q = query.strip().lower()
    if "work from home" in q:
        return [
            {
                "title": "Company Work From Home Guidance",
                "url": "https://example.com/wfh",
                "content": "Employees may work remotely three days per week.",
            }
        ]
    return []
