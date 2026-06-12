#!/usr/bin/env bash
# ExamMemory AI one-command local startup.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
ENV_FILE="$BACKEND_DIR/.env"
ENV_EXAMPLE="$ROOT_DIR/.env.example"

echo "ExamMemory AI - starting local server"

if [ ! -d "$BACKEND_DIR" ]; then
  echo "Error: backend directory not found at $BACKEND_DIR"
  exit 1
fi

cd "$BACKEND_DIR"

if [ ! -d ".venv" ]; then
  if command -v python3 >/dev/null 2>&1; then
    python3 -m venv .venv
  elif command -v python >/dev/null 2>&1; then
    python -m venv .venv
  else
    echo "Error: Python is not installed or not available on PATH."
    exit 1
  fi
  echo "Created backend/.venv"
fi

if [ -f ".venv/Scripts/activate" ]; then
  # Git Bash on Windows
  # shellcheck disable=SC1091
  source ".venv/Scripts/activate"
elif [ -f ".venv/bin/activate" ]; then
  # macOS/Linux
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
else
  echo "Error: could not find the virtual environment activation script."
  exit 1
fi

python -m pip install --upgrade pip >/dev/null
pip install -r requirements.txt -q

if [ ! -f "$ENV_FILE" ]; then
  if [ -f "$ENV_EXAMPLE" ]; then
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    echo "Created backend/.env from .env.example"
  else
    echo "Warning: .env.example not found. Starting without backend/.env."
  fi
fi

if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

if [ "${OPENAI_API_KEY:-}" = "sk-..." ]; then
  unset OPENAI_API_KEY
fi

if [ "${ANTHROPIC_API_KEY:-}" = "sk-ant-..." ]; then
  unset ANTHROPIC_API_KEY
fi

# Backward compatibility with the current .env.example name.
if [ -z "${JWT_SECRET:-}" ] && [ -n "${SECRET_KEY:-}" ]; then
  export JWT_SECRET="$SECRET_KEY"
fi

export DB_PATH="${DB_PATH:-data/exammemory.db}"
export REVISION_NEXT_DAY="${REVISION_NEXT_DAY:-false}"
export INGEST_INTERVAL_SECONDS="${INGEST_INTERVAL_SECONDS:-3600}"

echo ""
echo "Server: http://127.0.0.1:8000"
echo "Database: $DB_PATH"
if [ -n "${OPENAI_API_KEY:-}" ] || [ -n "${ANTHROPIC_API_KEY:-}" ]; then
  echo "AI: enabled through configured API key(s)"
else
  echo "AI: rule-based fallback mode"
fi
echo ""

uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
