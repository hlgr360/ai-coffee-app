# AI: Playwright end-to-end test for initial admin login and forced password change dialog
import pytest
from playwright.sync_api import sync_playwright

@pytest.mark.e2e
def test_admin_login_forced_password_change():
    """
    AI: This test verifies that the default admin user is prompted to change their password on first login.
    Steps:
    - Open the login page
    - Log in as admin/admin
    - Assert that the password change dialog/page is shown
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8000/login")
        page.fill('input[name="username"]', "admin")
        page.fill('input[name="password"]', "admin")
        page.click('button[type="submit"]')
        # Wait for navigation and check for password change form
        page.wait_for_load_state("networkidle")
        assert (
            "change password" in page.content().lower() or "new_password" in page.content().lower()
        ), "AI: Expected password change dialog after first admin login."
        browser.close()
