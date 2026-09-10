import os

import pytest
import requests


def is_url_up(url: str, timeout: int = 5) -> bool:
    try:
        r = requests.get(url, timeout=timeout)
        return r.status_code < 500
    except Exception:
        return False


TEST_MODE = os.environ.get("TEST_MODE", "").lower() in ["1", "true", "yes"]


@pytest.mark.skipif(not TEST_MODE, reason="Playwright E2E tests require TEST_MODE=true")
def test_streamlit_chat_retrieval_path():
    """End-to-end UI test for the Streamlit frontend using Playwright.

    Requirements: Playwright must be installed and browsers downloaded (`playwright install`).
    Start the backend and frontend before running this test:
      - Backend: `uvicorn backend.main:app --reload --port 8000`
      - Frontend: `streamlit run frontend/app.py`
    """
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        pytest.skip(f"Playwright not available: {e}")

    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8501")
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

    if not is_url_up(FRONTEND_URL):
        pytest.skip(f"Frontend not reachable at {FRONTEND_URL}")
    if not is_url_up(BACKEND_URL):
        pytest.skip(f"Backend not reachable at {BACKEND_URL}")

    def createConversation(page):
        # robustly click the New Chat by finding the closest button with matching text
        return page.locator('[data-testid="new-chat-button"]').evaluate(
            "el => { const btns = Array.from(document.querySelectorAll('button')); for (const b of btns){ if (b.innerText && b.innerText.toLowerCase().includes('new chat')){ b.click(); return true;} } return false; }"
        )

    def uploadKnowledgeBaseDocument(page, file_path: str):
        # find the upload file input and attach file; fall back to clicking the Upload button
        try:
            input_el = page.query_selector("input[type=file]")
            if input_el:
                input_el.set_input_files(file_path)
                # click Upload
                page.locator('[data-testid="kb-upload-button"]').evaluate(
                    "el => { const btns = Array.from(document.querySelectorAll('button')); for (const b of btns){ if (b.innerText && b.innerText.toLowerCase().includes('upload')){ b.click(); return true;} } return false; }"
                )
                return True
        except Exception:
            pass
        return False

    def sendMessage(page, text: str):
        # find a textarea or input and type then press Enter
        prompt = None
        for sel in [
            'textarea[placeholder="Type your message..."]',
            'input[placeholder="Type your message..."]',
            '[placeholder="Type your message..."]',
        ]:
            if page.query_selector(sel):
                prompt = sel
                break
        assert prompt, "Chat input not found"
        page.fill(prompt, text)
        page.keyboard.press("Enter")

    def waitForAssistantResponse(page, timeout=30000):
        # wait until assistant message appears or sources panel shows
        try:
            page.wait_for_selector('[data-testid="assistant-message"]', timeout=timeout)
            return True
        except Exception:
            try:
                page.wait_for_selector('[data-testid="source-panel"]', timeout=5000)
                return True
            except Exception:
                return False

    def verifySources(page):
        return bool(page.query_selector('[data-testid="source-item"]'))

    def verifyStatusItems(page):
        return bool(page.query_selector('[data-testid="status-item"]'))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()

        page.goto(FRONTEND_URL, timeout=60000)
        page.wait_for_selector('[data-testid="sidebar"]', timeout=30000)

        # Create a conversation
        assert createConversation(page), "Failed to create conversation"

        # Retrieval path: ask for work from home policy
        sendMessage(page, "What is the work from home policy?")

        # Wait for exact assistant response
        assert waitForAssistantResponse(
            page, timeout=30000
        ), "Assistant response did not appear"
        # verify assistant exact text
        assistant_text = page.locator(
            '[data-testid="assistant-message"]'
        ).last.inner_text()
        assert "Employees may work remotely three days per week." in assistant_text

        # verify source panel content
        assert page.query_selector(
            '[data-testid="source-panel"]'
        ), "Source panel missing"
        # check for expected document name
        page.wait_for_selector("text=sample_company_policy.pdf", timeout=5000)
        # check for relevance score
        page.wait_for_selector("text=0.92", timeout=5000)

        # verify status sequence
        page.click('[data-testid="status-panel"]')
        page.wait_for_selector("text=Retrieval Complete", timeout=5000)
        page.wait_for_selector("text=Relevance Check Passed", timeout=5000)
        page.wait_for_selector("text=Answer Generated", timeout=5000)
        page.wait_for_selector("text=Evaluation Passed", timeout=5000)

        ctx.close()
        browser.close()


