# PowerShell script to run deterministic Playwright E2E tests with coverage
# Usage: run this after starting backend (TEST_MODE=true) and frontend.

$env:TEST_MODE = 'true'
$env:PYTEST_ADDOPTS = '--maxfail=1 -q'
.venv\Scripts\pytest --cov=langgraph_workflow --cov-report=html:coverage_html tests/test_e2e_ui.py
