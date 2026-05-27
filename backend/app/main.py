"""
ExamMemory AI — FastAPI backend v2.0
All original routes preserved + Weekly Test, Mock Test, PYQ, Leaderboard, PDF, AI Doubt.
"""
import datetime, os, asyncio
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .database import init_db, get_db, User, Article, ReadLog, RevisionSchedule, new_id
from .ingest import get_ingest_status, ingest_feeds
from .sources import sorted_sources
from .auth import hash_password, verify_password, create_access_token, require_user
from .weekly_test import get_current_week_test, submit_weekly_attempt, get_weekly_leaderboard
from .mock_test import get_mock_test, submit_mock_attempt, get_mock_leaderboard
from .pyq_matcher import seed_pyqs, match_pyqs, search_pyqs
from .pdf_generator import generate_pdf_bytes
from .leaderboard import get_leaderboard, get_user_rank, award_xp, XP_READ_ARTICLE, XP_REVISION_DONE
from .ai_doubt import answer_doubt

REVISION_NEXT_DAY = os.getenv("REVISION_NEXT_DAY", "false").lower() == "true"
INGEST_INTERVAL_SECONDS = int(os.getenv("INGEST_INTERVAL_SECONDS", "3600"))


async def _scheduled_ingest_loop():
    while True:
        await asyncio.sleep(INGEST_INTERVAL_SECONDS)
        try:
            await ingest_feeds()
        except Exception as e:
            print(f"[INGEST] Scheduled run failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("[BOOT] DB initialised")
    asyncio.create_task(ingest_feeds())
    asyncio.create_task(_scheduled_ingest_loop())
    print("[BOOT] RSS ingest started in background")
    from .database import SessionLocal
    _db = SessionLocal()
    seed_pyqs(_db)
    _db.close()
    print("[BOOT] PYQs seeded")
    yield


app = FastAPI(title="ExamMemory AI", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ── Pydantic schemas ───────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    name: str = "Student"
    target_exam: str = "UPSC"

class ReadRequest(BaseModel):
    user_id: str
    exam_type: str = "UPSC"

class RevisionSubmit(BaseModel):
    user_id: str
    schedule_ids: list[str]
    correct_count: int
    total_count: int

class SignupRequest(BaseModel):
    email: str
    password: str
    name: str = "Student"
    target_exam: str = "UPSC"
    guest_user_id: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class WeeklySubmit(BaseModel):
    user_id: str
    test_id: str
    answers: list

class MockSubmit(BaseModel):
    user_id: str
    test_id: str
    answers: list
    time_taken: int = 0

class DoubtRequest(BaseModel):
    question: str
    article_id: str


# ── Helpers ────────────────────────────────────────────────────────────────────
def _article_out(a: Article, exam: str = "UPSC") -> dict:
    return {
        "id":              a.id,
        "title":           a.title,
        "source_name":     a.source_name,
        "source_url":      a.source_url,
        "language":        getattr(a, "language", None) or "en",
        "category":        a.category,
        "importance_score":a.importance_score,
        "include":         a.include,
        "why_important":   a.why_important,
        "tags":            a.tags or [],
        "target_exams":    a.target_exams or [],
        "quick":           a.quick_json,
        "deep":            a.deep_json,
        "mcqs":            a.mcqs_json or [],
        "published_at":    a.published_at.isoformat() if a.published_at else None,
    }

def _schedule_revision(user_id, article_id, db):
    now  = datetime.datetime.utcnow()
    days = [2, 7, 21, 45] if REVISION_NEXT_DAY else [0, 7, 21, 45]
    for d in days:
        if not db.query(RevisionSchedule).filter(
            RevisionSchedule.user_id==user_id,
            RevisionSchedule.article_id==article_id,
            RevisionSchedule.day_number==d
        ).first():
            db.add(RevisionSchedule(id=new_id(), user_id=user_id, article_id=article_id,
                                    due_at=now+datetime.timedelta(days=d), day_number=d))
    db.commit()

def _update_streak(user, db):
    now  = datetime.datetime.utcnow().date()
    last = user.last_active.date() if user.last_active else None
    if last:
        delta = (now - last).days
        if delta == 1:  user.streak_days = (user.streak_days or 0) + 1
        elif delta > 1: user.streak_days = 1
    else:
        user.streak_days = 1
    user.last_active = datetime.datetime.utcnow()
    db.commit()

def _user_out(user):
    return {"id":user.id,"email":user.email,"name":user.name,
            "target_exam":user.target_exam,"streak_days":user.streak_days or 0,
            "xp_points":user.xp_points or 0}

def _auth_response(user):
    return {"token": create_access_token(user.id), "user": _user_out(user)}

def _normalize_email(e):
    return e.strip().lower()

def _merge_guest_progress(guest_id, account, db):
    if not guest_id or guest_id == account.id: return
    guest = db.query(User).filter(User.id==guest_id).first()
    if not guest or guest.email: return
    db.query(ReadLog).filter(ReadLog.user_id==guest_id).update({ReadLog.user_id:account.id},synchronize_session=False)
    db.query(RevisionSchedule).filter(RevisionSchedule.user_id==guest_id).update({RevisionSchedule.user_id:account.id},synchronize_session=False)
    if (guest.streak_days or 0) > (account.streak_days or 0): account.streak_days = guest.streak_days
    if guest.last_active and (not account.last_active or guest.last_active > account.last_active): account.last_active = guest.last_active
    db.delete(guest); db.commit()

def _category_accuracy(user_id, db):
    schedules = db.query(RevisionSchedule).filter(RevisionSchedule.user_id==user_id, RevisionSchedule.completed==True).all()
    if not schedules:
        return [{"name":"Economy","pct":88},{"name":"Polity","pct":74},{"name":"Environment","pct":61},{"name":"Int'l Relations","pct":79},{"name":"Sci & Tech","pct":85}]
    cats = {}
    for s in schedules:
        art = db.query(Article).filter(Article.id==s.article_id).first()
        if not art: continue
        c = art.category
        if c not in cats: cats[c]={"total":0,"sum":0}
        cats[c]["total"]+=1; cats[c]["sum"]+=(s.score_pct or 50)
    return [{"name":k,"pct":round(v["sum"]/v["total"])} for k,v in cats.items()]


# ═══════════════════════════════════════════════════════════
# ROUTES — Original (preserved exactly)
# ═══════════════════════════════════════════════════════════

@app.get("/api/health")
def health():
    ai_on = bool(os.getenv("OPENAI_API_KEY","") or os.getenv("ANTHROPIC_API_KEY",""))
    return {"status":"ok","ai":ai_on,"version":"2.0.0"}


@app.get("/api/sources")
def list_sources():
    return [{"name":s["name"],"language":s["language"],"priority":s["priority"],"boost":s.get("boost",0)} for s in sorted_sources()]


@app.post("/api/users")
def create_user(body: UserCreate, db: Session = Depends(get_db)):
    user = User(id=new_id(), name=body.name, target_exam=body.target_exam,
                last_active=datetime.datetime.utcnow(), streak_days=1)
    db.add(user); db.commit()
    return {"id":user.id,"name":user.name,"target_exam":user.target_exam}


@app.get("/api/users/{user_id}")
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id==user_id).first()
    if not user: raise HTTPException(404, "User not found")
    return {"id":user.id,"name":user.name,"streak_days":user.streak_days}


@app.post("/api/auth/signup")
def auth_signup(body: SignupRequest, db: Session = Depends(get_db)):
    email = _normalize_email(body.email)
    if not email or "@" not in email: raise HTTPException(400, "Valid email required")
    if len(body.password) < 6: raise HTTPException(400, "Password must be at least 6 characters")
    if db.query(User).filter(User.email==email).first(): raise HTTPException(409, "Email already registered")
    user = User(id=new_id(), email=email, password_hash=hash_password(body.password),
                name=body.name.strip() or "Student", target_exam=body.target_exam,
                last_active=datetime.datetime.utcnow(), streak_days=1)
    db.add(user); db.commit()
    if body.guest_user_id: _merge_guest_progress(body.guest_user_id, user, db); db.refresh(user)
    return _auth_response(user)


@app.post("/api/auth/login")
def auth_login(body: LoginRequest, db: Session = Depends(get_db)):
    email = _normalize_email(body.email)
    user  = db.query(User).filter(User.email==email).first()
    if not user or not user.password_hash: raise HTTPException(401, "Invalid email or password")
    if not verify_password(body.password, user.password_hash): raise HTTPException(401, "Invalid email or password")
    return _auth_response(user)


@app.get("/api/auth/me")
def auth_me(user: User = Depends(require_user)):
    return _user_out(user)


@app.get("/api/articles")
def list_articles(exam: str="UPSC", include_rejected: bool=False, db: Session=Depends(get_db)):
    q = db.query(Article)
    if not include_rejected: q = q.filter(Article.include==True)
    arts = q.order_by(Article.importance_score.desc(), Article.published_at.desc()).limit(60).all()
    return [_article_out(a, exam) for a in arts]


@app.get("/api/articles/{article_id}")
def get_article(article_id: str, db: Session=Depends(get_db)):
    a = db.query(Article).filter(Article.id==article_id).first()
    if not a: raise HTTPException(404, "Article not found")
    return _article_out(a)


@app.post("/api/articles/{article_id}/read")
def mark_read(article_id: str, body: ReadRequest, db: Session=Depends(get_db)):
    art = db.query(Article).filter(Article.id==article_id).first()
    if not art: raise HTTPException(404, "Article not found")
    user = db.query(User).filter(User.id==body.user_id).first()
    if not user:
        user = User(id=body.user_id, name="Student", target_exam=body.exam_type,
                    last_active=datetime.datetime.utcnow(), streak_days=1)
        db.add(user); db.commit()
    if not db.query(ReadLog).filter(ReadLog.user_id==body.user_id, ReadLog.article_id==article_id).first():
        db.add(ReadLog(id=new_id(), user_id=body.user_id, article_id=article_id, exam_type=body.exam_type))
        db.commit()
        award_xp(user, XP_READ_ARTICLE, db)
    _update_streak(user, db)
    _schedule_revision(body.user_id, article_id, db)
    return {"status":"logged","revision_scheduled":True}


@app.get("/api/dashboard/{user_id}")
def dashboard(user_id: str, db: Session=Depends(get_db)):
    user = db.query(User).filter(User.id==user_id).first()
    today_start = datetime.datetime.utcnow().replace(hour=0,minute=0,second=0,microsecond=0)
    today_count = db.query(Article).filter(Article.include==True, Article.published_at>=today_start).count()
    if today_count == 0: today_count = db.query(Article).filter(Article.include==True).count()
    now       = datetime.datetime.utcnow()
    due_count = db.query(RevisionSchedule).filter(RevisionSchedule.user_id==user_id,
        RevisionSchedule.due_at<=now, RevisionSchedule.completed==False).count()
    completed = db.query(RevisionSchedule).filter(RevisionSchedule.user_id==user_id,
        RevisionSchedule.completed==True, RevisionSchedule.score_pct!=None).all()
    retention = round(sum(s.score_pct for s in completed)/len(completed)) if completed else 82
    cat_acc   = _category_accuracy(user_id, db)
    weak      = [c["name"] for c in cat_acc if c["pct"] < 65]
    return {"today_news_count":today_count,"revision_due_count":due_count,"retention_score":retention,
            "streak_days":user.streak_days if user else 1,"xp_points":user.xp_points if user else 0,
            "weak_areas":weak,"category_accuracy":cat_acc}


@app.get("/api/revision/due/{user_id}")
def revision_due(user_id: str, db: Session=Depends(get_db)):
    now = datetime.datetime.utcnow()
    schedules = db.query(RevisionSchedule).filter(RevisionSchedule.user_id==user_id,
        RevisionSchedule.due_at<=now, RevisionSchedule.completed==False).limit(20).all()
    questions = []
    for s in schedules:
        art = db.query(Article).filter(Article.id==s.article_id).first()
        if not art or not art.mcqs_json: continue
        for mcq in art.mcqs_json:
            questions.append({"schedule_id":s.id,"article_id":art.id,"article_title":art.title,
                              "category":art.category,"day_number":s.day_number,"mcq":mcq})
    msg = (f"{len(schedules)} topics due — quick 2-minute quiz!" if schedules
           else "No revision due. Keep reading to build your queue.")
    return {"message":msg,"questions":questions}


@app.post("/api/revision/submit")
def revision_submit(body: RevisionSubmit, db: Session=Depends(get_db)):
    score_pct = round(body.correct_count/body.total_count*100) if body.total_count else 0
    user = db.query(User).filter(User.id==body.user_id).first()
    for sid in body.schedule_ids:
        s = db.query(RevisionSchedule).filter(RevisionSchedule.id==sid).first()
        if s:
            s.completed=True; s.score_pct=score_pct
            if score_pct < 50:
                db.add(RevisionSchedule(id=new_id(), user_id=s.user_id, article_id=s.article_id,
                    due_at=datetime.datetime.utcnow()+datetime.timedelta(days=1), day_number=s.day_number))
    db.commit()
    if user: award_xp(user, XP_REVISION_DONE * len(body.schedule_ids), db)
    feedback = ("Excellent! Next revision gap extended." if score_pct>=75
                else "Good effort. Repeat scheduled sooner for weak topics." if score_pct>=50
                else "Needs work — extra revision added to your queue.")
    return {"score_percent":score_pct,"feedback":feedback}


@app.post("/api/ingest/run")
async def trigger_ingest():
    status = get_ingest_status()
    if status.get("status") == "running":
        return {**status, "message": "Ingest already running"}
    asyncio.create_task(ingest_feeds())
    return {"status": "started", "message": "RSS ingest started in background"}


@app.get("/api/ingest/status")
def ingest_status():
    return get_ingest_status()


# ═══════════════════════════════════════════════════════════
# ROUTES — New features
# ═══════════════════════════════════════════════════════════

@app.get("/api/weekly-test")
def weekly_test(db: Session=Depends(get_db)):
    return get_current_week_test(db)

@app.post("/api/weekly-test/submit")
def weekly_test_submit(body: WeeklySubmit, db: Session=Depends(get_db)):
    return submit_weekly_attempt(db, body.user_id, body.test_id, body.answers)

@app.get("/api/weekly-test/leaderboard")
def weekly_lb(week: Optional[str]=None, db: Session=Depends(get_db)):
    return get_weekly_leaderboard(db, week)

@app.get("/api/mock-test")
def mock_test(exam_type: str="UPSC", month: Optional[str]=None, db: Session=Depends(get_db)):
    return get_mock_test(db, exam_type, month)

@app.post("/api/mock-test/submit")
def mock_test_submit(body: MockSubmit, db: Session=Depends(get_db)):
    return submit_mock_attempt(db, body.user_id, body.test_id, body.answers, body.time_taken)

@app.get("/api/mock-test/leaderboard")
def mock_lb(exam_type: str="UPSC", month: Optional[str]=None, db: Session=Depends(get_db)):
    return get_mock_leaderboard(db, month=month, exam_type=exam_type)

@app.get("/api/articles/{article_id}/pyqs")
def article_pyqs(article_id: str, db: Session=Depends(get_db)):
    return {"article_id":article_id,"pyqs":match_pyqs(article_id, db)}

@app.get("/api/pyqs/search")
def pyq_search(q: str, exam: Optional[str]=None, db: Session=Depends(get_db)):
    return {"query":q,"results":search_pyqs(q, db, exam)}

@app.get("/api/leaderboard")
def leaderboard(period: str="weekly", exam_type: str="UPSC", db: Session=Depends(get_db)):
    return get_leaderboard(db, period, exam_type)

@app.get("/api/leaderboard/me/{user_id}")
def my_rank(user_id: str, period: str="weekly", exam_type: str="UPSC", db: Session=Depends(get_db)):
    return get_user_rank(user_id, db, period, exam_type)

@app.get("/api/pdf/monthly")
def monthly_pdf(exam_type: str="UPSC", month: Optional[str]=None, db: Session=Depends(get_db)):
    try:
        pdf_bytes = generate_pdf_bytes(db, month, exam_type)
        label = month or datetime.datetime.utcnow().strftime("%Y-%m")
        if pdf_bytes[:4] == b"%PDF":
            return Response(content=pdf_bytes, media_type="application/pdf",
                headers={"Content-Disposition":f"attachment; filename=ExamMemory-{label}-{exam_type}.pdf"})
        return Response(content=pdf_bytes, media_type="text/html")
    except Exception as e:
        raise HTTPException(500, f"PDF generation failed: {e}")

@app.post("/api/doubt")
async def ask_doubt(body: DoubtRequest, db: Session=Depends(get_db)):
    if not body.question.strip(): raise HTTPException(400, "Question is required")
    return await answer_doubt(body.article_id, body.question.strip(), db)


# ── Static frontend ────────────────────────────────────────────────────────────
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")

if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(404, "API route not found")
        index = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index):
            return FileResponse(index)
        return {"detail":"Frontend not found"}
