#!/bin/bash
# ExamMemory AI — one-command startup
set -e

echo "📚 ExamMemory AI — Starting..."

cd backend

# Create venv if needed
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  echo "✅ Virtual environment created"
fi

# Activate
source .venv/bin/activate 2>/dev/null || .venv\Scripts\activate 2>/dev/null || true

# Install deps
pip install -r requirements.txt -q

# Copy .env if not present
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "✅ .env created (add OPENAI_API_KEY for real AI)"
fi

echo ""
echo "🚀 Starting server at http://127.0.0.1:8000"
echo "   Open that URL in your browser."
echo "   First startup fetches articles (~30 seconds)."
echo ""

uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
