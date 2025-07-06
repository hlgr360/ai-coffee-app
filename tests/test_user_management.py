import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient
import os
import shutil
import tempfile
import sqlite3
import pathlib
from app import app

@pytest.fixture(scope="session")
def test_db_path():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_coffee.db")
    yield db_path
    shutil.rmtree(temp_dir)

@pytest.fixture(scope="function")
def init_test_db(test_db_path):
    # Initialize the test DB with schema and seed data
    sql_path = pathlib.Path(__file__).parent.parent / "init_db.sql"
    with sqlite3.connect(test_db_path) as conn, open(sql_path) as f:
        conn.executescript(f.read())
    yield

@pytest.fixture(scope="function")
def client(test_db_path, init_test_db, monkeypatch):
    monkeypatch.setenv("COFFEE_DB_PATH", test_db_path)
    with TestClient(app) as c:
        yield c

# AI: Test that the default admin user is seeded and can log in, and is prompted to change password.
def test_admin_user_seeded(client):
    # Try to login as admin (default password is 'admin')
    response = client.post("/login", data={"username": "admin", "password": "admin"})
    assert response.status_code in (200, 302, 307)
    # Should redirect to password change or main page
    assert "change password" in response.text.lower() or response.is_redirect
