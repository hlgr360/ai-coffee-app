#!/bin/bash
# AI: Automated Playwright E2E test runner for ai-coffee-app with isolated test DB
set -e

TEST_DB="coffee_test.db"
APP_PORT=8000

# 0. Kill any process using the app port
PID=$(lsof -ti tcp:$APP_PORT || true)
if [ -n "$PID" ]; then
  echo "Killing process on port $APP_PORT (PID $PID)"
  kill $PID
  sleep 1
fi

# 1. Remove old test DB if exists
if [ -f "$TEST_DB" ]; then
  rm "$TEST_DB"
fi

# 2. Initialize test DB
sqlite3 "$TEST_DB" < init_db.sql

# 3. Start FastAPI app with test DB in background
export COFFEE_DB_PATH="$TEST_DB"
uvicorn app:app --port $APP_PORT --host 127.0.0.1 &
APP_PID=$!

# 4. Wait for app to be ready (max 10s)
for i in {1..20}; do
  if curl -s http://127.0.0.1:$APP_PORT/login > /dev/null; then
    break
  fi
  sleep 0.5
done

# 5. Run all Playwright tests in tests/playwright
pytest tests/playwright
TEST_RESULT=$?

# 6. Stop FastAPI app
kill $APP_PID
wait $APP_PID 2>/dev/null

exit $TEST_RESULT
