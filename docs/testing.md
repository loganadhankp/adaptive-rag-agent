# Deterministic E2E Testing

This document describes how to run deterministic Playwright E2E tests using the project's TEST_MODE.

## Enabling Test Mode

Set environment variable `TEST_MODE=true` when starting the backend. Example:

Windows PowerShell:

```powershell
$env:TEST_MODE = 'true'
.venv\Scripts\uvicorn backend.main:app --reload --port 8000
```

Linux / macOS:

```bash
export TEST_MODE=true
.venv/bin/uvicorn backend.main:app --reload --port 8000
```

When `TEST_MODE` is enabled the following behaviors occur:

- `MockLLM` is used to generate deterministic answers for known questions.
- `mock_retriever` returns deterministic documents (see fixtures below).
- `mock_tavily` returns deterministic web search results for matching queries.
- External API calls are disabled.

## Fixtures

The repository includes a sample KB file: `data/sample/sample_company_policy.pdf`.
Its content is deterministic and used by the mock retriever metadata.

Known question mapping:

- Question: "What is the work from home policy?"
  - Response: "Employees may work remotely three days per week."
  - Source: `sample_company_policy.pdf`
  - Expected workflow status sequence: Retrieval Complete → Relevance Check Passed → Answer Generated → Evaluation Passed

## Running Playwright E2E Tests

1. Install dependencies and Playwright browsers:

```bash
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\playwright install
```

2. Start the backend in TEST_MODE (important):

```bash
# Windows PowerShell
$env:TEST_MODE = 'true'
.venv\Scripts\uvicorn backend.main:app --reload --port 8000
```

3. Start the frontend:

```bash
.venv\Scripts\streamlit run frontend/app.py
```

4. Run the E2E test (script uses Playwright):

```bash
.venv\Scripts\python -m pytest tests/test_e2e_ui.py -q
```

### Deterministic test scenarios covered

- Retrieval path: "What is the work from home policy?" → returns canonical answer from `sample_company_policy.pdf` and shows relevance score 0.92.
- Rewrite path: "What is the policy?" → triggers rewrite to "What is the work from home policy?" and returns canonical answer.
- Fallback (web search) path: include the phrase "use tavily" in the query to force retriever to return no documents; expected to use mock Tavily web result.
- Regeneration path: certain prompts will get a low evaluation on first generation and trigger regeneration; final answer becomes the canonical answer.

### Running deterministic tests with coverage

Use the provided convenience script (Windows PowerShell):

```powershell
.\scripts\run_deterministic_e2e_with_coverage.ps1
```

Or run pytest directly with coverage:

```bash
.venv\Scripts\pytest --cov=langgraph_workflow --cov-report=html:coverage_html tests/test_e2e_ui.py
```

Coverage report will be generated into the `coverage_html` directory.

## CI Integration Notes

The included GitHub Actions workflow `.github/workflows/ci.yml` runs the deterministic E2E tests on `ubuntu-latest` for Python 3.11 and 3.12. Key points:

- The workflow sets `TEST_MODE=true` to enable mock LLM, retriever, and Tavily.
- The backend and frontend are started as background processes and health-checked before tests run.
- Playwright browsers are installed via `python -m playwright install --with-deps`.
- Artifacts (coverage, logs, reports) are uploaded and retained for 14 days.

### Troubleshooting CI failures

- If code-quality checks fail, run `black .`, `isort .`, `flake8 .`, and `mypy .` locally to reproduce and fix issues.
- If Playwright tests fail in CI but pass locally, ensure `TEST_MODE=true` is set in the workflow and that the backend reached `/health` before tests start (check `logs/backend.log`).
- If browsers fail to install, confirm the `python -m playwright install --with-deps` step succeeds and has network access.

## Notes and Best Practices

- The test harness uses `data-testid` markers injected in the DOM for stable selectors. Avoid relying on visible text or Streamlit class names.
- If you need to extend deterministic mappings, edit `mocks/mock_llm.py`, `mocks/mock_retriever.py`, and `mocks/mock_tavily.py`.
- To run tests in CI (GitHub Actions), ensure you set `TEST_MODE=true`, install Playwright browsers, and start the backend and frontend as services before running the tests.

*** End of document ***
