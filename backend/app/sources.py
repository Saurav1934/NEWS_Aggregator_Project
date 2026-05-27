"""
News RSS sources — priority order for Indian government exam current affairs.
Higher priority = fetched first and wins cross-source deduplication.
"""

# priority: 10 = must-have, 7–9 = high/medium, 5–6 = optional (Hindi/regional)
NEWS_SOURCES = [
    # ── High priority — English (UPSC, State PSC, Banking) ─────────────────────
    {"name": "The Hindu",        "url": "https://www.thehindu.com/feeder/default.rss",                      "language": "en", "priority": 10, "boost": 1.0},
    {"name": "Indian Express",   "url": "https://indianexpress.com/feed/",                                   "language": "en", "priority": 10, "boost": 1.0},
    {"name": "PIB",              "url": "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3",           "language": "en", "priority": 10, "boost": 0.9},
    {"name": "PRS India",        "url": "https://www.prsindia.org/rss/rss-feed",                            "language": "en", "priority": 10, "boost": 0.9},
    {"name": "Economic Times",   "url": "https://economictimes.indiatimes.com/rssfeedsdefault.cms",         "language": "en", "priority": 9,  "boost": 0.8},
    {"name": "RBI",              "url": "https://www.rbi.org.in/scripts/rss.aspx?Id=1",                    "language": "en", "priority": 9,  "boost": 0.8},
    # ── Medium priority — English general + economy ────────────────────────────
    {"name": "Hindustan Times",  "url": "https://www.hindustantimes.com/feeds/rss/latest/rssfeed.xml",     "language": "en", "priority": 8,  "boost": 0.5},
    {"name": "Business Standard","url": "https://www.business-standard.com/rss/home_page_top_stories.rss","language": "en", "priority": 8,  "boost": 0.6},
    {"name": "Times of India",   "url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",      "language": "en", "priority": 7,  "boost": 0.3},
    {"name": "The Telegraph",    "url": "https://www.telegraphindia.com/feeds/rss.jsp?id=3",               "language": "en", "priority": 7,  "boost": 0.4},
    {"name": "ISRO",             "url": "https://www.isro.gov.in/rss",                                     "language": "en", "priority": 8,  "boost": 0.7},
    {"name": "Down To Earth",    "url": "https://www.downtoearth.org.in/rss",                              "language": "en", "priority": 8,  "boost": 0.5},
    {"name": "UN News",          "url": "https://news.un.org/feed/subscribe/en/news/all/rss.xml",          "language": "en", "priority": 7,  "boost": 0.5},
    {"name": "World Bank",       "url": "https://feeds.worldbank.org/worldbank/blogs/all",                 "language": "en", "priority": 7,  "boost": 0.5},
    # ── Lower priority — Hindi (SSC, State PSC, Hindi medium) ──────────────────
    {"name": "Dainik Bhaskar",   "url": "https://www.bhaskar.com/rss",                                     "language": "hi", "priority": 6,  "boost": 0.2},
    {"name": "Amar Ujala",       "url": "https://www.amarujala.com/rss/breaking-news.xml",                 "language": "hi", "priority": 5,  "boost": 0.2},
]

SOURCE_NAMES = {s["name"] for s in NEWS_SOURCES}


def sorted_sources(min_priority: int = 5) -> list[dict]:
    """Sources highest-priority first (for ingest order + dedup winner)."""
    return sorted(
        [s for s in NEWS_SOURCES if s["priority"] >= min_priority],
        key=lambda s: (-s["priority"], s["name"]),
    )


def entries_limit(priority: int) -> int:
    if priority >= 10: return 20
    if priority >= 8:  return 15
    return 10
