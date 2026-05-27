"""
RSS ingestion: fetches, deduplicates, AI-scores, and saves articles.
"""
import asyncio
import datetime
import hashlib
import os
import re

import feedparser
import httpx
from sqlalchemy.orm import Session

from .ai import ai_filter_and_summarise
from .database import Article, SessionLocal
from .sources import entries_limit, sorted_sources


FEED_CONCURRENCY = int(os.getenv("INGEST_FEED_CONCURRENCY", "6"))
AI_CONCURRENCY = int(os.getenv("INGEST_AI_CONCURRENCY", "5"))
FEED_TIMEOUT_SECONDS = float(os.getenv("INGEST_FEED_TIMEOUT_SECONDS", "10"))

_ingest_lock = None
_last_status = {
    "status": "idle",
    "new": 0,
    "errors": [],
    "sources": 0,
    "started_at": None,
    "finished_at": None,
}


# Fallback demo articles when all feeds fail (network restricted env)
SEED_ARTICLES = [
    {
        "title": "RBI cuts repo rate by 25 bps to 6.25% - first cut since 2020",
        "source_name": "RBI",
        "source_url": "https://rbi.org.in",
        "content": "The Reserve Bank of India Monetary Policy Committee reduced the repo rate by 25 basis points to 6.25 percent. This is the first rate cut since May 2020. The MPC cited easing inflation and need to support economic growth. CRR remains 4 percent. GDP forecast for FY26 is 6.8 percent.",
    },
    {
        "title": "India ranks 63rd in Global Innovation Index 2025 - highest ever ranking",
        "source_name": "WIPO",
        "source_url": "https://wipo.int",
        "content": "India has achieved its best-ever ranking of 63rd in the Global Innovation Index 2025 published by WIPO. Switzerland tops the list. India is first among central and southern Asia. The index ranks 132 economies on innovation inputs and outputs.",
    },
    {
        "title": "Supreme Court upholds Right to Privacy in digital data case under Article 21",
        "source_name": "Supreme Court of India",
        "source_url": "https://main.sci.gov.in",
        "content": "The Supreme Court of India reaffirmed that Right to Privacy is a fundamental right under Article 21 of the Constitution. The ruling came in a case challenging data collection practices. The court cited the Puttaswamy judgment of 2017. This reinforces constitutional backing of the DPDP Act 2023.",
    },
    {
        "title": "India UAE CEPA extended - trade target revised to USD 100 billion by 2030",
        "source_name": "Ministry of External Affairs",
        "source_url": "https://mea.gov.in",
        "content": "India and UAE signed an extension of the Comprehensive Economic Partnership Agreement. The bilateral trade target has been revised to 100 billion USD by 2030. UAE is India's third-largest trade partner. The deal covers goods, services, and investments. I2U2 framework was also discussed.",
    },
    {
        "title": "PM Surya Ghar Muft Bijli Yojana targets 1 crore rooftop solar homes",
        "source_name": "PIB",
        "source_url": "https://pib.gov.in",
        "content": "The government launched PM Surya Ghar Muft Bijli Yojana to install rooftop solar on 1 crore households. Eligible families will receive 300 units of free electricity per month. The scheme is administered by Ministry of New and Renewable Energy with a budget of Rs 75000 crore. Net metering allows surplus to be sold back to grid.",
    },
    {
        "title": "India joins IPEF Supply Chain Agreement - boosts resilience with Indo-Pacific partners",
        "source_name": "MEA",
        "source_url": "https://mea.gov.in",
        "content": "India formally ratified the Indo-Pacific Economic Framework Supply Chain Agreement. The IPEF includes 14 member countries. The agreement aims to reduce dependence on single-source supply chains. India sees strategic benefits in semiconductors and critical minerals.",
    },
    {
        "title": "ISRO successfully tests Gaganyaan crew escape system at Sriharikota",
        "source_name": "ISRO",
        "source_url": "https://isro.gov.in",
        "content": "ISRO conducted a successful test of the crew escape system for the Gaganyaan human spaceflight mission at SDSC SHAR Sriharikota. The system is designed to pull astronauts to safety in case of launch emergency. Gaganyaan aims to send Indian astronauts to space by 2025.",
    },
    {
        "title": "COP29 agrees on $300 billion annual climate finance for developing nations",
        "source_name": "UNFCCC",
        "source_url": "https://unfccc.int",
        "content": "Parties at COP29 agreed on a new climate finance goal of 300 billion USD annually for developing nations by 2035. India and several nations pushed for higher ambition. The deal builds on the Paris Agreement. Loss and damage fund was also discussed. India reaffirmed its 2070 net-zero target.",
    },
]

