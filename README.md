# ExamMemory AI — Phase 1 MVP

**Read today. Revise tomorrow. Remember in the exam.**

AI-powered current affairs memory engine for Indian government exam aspirants (UPSC, SSC, Banking, Railway, State PSC, Defence).

---

## What's in this release

| Feature | Status |
|---|---|
| RSS ingestion (PIB, Hindu, Express, PRS, RBI) | Hourly + on startup |
| AI filtering — importance score, category, include/reject | OpenAI or rule-based fallback |
| AI exam summaries — Quick Mode + Deep Mode + MCQs | OpenAI or template fallback |
| Read tracking per user (SQLite) | ✅ |
| Next-day revision quiz (spaced repetition) | Demo = same day; set `REVISION_NEXT_DAY=true` for prod |
| Dashboard: news count, revision due, streak, retention, weak areas | ✅ |
| **Demo mode** — full UI works with no backend | ✅ New |
| **Dark mode** — respects system preference + manual toggle | ✅ New |
| **Modal accessibility** — Escape key, focus trap | ✅ New |
| **Quiz loading state** — spinner while questions build | ✅ New |
| **Streak calendar** — 7-day visual dot row | ✅ New |
| **Category accuracy bars** | ✅ New |
| **Search clear button + click-to-open from results** | ✅ New |
| **Netlify API proxy** — deployed site now connects to backend | ✅ Fixed |

---

## Quick start — local

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env     # add OPENAI_API_KEY for real AI
uvicorn app.main:app --reload --port 8000
```

Open **http://127.0.0.1:8000** — API + frontend served together. First startup runs RSS ingest (1–2 min).

### 2. Frontend only (demo mode)

Open `index.html` directly in any browser. The site detects the backend is absent and activates **demo mode** with 5 realistic sample articles, a full revision quiz, and all UI features working.

### 3. Optional — real AI

Add to `backend/.env`:
```
OPENAI_API_KEY=sk-...
```
Without a key, the app uses keyword filtering and template summaries (fine for local demo).

---

## Deploying to Netlify

### Step 1 — Push frontend to GitHub

```bash
git add .
git commit -m "feat: ExamMemory AI MVP"
git push
```

### Step 2 — Connect repo on Netlify

Netlify → New site → Import from GitHub → select repo → publish directory: `.`

### Step 3 — Set environment variable

Netlify → Site settings → Environment variables:

```
EXAMMEMORY_API_URL = https://your-backend.fly.dev
```

The `netlify.toml` proxies all `/api/*` calls to your backend automatically.
If `EXAMMEMORY_API_URL` is not set, the frontend falls back to demo mode gracefully.

---

## API reference

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Health check + AI status |
| POST | `/api/users` | Create anonymous user |
| GET | `/api/users/{id}` | Validate user exists |
| GET | `/api/articles` | List articles (`?exam=UPSC&include_rejected=true`) |
| GET | `/api/articles/{id}` | Full summary + MCQs |
| POST | `/api/articles/{id}/read` | Log read + schedule revision |
| GET | `/api/dashboard/{user_id}` | Stats — count, streak, retention, weak areas, category_accuracy |
| GET | `/api/revision/due/{user_id}` | Revision quiz questions |
| POST | `/api/revision/submit` | Complete revision + update spaced schedule |
| POST | `/api/ingest/run` | Trigger RSS pipeline manually |

> **Note:** `GET /api/dashboard/{user_id}` should now return `category_accuracy` as an array of `{name, pct}` objects.

---

## Stack

- **Frontend:** Vanilla HTML + CSS + JS (served by FastAPI or Netlify)
- **Backend:** FastAPI, SQLAlchemy, SQLite, APScheduler, feedparser
- **AI:** OpenAI `gpt-4o-mini` (optional)
- **Fonts:** DM Serif Display + Sora (Google Fonts)

## Production roadmap (Phase 2+)

- PostgreSQL + auth (Supabase or Clerk)
- Day 7 / 21 / 45 spaced repetition scheduling
- Push + Telegram notifications
- Next.js frontend with SSR
- Weekly and monthly mock tests
