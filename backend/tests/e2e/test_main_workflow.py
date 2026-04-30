import os

import pytest


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_E2E") != "1",
    reason="Set RUN_E2E=1 and start backend/frontend services to run E2E tests.",
)


def test_main_workflow_through_browser() -> None:
    from playwright.sync_api import expect, sync_playwright

    frontend_url = os.getenv("FRONTEND_URL", "http://127.0.0.1:3000")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        try:
            page.goto(frontend_url, wait_until="networkidle")
            expect(page.get_by_role("heading", name="记一笔消费")).to_be_visible()
            expect(page.get_by_role("heading", name="攒钱计划")).to_be_visible()
            expect(page.get_by_role("heading", name="本月总览与统计")).to_be_visible()
        finally:
            browser.close()