@pytest.mark.skipif(not TEST_MODE, reason="Playwright E2E tests require TEST_MODE=true")
def test_streamlit_chat_rewrite_path():
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        pytest.skip(f"Playwright not available: {e}")

    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8501")
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

    if not is_url_up(FRONTEND_URL):
        pytest.skip(f"Frontend not reachable at {FRONTEND_URL}")
    if not is_url_up(BACKEND_URL):
        pytest.skip(f"Backend not reachable at {BACKEND_URL}")

    def createConversation(page):
        return page.locator('[data-testid="new-chat-button"]').evaluate(
            "el => { const btns = Array.from(document.querySelectorAll('button')); for (const b of btns){ if (b.innerText && b.innerText.toLowerCase().includes('new chat')){ b.click(); return true;} } return false; }"
        )

    def sendMessage(page, text: str):
        prompt = None
        for sel in [
            'textarea[placeholder="Type your message..."]',
            'input[placeholder="Type your message..."]',
            '[placeholder="Type your message..."]',
        ]:
            if page.query_selector(sel):
                prompt = sel
                break
        assert prompt, "Chat input not found"
        page.fill(prompt, text)
        page.keyboard.press("Enter")

    def waitForAssistantResponse(page, timeout=30000):
        try:
            page.wait_for_selector('[data-testid="assistant-message"]', timeout=timeout)
            return True
        except Exception:
            try:
                page.wait_for_selector('[data-testid="source-panel"]', timeout=5000)
                return True
            except Exception:
                return False

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()

        page.goto(FRONTEND_URL, timeout=60000)
        page.wait_for_selector('[data-testid="sidebar"]', timeout=30000)

        assert createConversation(page), "Failed to create conversation"

        # Ask a vague question that requires rewrite
        sendMessage(page, "What is the policy?")

        # Wait for rewrite step to be recorded in status panel
        # Status panel should include rewrite_query step detail
        page.wait_for_selector("text=Rewrote query", timeout=10000)

        # Then wait for assistant response and assert it contains canonical answer
        assert waitForAssistantResponse(page, timeout=30000)
        assistant_text = page.locator(
            '[data-testid="assistant-message"]'
        ).last.inner_text()
        assert "Employees may work remotely three days per week." in assistant_text

        ctx.close()
        browser.close()


@pytest.mark.skipif(not TEST_MODE, reason="Playwright E2E tests require TEST_MODE=true")
def test_streamlit_chat_fallback_path():
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        pytest.skip(f"Playwright not available: {e}")

    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8501")
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

    if not is_url_up(FRONTEND_URL):
        pytest.skip(f"Frontend not reachable at {FRONTEND_URL}")
    if not is_url_up(BACKEND_URL):
        pytest.skip(f"Backend not reachable at {BACKEND_URL}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()

        page.goto(FRONTEND_URL, timeout=60000)
        page.wait_for_selector('[data-testid="sidebar"]', timeout=30000)

        # create conversation
        page.locator('[data-testid="new-chat-button"]').evaluate(
            "el => { const btns = Array.from(document.querySelectorAll('button')); for (const b of btns){ if (b.innerText && b.innerText.toLowerCase().includes('new chat')){ b.click(); return true;} } return false; }"
        )

        # ask question that triggers tavily fallback
        for sel in [
            'textarea[placeholder="Type your message..."]',
            'input[placeholder="Type your message..."]',
            '[placeholder="Type your message..."]',
        ]:
            if page.query_selector(sel):
                page.fill(sel, "Work from home - please use tavily")
                page.keyboard.press("Enter")
                break

        # wait for assistant response (via web search)
        assert page.wait_for_selector(
            '[data-testid="assistant-message"]', timeout=20000
        )
        assistant_text = page.locator(
            '[data-testid="assistant-message"]'
        ).last.inner_text()
        assert "Employees may work remotely three days per week." in assistant_text

        # verify web source present
        assert page.query_selector(
            "text=https://example.com/wfh"
        ) or page.query_selector("text=example.com/wfh")

        ctx.close()
        browser.close()


@pytest.mark.skipif(not TEST_MODE, reason="Playwright E2E tests require TEST_MODE=true")
def test_streamlit_chat_regeneration_path():
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        pytest.skip(f"Playwright not available: {e}")

    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8501")
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

    if not is_url_up(FRONTEND_URL):
        pytest.skip(f"Frontend not reachable at {FRONTEND_URL}")
    if not is_url_up(BACKEND_URL):
        pytest.skip(f"Backend not reachable at {BACKEND_URL}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()

        page.goto(FRONTEND_URL, timeout=60000)
        page.wait_for_selector('[data-testid="sidebar"]', timeout=30000)

        # create conversation
        page.locator('[data-testid="new-chat-button"]').evaluate(
            "el => { const btns = Array.from(document.querySelectorAll('button')); for (const b of btns){ if (b.innerText && b.innerText.toLowerCase().includes('new chat')){ b.click(); return true;} } return false; }"
        )

        # ask a question that requires regeneration (mock will return low score first)
        for sel in [
            'textarea[placeholder="Type your message..."]',
            'input[placeholder="Type your message..."]',
            '[placeholder="Type your message..."]',
        ]:
            if page.query_selector(sel):
                page.fill(sel, "Provide a detailed work from home policy")
                page.keyboard.press("Enter")
                break

        # wait for assistant response
        assert page.wait_for_selector(
            '[data-testid="assistant-message"]', timeout=30000
        )
        assistant_text = page.locator(
            '[data-testid="assistant-message"]'
        ).last.inner_text()
        # final response should be improved canonical answer
        assert "Employees may work remotely three days per week." in assistant_text

        # verify that generate step appears at least twice (regeneration happened)
        page.click('[data-testid="status-panel"]')
        # count occurrences of 'Generate Answer' in status panel
        gen_count = len(page.locator("text=Generate Answer").all())
        assert gen_count >= 2, "Expected regeneration to run at least once"

        ctx.close()
        browser.close()