_TITLE_NOISE = re.compile(
    r"\b(live updates?|breaking|exclusive|watch|video|photos?|read|full story)\b",
    re.I,
)


def _normalize_title(title: str) -> str:
    t = (title or "").lower()
    t = _TITLE_NOISE.sub("", t)
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:200]


def _story_hash(title: str) -> str:
    """Cross-source dedup: same headline from Hindu + Express becomes one story."""
    norm = _normalize_title(title)
    if len(norm) < 12:
        norm = (title or "").lower().strip()
    return hashlib.md5(norm.encode()).hexdigest()[:12]


def _article_id(title: str, source: str) -> str:
    return hashlib.md5(f"{source}::{title}".lower().encode()).hexdigest()[:12]


def _detect_language(text: str, feed_language: str) -> str:
    if re.search(r"[\u0900-\u097F]", text or ""):
        return "hi"
    return feed_language or "en"


def _get_ingest_lock():
    global _ingest_lock
    if _ingest_lock is None:
        _ingest_lock = asyncio.Lock()
    return _ingest_lock


def get_ingest_status() -> dict:
    return dict(_last_status)


async def _fetch_source(source_cfg: dict, client: httpx.AsyncClient, semaphore: asyncio.Semaphore):
    async with semaphore:
        try:
            response = await client.get(source_cfg["url"])
            response.raise_for_status()
            parsed = await asyncio.to_thread(feedparser.parse, response.content)
            limit = entries_limit(source_cfg["priority"])
            return source_cfg, [dict(entry) for entry in parsed.entries[:limit]], None
        except Exception as e:
            return source_cfg, [], f"{source_cfg['name']}: {e}"


def _entry_candidate(entry: dict, source_cfg: dict):
    title = (entry.get("title") or "").strip()
    url = entry.get("link") or ""
    summary = entry.get("summary") or entry.get("description") or ""

    if not title or len(title) < 12:
        return None

    language = _detect_language(f"{title} {summary}", source_cfg.get("language", "en"))
    return {
        "id": _article_id(title, source_cfg["name"]),
        "title": title,
        "url": url,
        "summary": summary,
        "story_hash": _story_hash(title),
        "language": language,
        "source_cfg": source_cfg,
    }


async def _analyse_candidate(candidate: dict, semaphore: asyncio.Semaphore):
    source_cfg = candidate["source_cfg"]
    async with semaphore:
        result = await ai_filter_and_summarise(
            candidate["title"],
            candidate["summary"],
            source_cfg["name"],
            language=candidate["language"],
            source_boost=source_cfg.get("boost", 0),
            source_priority=source_cfg.get("priority", 5),
        )
    return candidate, result


def _save_article(candidate: dict, result: dict, db: Session) -> bool:
    if db.query(Article).filter(Article.id == candidate["id"]).first():
        return False
    if db.query(Article).filter(Article.story_hash == candidate["story_hash"]).first():
        return False

    source_cfg = candidate["source_cfg"]
    db.add(
        Article(
            id=candidate["id"],
            title=candidate["title"],
            source_name=source_cfg["name"],
            source_url=candidate["url"],
            language=candidate["language"],
            story_hash=candidate["story_hash"],
            category=result["category"],
            importance_score=result["importance_score"],
            include=result["include"],
            why_important=result["why_important"],
            tags=result.get("tags", []),
            target_exams=result.get("target_exams", []),
            quick_json=result.get("quick"),
            deep_json=result.get("deep"),
            mcqs_json=result.get("mcqs", []),
            published_at=datetime.datetime.utcnow(),
        )
    )
    return True


async def ingest_feeds():
    lock = _get_ingest_lock()
    if lock.locked():
        return {**get_ingest_status(), "status": "running", "skipped": True}

    async with lock:
        return await _run_ingest()


