import sys
import os
import sqlite3
import pathlib
import pytest
from fastapi.testclient import TestClient
from app import app

@pytest.fixture(scope="session")
def test_db_path():
    temp_dir = pathlib.Path(__file__).parent / "_tmp"
    temp_dir.mkdir(exist_ok=True)
    db_path = temp_dir / "test_coffee.db"
    yield str(db_path)
    if db_path.exists():
        db_path.unlink()

@pytest.fixture(scope="function")
def init_test_db(test_db_path):
    sql_path = pathlib.Path(__file__).parent.parent / "init_db.sql"
    with sqlite3.connect(test_db_path) as conn, open(sql_path) as f:
        conn.executescript(f.read())
    yield

@pytest.fixture(scope="function")
def client(test_db_path, monkeypatch):
    # Always re-init DB for each test for full isolation
    sql_path = pathlib.Path(__file__).parent.parent / "init_db.sql"
    with sqlite3.connect(test_db_path) as conn, open(sql_path) as f:
        conn.executescript(f.read())
    monkeypatch.setenv("COFFEE_DB_PATH", test_db_path)
    with TestClient(app) as c:
        yield c

def login_as_admin(client):
    resp = client.post("/login", data={"username": "admin", "password": "admin"})
    assert resp.status_code in (200, 302, 303, 307)
    # Follow redirect to password change
    if resp.is_redirect:
        resp = client.get(resp.headers["location"])
    return resp

# AI: Test that an admin can add and delete a user via the settings flyout
#      and that the user list updates accordingly.
def test_admin_can_add_and_delete_user(client):
    login_as_admin(client)
    # Add a new user
    resp = client.post("/settings/users/add", data={"username": "testuser", "password": "testpass"})
    assert resp.status_code in (200, 302, 303, 307)
    # User should now exist in the user list
    users = client.get("/api/users").json()["users"]
    assert any(u["username"] == "testuser" for u in users)
    # Delete the user
    user_id = next(u["id"] for u in users if u["username"] == "testuser")
    resp = client.post("/settings/users/delete", data={"user_id": user_id})
    assert resp.status_code in (200, 302, 303, 307)
    users = client.get("/api/users").json()["users"]
    assert not any(u["username"] == "testuser" for u in users)

# AI: Test that a user can add and delete a cup, and the cups list updates accordingly.
def test_user_can_add_and_delete_cup(client):
    login_as_admin(client)
    # Add a new cup
    resp = client.post("/settings/cups", data={"name": "Espresso", "size": 30})
    assert resp.status_code in (200, 302, 303, 307)
    cups = client.get("/api/cups").json()
    assert any(c["name"] == "Espresso" for c in cups)
    # Delete the cup
    cup_id = next(c["id"] for c in cups if c["name"] == "Espresso")
    resp = client.post("/settings/cups/delete", data={"cup_id": cup_id})
    assert resp.status_code in (200, 302, 303, 307)
    cups = client.get("/api/cups").json()
    assert not any(c["name"] == "Espresso" for c in cups)

# AI: Test that a coffee entry can be added and appears in the daily entries API.
def test_add_coffee_entry(client):
    login_as_admin(client)
    cups = client.get("/api/cups").json()
    cup_id = cups[0]["id"]
    resp = client.post("/add", data={"cup_id": cup_id})
    assert resp.status_code in (200, 302, 303, 307)
    # Check that the entry appears in the API
    entries = client.get("/api/entries").json()
    assert any(e["cup_id"] == cup_id for e in entries)

# AI: Test that the admin is forced to change password on first login, and that the flow works.
def test_forced_password_change(client, test_db_path):
    # Check admin must_change_password is set
    import sqlite3
    with sqlite3.connect(test_db_path) as conn:
        cur = conn.execute("SELECT must_change_password FROM users WHERE username = 'admin'")
        val = cur.fetchone()[0]
        assert val == 1, f"Expected must_change_password=1, got {val}"
    # Login as admin, should be forced to change password
    resp = client.post("/login", data={"username": "admin", "password": "admin"})
    # Instead of checking for redirect, check that the password change form is present
    assert "Change Password" in resp.text or "new_password" in resp.text, "Expected password change form after login with must_change_password"
    # Change password
    resp = client.post("/settings/password", data={"new_password": "newadminpass"})
    assert resp.status_code in (200, 302, 303, 307)
    # Logout and login with new password
    client.get("/logout")
    resp = client.post("/login", data={"username": "admin", "password": "newadminpass"})
    assert resp.status_code in (200, 302, 303, 307)
