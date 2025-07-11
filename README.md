# ai-coffee-app
Vibe coded AI Coffee App

## Quickstart: Initialize Environment (Dev, Test, Prod)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/hlgr360/ai-coffee-app.git
   cd ai-coffee-app
   ```

2. **Create and activate a Python virtual environment (recommended):**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   - For pip users:
     ```bash
     pip install -r requirements.txt
     pip install -r requirements-test.txt
     ```
   - For uv users (recommended):
     ```bash
     uv pip install -e .[dev]
     # or
     uv pip install -r requirements-test.txt
     ```

4. **Initialize the database:**
   ```bash
   rm -f coffee.db && sqlite3 coffee.db < init_db.sql
   ```

5. **Run the app:**
   - Development (live reload):
     ```bash
     uv dev
     ```
   - Production:
     ```bash
     uvicorn app:app --host 0.0.0.0 --port 8000
     ```

6. **Run tests:**
   - Unit/integration:
     ```bash
     pytest --disable-warnings -v
     ```
   - End-to-end (browser):
     ```bash
     ./run_playwright_e2e.sh
     ```

7. **MCP/Context7/Playwright configuration:**
   - MCP server config is in `.vscode/mcp.json` (for advanced workflows)
   - Playwright MCP can be started with:
     ```bash
     npx @playwright/mcp@latest
     ```

## Testing Strategy (Summary)

- **Unit & Integration Tests:**
  - Located in `tests/` (e.g., `test_auth.py`, `test_user_management.py`)
  - Run with `pytest` and use an isolated test database.
- **End-to-End (E2E) Browser Tests:**
  - Implemented with Playwright (Python) in `tests/playwright/`
  - Covers full user/admin flows, password changes, permissions, and UI actions.
  - All web UI elements have stable `id` attributes for robust selectors.
- **Automated E2E Runner:**
  - `run_playwright_e2e.sh` resets the test DB, starts the app, runs all Playwright tests, and shuts down the app.
- **Best Practices:**
  - All new features must include appropriate tests (unit, integration, or E2E as needed).
  - If unsure about test coverage for a feature, prompt the developer for a decision.

## Development, Testing, and Runtime Commands

### 1. Environment Setup

#### Create and activate a virtual environment (recommended):
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Install dependencies:
```bash
pip install -r requirements-test.txt
```

### Using `uv` for Dependency Management

If you use [`uv`](https://github.com/astral-sh/uv) (recommended for fast installs and modern Python workflows):

#### Install all dependencies (including dev) from `pyproject.toml`:
```bash
uv pip install -e .[dev]
```

#### Or, install from requirements file:
```bash
uv pip install -r requirements-test.txt
```

This will set up your environment for development, testing, and running the app.

### 2. Initialize the Database

#### For development or runtime (creates/overwrites `coffee.db`):
```bash
rm -f coffee.db && sqlite3 coffee.db < init_db.sql
```

#### For tests (handled automatically, but you can manually reset):
```bash
rm -rf tests/_tmp && mkdir -p tests/_tmp
```

### 3. Running the App

#### Development (with live reload):
```bash
uv dev
```

#### Production (no reload):
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

### 4. Running the Tests

#### Run all tests with pytest:
```bash
uv pip install pytest && uv pip install -r requirements-test.txt && pytest --disable-warnings -v
```

#### Run all browser-based E2E tests:
```bash
./run_playwright_e2e.sh
```

#### Run a specific test file:
```bash
uv pip install pytest && uv pip install -r requirements-test.txt && pytest tests/test_full_app.py
```

### 5. Notes
- The default admin user is `admin` with password `admin` (must change on first login).
- All test cases are isolated and use a temporary database.
- All web UI elements have stable `id` attributes for E2E testing.
- See `.copilot` and `history.txt` for project conventions and requirements.
- The daily coffee table uses the ID `daily-coffee-table` for E2E test selectors.
- If you change any UI element IDs or flows, update both the Playwright tests and this documentation.
- Playwright E2E tests may require closing overlays/flyouts before interacting with the main UI (see test_full_user_flow.py for example).
