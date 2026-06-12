# ExamMemory AI

Read today. Revise tomorrow. Remember in the exam.

ExamMemory AI is a current-affairs revision app for Indian government exam aspirants, including UPSC, SSC, Banking, Railway, State PSC, and Defence. It ingests news feeds, filters exam-relevant articles, generates summaries and MCQs, schedules revision, and provides quizzes, mock tests, saved articles, filters, leaderboards, PDF/notes export, and an AI doubt solver.

## Project Structure

```text
.
|-- backend/
|   |-- app/
|   |   |-- main.py
|   |   |-- ai.py
|   |   |-- ingest.py
|   |   |-- database.py
|   |   |-- auth.py
|   |   |-- weekly_test.py
|   |   |-- mock_test.py
|   |   |-- pyq_matcher.py
|   |   |-- leaderboard.py
|   |   |-- pdf_generator.py
|   |   `-- ai_doubt.py
|   |-- openapi.json
|   `-- requirements.txt
|-- frontend/
|   |-- index.html
|   |-- scripts.js
|   `-- style.css
|-- .env.example
`-- start.sh
```

The FastAPI backend serves both the API and the frontend. When the backend is running, open `http://127.0.0.1:8000`.

## Features

| Feature | Status |
|---|---|
| RSS ingestion from exam-relevant sources | Available |
| AI/rule-based article filtering | Available |
| Quick and deep exam summaries | Available |
| MCQ generation | Available |
| Anonymous users and email/password auth | Available |
| Read tracking and revision scheduling | Available |
| Daily revision quiz | Available |
| Weekly test and monthly mock test | Available |
| PYQ matching | Available |
| Leaderboards and XP | Available |
| AI doubt solver | Available |
| Monthly PDF export | Available |
| Saved articles | Browser-local |
| Category/source/status/importance filters | Browser-local |
| Markdown notes export for filtered/saved articles | Browser-local |
| Demo mode when backend is unavailable | Available |
| Dark mode | Available |

## Quick Start

### Option 1: one-command startup

From the repo root:

```bash
./start.sh
```

The script will:

- create `backend/.venv` if needed
- install backend dependencies from `backend/requirements.txt`
- copy `.env.example` to `backend/.env` if `backend/.env` does not exist
- load values from `backend/.env`
- start FastAPI at `http://127.0.0.1:8000`

### Option 2: manual backend startup

From the repo root:

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows cmd
.venv\Scripts\activate.bat

# macOS/Linux/Git Bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a local environment file:

```bash
# Windows PowerShell, from backend/
Copy-Item ..\.env.example .env

# macOS/Linux/Git Bash, from backend/
cp ../.env.example .env
```

Start the server:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

## Environment Variables

Create `backend/.env` from the root `.env.example`.

Important variables:

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
REVISION_NEXT_DAY=false
DB_PATH=data/exammemory.db
JWT_SECRET=change-this-in-production
JWT_EXPIRE_DAYS=30
INGEST_INTERVAL_SECONDS=3600
```

Notes:

- `OPENAI_API_KEY` is optional. Without it, the app uses rule-based filtering and template summaries.
- `ANTHROPIC_API_KEY` is optional and used by the AI doubt solver when present.
- `DB_PATH` is relative to the backend folder when using `start.sh`.
- `JWT_SECRET` should be changed before production use.
- `start.sh` also maps older `SECRET_KEY` values to `JWT_SECRET` for compatibility.

## Frontend Notes

The frontend lives in `frontend/` and is served by FastAPI from `/static`.

Use the backend URL for the complete app:

```text
http://127.0.0.1:8000
```

Opening `frontend/index.html` directly may not load `/static/style.css` and `/static/scripts.js` in every browser because those paths are meant for FastAPI hosting.

Saved articles, article filters, and Markdown notes export are stored/handled in the browser with `localStorage`. They do not require backend migrations, but they also do not sync across devices yet.

## API Reference

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Health check and AI status |
| GET | `/api/sources` | List RSS sources |
| POST | `/api/users` | Create anonymous user |
| GET | `/api/users/{id}` | Validate user |
| POST | `/api/auth/signup` | Create account |
| POST | `/api/auth/login` | Log in |
| GET | `/api/auth/me` | Current authenticated user |
| GET | `/api/articles` | List articles |
| GET | `/api/articles/{id}` | Article details, summaries, MCQs |
| POST | `/api/articles/{id}/read` | Mark article read and schedule revision |
| GET | `/api/dashboard/{user_id}` | Dashboard stats |
| GET | `/api/revision/due/{user_id}` | Due revision questions |
| POST | `/api/revision/submit` | Submit revision result |
| POST | `/api/ingest/run` | Start RSS ingest |
| GET | `/api/ingest/status` | Ingest status |
| GET | `/api/weekly-test` | Current weekly test |
| POST | `/api/weekly-test/submit` | Submit weekly test |
| GET | `/api/weekly-test/leaderboard` | Weekly leaderboard |
| GET | `/api/mock-test` | Current monthly mock test |
| POST | `/api/mock-test/submit` | Submit mock test |
| GET | `/api/mock-test/leaderboard` | Mock leaderboard |
| GET | `/api/articles/{article_id}/pyqs` | Related previous-year questions |
| GET | `/api/pyqs/search` | Search PYQs |
| GET | `/api/leaderboard` | XP leaderboard |
| GET | `/api/leaderboard/me/{user_id}` | User rank |
| GET | `/api/pdf/monthly` | Monthly PDF export |
| POST | `/api/doubt` | AI doubt solver |

## Development Notes

- Backend: FastAPI, SQLAlchemy, SQLite, feedparser, httpx.
- Frontend: vanilla HTML, CSS, and JavaScript.
- The SQLite database is created under `backend/data/` by default.
- `backend/data/`, virtual environments, `.env`, and Python cache files are ignored by Git.
- On first startup, RSS ingest runs in the background. If feeds are unreachable, the backend seeds demo articles.

## Production Notes

Before production:

- set a strong `JWT_SECRET`
- use a production database such as PostgreSQL
- restrict CORS origins in `backend/app/main.py`
- provide real API keys through environment variables
- run the backend behind a production ASGI server/process manager
- consider moving saved articles from browser `localStorage` into the user account/database
