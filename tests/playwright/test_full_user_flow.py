import pytest
from playwright.sync_api import sync_playwright

@pytest.mark.e2e
def test_full_user_flow():
    """
    AI: This test covers the following E2E user flows:
    - Initial login as admin, forced password change
    - Change admin password
    - Add a test user (not admin) with password 'changeme'
    - Logout and login as test user, forced password change
    - Change test user password
    - Assert test user cannot add other users (no admin access)
    - Add a cup of coffee as test user
    - Logout
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # --- Admin initial login and forced password change ---
        page.goto("http://localhost:8000/login")
        page.fill('input[name="username"]', "admin")
        page.fill('input[name="password"]', "admin")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        assert "change password" in page.content().lower() or "new_password" in page.content().lower(), "AI: Expected password change dialog for admin."

        # Change admin password
        page.fill('input[name="new_password"]', "adminpass1!")
        page.fill('input[name="confirm_password"]', "adminpass1!")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        assert "settings" in page.content().lower(), "AI: Expected to see settings after admin password change."

        # Explicitly open settings flyout after password change
        page.click('#settings-icon')
        page.wait_for_selector('#user-management-table', timeout=3000)

        # Add test user (not admin)
        page.fill('input#new-username', "testuser")
        page.fill('input#new-password', "changeme")
        is_admin_checkbox = page.query_selector('input#new-is-admin')
        if is_admin_checkbox and is_admin_checkbox.is_checked():
            is_admin_checkbox.click()
        page.click('button#add-user-btn')
        page.wait_for_timeout(500)
        # Wait for the user to appear in the user management table inside the flyout
        user_row = page.wait_for_selector('#users-table-body tr:has-text("testuser")', timeout=2000)
        assert user_row is not None, "AI: testuser should appear in user table."

        # Logout admin
        # Close the settings flyout before logging out
        page.click('#close-settings-btn')
        page.wait_for_timeout(300)
        page.click('#logout-icon')
        page.wait_for_load_state("networkidle")
        assert "login" in page.content().lower(), "AI: Should be back at login after logout."

        # Login as testuser (should force password change)
        page.fill('input[name="username"]', "testuser")
        page.fill('input[name="password"]', "changeme")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        assert "change password" in page.content().lower() or "new_password" in page.content().lower(), "AI: Expected password change dialog for testuser."

        # Change testuser password
        page.fill('input[name="new_password"]', "userpass1!")
        page.fill('input[name="confirm_password"]', "userpass1!")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        assert "settings" in page.content().lower(), "AI: Expected to see settings after testuser password change."

        # Open settings flyout and assert no user management table (not admin)
        page.click('#settings-icon')
        page.wait_for_timeout(500)
        assert not page.query_selector('#user-management-table'), "AI: Non-admin should not see user management table."

        # Close the settings flyout before adding a cup of coffee
        page.click('#close-settings-btn')
        page.wait_for_timeout(300)
        # Add a cup of coffee (select first cup and click add)
        page.select_option('select#cup-select', index=0)
        page.click('button#add-coffee-btn')
        page.wait_for_timeout(500)
        # Assert the coffee entry appears in the table (look for the cup name or amount)
        assert page.query_selector('#daily-coffee-table tbody tr'), "AI: Coffee entry should appear in table."

        # Logout testuser
        page.click('#logout-icon')
        page.wait_for_load_state("networkidle")
        assert "login" in page.content().lower(), "AI: Should be back at login after logout."

        browser.close()
