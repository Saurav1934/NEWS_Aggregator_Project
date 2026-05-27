from sqlalchemy import create_engine, Column, String, Float, Boolean, Integer, DateTime, Text, JSON, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime, uuid, os

DB_PATH = os.getenv("DB_PATH", "data/exammemory.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def new_id():
    return str(uuid.uuid4())[:8]


class User(Base):
    __tablename__ = "users"
    id            = Column(String, primary_key=True, default=new_id)
    email         = Column(String, unique=True, nullable=True, index=True)
    password_hash = Column(String, nullable=True)
    name          = Column(String, default="Student")
    target_exam   = Column(String, default="UPSC")
    streak_days   = Column(Integer, default=0)
    last_active   = Column(DateTime, nullable=True)
    xp_points     = Column(Integer, default=0)
    created_at    = Column(DateTime, default=datetime.datetime.utcnow)


class Article(Base):
    __tablename__ = "articles"
    id               = Column(String, primary_key=True, default=new_id)
    title            = Column(String)
    source_name      = Column(String)
    source_url       = Column(String)
    language         = Column(String, default="en")
    story_hash       = Column(String, index=True)
    category         = Column(String, default="General")
    importance_score = Column(Float, default=5.0)
    include          = Column(Boolean, default=True)
    why_important    = Column(Text, default="")
    tags             = Column(JSON, default=list)
    target_exams     = Column(JSON, default=list)
    quick_json       = Column(JSON, nullable=True)
    deep_json        = Column(JSON, nullable=True)
    mcqs_json        = Column(JSON, default=list)
    published_at     = Column(DateTime, default=datetime.datetime.utcnow)
    fetched_at       = Column(DateTime, default=datetime.datetime.utcnow)


class ReadLog(Base):
    __tablename__ = "read_logs"
    id         = Column(String, primary_key=True, default=new_id)
    user_id    = Column(String)
    article_id = Column(String)
    exam_type  = Column(String)
    read_at    = Column(DateTime, default=datetime.datetime.utcnow)


class RevisionSchedule(Base):
    __tablename__ = "revision_schedules"
    id          = Column(String, primary_key=True, default=new_id)
    user_id     = Column(String)
    article_id  = Column(String)
    due_at      = Column(DateTime)
    day_number  = Column(Integer, default=2)
    completed   = Column(Boolean, default=False)
    score_pct   = Column(Float, nullable=True)
    created_at  = Column(DateTime, default=datetime.datetime.utcnow)


# ── Weekly Test ────────────────────────────────────────────────────────────────
class WeeklyTest(Base):
    __tablename__ = "weekly_tests"
    id         = Column(String, primary_key=True, default=new_id)
    week_label = Column(String, index=True)
    questions  = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class WeeklyTestAttempt(Base):
    __tablename__ = "weekly_test_attempts"
    id           = Column(String, primary_key=True, default=new_id)
    user_id      = Column(String, index=True)
    test_id      = Column(String)
    week_label   = Column(String)
    score_pct    = Column(Float)
    correct      = Column(Integer)
    total        = Column(Integer)
    answers      = Column(JSON, default=list)
    attempted_at = Column(DateTime, default=datetime.datetime.utcnow)


# ── Monthly Mock Test ──────────────────────────────────────────────────────────
class MockTest(Base):
    __tablename__ = "mock_tests"
    id           = Column(String, primary_key=True, default=new_id)
    month_label  = Column(String, index=True)
    exam_type    = Column(String, default="UPSC")
    questions    = Column(JSON, default=list)
    created_at   = Column(DateTime, default=datetime.datetime.utcnow)

class MockTestAttempt(Base):
    __tablename__ = "mock_test_attempts"
    id           = Column(String, primary_key=True, default=new_id)
    user_id      = Column(String, index=True)
    test_id      = Column(String)
    month_label  = Column(String)
    exam_type    = Column(String)
    score_pct    = Column(Float)
    correct      = Column(Integer)
    total        = Column(Integer)
    time_taken   = Column(Integer, default=0)
    answers      = Column(JSON, default=list)
    attempted_at = Column(DateTime, default=datetime.datetime.utcnow)


# ── PYQ Matcher ────────────────────────────────────────────────────────────────
class PYQ(Base):
    __tablename__ = "pyqs"
    id          = Column(String, primary_key=True, default=new_id)
    exam        = Column(String)
    year        = Column(Integer)
    paper       = Column(String)
    question    = Column(String)
    options     = Column(JSON, default=list)
    answer      = Column(String)
    explanation = Column(Text, default="")
    category    = Column(String)
    keywords    = Column(JSON, default=list)


def _add_col(conn, table, col, defn):
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    if col not in {r[1] for r in rows}:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {defn}"))

def _migrate():
    with engine.connect() as conn:
        _add_col(conn, "articles", "language",   "VARCHAR DEFAULT 'en'")
        _add_col(conn, "articles", "story_hash", "VARCHAR")
        _add_col(conn, "users",    "email",         "VARCHAR")
        _add_col(conn, "users",    "password_hash", "VARCHAR")
        _add_col(conn, "users",    "xp_points",     "INTEGER DEFAULT 0")
        conn.commit()

def init_db():
    Base.metadata.create_all(bind=engine)
    _migrate()