async def _run_ingest():
    sources = sorted_sources()
    started_at = datetime.datetime.utcnow().isoformat()
    _last_status.update(
        {
            "status": "running",
            "new": 0,
            "errors": [],
            "sources": len(sources),
            "started_at": started_at,
            "finished_at": None,
        }
    )

    db = SessionLocal()
    new_count = 0
    errors = []
    candidates = []

    try:
        feed_sem = asyncio.Semaphore(FEED_CONCURRENCY)
        timeout = httpx.Timeout(FEED_TIMEOUT_SECONDS)
        headers = {"User-Agent": "ExamMemoryAI/2.0 RSS ingester"}
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers) as client:
            feed_results = await asyncio.gather(
                *[_fetch_source(source_cfg, client, feed_sem) for source_cfg in sources]
            )
        entries_by_source = {cfg["name"]: entries for cfg, entries, _ in feed_results}
        errors.extend(error for _, _, error in feed_results if error)

        existing_story_hashes = {
            row[0] for row in db.query(Article.story_hash).filter(Article.story_hash != None).all()
        }
        existing_ids = {row[0] for row in db.query(Article.id).all()}
        seen_story_hashes = set(existing_story_hashes)
        seen_ids = set(existing_ids)

        # Preserve source priority for dedup winners while still fetching feeds in parallel.
        for source_cfg in sources:
            for entry in entries_by_source.get(source_cfg["name"], []):
                candidate = _entry_candidate(entry, source_cfg)
                if not candidate:
                    continue
                if candidate["story_hash"] in seen_story_hashes or candidate["id"] in seen_ids:
                    continue
                seen_story_hashes.add(candidate["story_hash"])
                seen_ids.add(candidate["id"])
                candidates.append(candidate)

        ai_sem = asyncio.Semaphore(AI_CONCURRENCY)
        analyse_tasks = [_analyse_candidate(candidate, ai_sem) for candidate in candidates]
        analysed = await asyncio.gather(*analyse_tasks, return_exceptions=True) if analyse_tasks else []

        for item in analysed:
            if isinstance(item, Exception):
                errors.append(f"AI: {item}")
                continue
            candidate, result = item
            if _save_article(candidate, result, db):
                new_count += 1
        db.commit()

        total = db.query(Article).count()
        if total == 0:
            print("[INGEST] No live feeds reachable - seeding demo articles")
            for seed in SEED_ARTICLES:
                result = await ai_filter_and_summarise(
                    seed["title"], seed["content"], seed["source_name"], language="en"
                )
                art_id = _article_id(seed["title"], seed["source_name"])
                story_key = _story_hash(seed["title"])
                if not db.query(Article).filter(Article.id == art_id).first():
                    db.add(
                        Article(
                            id=art_id,
                            title=seed["title"],
                            source_name=seed["source_name"],
                            source_url=seed["source_url"],
                            language="en",
                            story_hash=story_key,
                            category=result["category"],
                            importance_score=result["importance_score"],
                            include=result["include"],
                            why_important=result["why_important"],
                            tags=result.get("tags", []),
                            target_exams=result.get("target_exams", []),
                            quick_json=result.get("quick"),
                            deep_json=result.get("deep"),
                            mcqs_json=result.get("mcqs", []),
                        )
                    )
            db.commit()
            new_count = len(SEED_ARTICLES)

        _last_status.update(
            {
                "status": "idle",
                "new": new_count,
                "errors": errors,
                "sources": len(sources),
                "finished_at": datetime.datetime.utcnow().isoformat(),
            }
        )
        print(f"[INGEST] Done - {new_count} new articles. Errors: {errors or 'none'}")
        return {
            "new": new_count,
            "errors": errors,
            "sources": len(sources),
            "candidates": len(candidates),
        }
    except Exception as e:
        errors.append(f"ingest: {e}")
        _last_status.update(
            {
                "status": "failed",
                "new": new_count,
                "errors": errors,
                "sources": len(sources),
                "finished_at": datetime.datetime.utcnow().isoformat(),
            }
        )
        raise
    finally:
        db.close()
