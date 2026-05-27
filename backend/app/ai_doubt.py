"""AI Doubt Solver — answers student questions per article. Claude → OpenAI → rule-based."""
import os
from .database import Article

OPENAI_KEY    = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")

RULE_ANSWERS = {
    "mpc":        "The Monetary Policy Committee (MPC) is a 6-member statutory body under the RBI Act. It sets the policy repo rate by majority vote. Members: RBI Governor (chair), 2 RBI officials, 3 external experts appointed by the government.",
    "repo rate":  "Repo rate is the rate at which RBI lends money to commercial banks. When RBI cuts it, banks get cheaper funds → lower loan rates → EMIs fall → more spending → economic growth.",
    "gdp":        "GDP measures the total monetary value of all goods and services produced in a country in a year. India uses constant prices (base year 2011-12) for real growth calculations.",
    "inflation":  "Inflation is a sustained rise in the general price level. Measured by CPI in India. RBI targets 4% CPI (±2% band).",
    "article 21": "Article 21: 'No person shall be deprived of his life or personal liberty except according to procedure established by law.' Expanded to include: right to privacy, education, health, livelihood.",
    "cepa":       "CEPA (Comprehensive Economic Partnership Agreement) is a broad trade deal covering goods, services, investment, and IP. India has CEPAs with UAE (2022), Japan, South Korea, Singapore.",
    "brics":      "BRICS: Brazil, Russia, India, China, South Africa. Formed 2006. Now expanded. Represents ~40% of world population.",
    "isro":       "ISRO (Indian Space Research Organisation) established 1969. HQ: Bengaluru. Key missions: Chandrayaan, Mangalyaan, Gaganyaan. PSLV is workhorse rocket.",
    "wipo":       "WIPO (World Intellectual Property Organization) is a UN agency in Geneva. Publishes the Global Innovation Index (GII) annually.",
    "cop":        "COP (Conference of Parties) is the annual UN climate summit under UNFCCC. COP28 in Dubai (2023). India committed to net-zero by 2070.",
}

async def _openai_answer(question, context):
    import httpx
    prompt = f"""You are an expert UPSC/SSC exam tutor. Article context:\n{context[:1500]}\n\nStudent question: {question}\n\nAnswer in 3-5 sentences, plain text, exam-relevant facts only."""
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization":f"Bearer {OPENAI_KEY}"},
            json={"model":"gpt-4o-mini","messages":[{"role":"user","content":prompt}],"temperature":0.4,"max_tokens":300})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()

async def _anthropic_answer(question, context):
    import httpx
    prompt = f"""You are an expert UPSC/SSC exam tutor. Article context:\n{context[:1500]}\n\nStudent question: {question}\n\nAnswer in 3-5 sentences, plain text, exam-relevant facts only."""
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key":ANTHROPIC_KEY,"anthropic-version":"2023-06-01","content-type":"application/json"},
            json={"model":"claude-haiku-4-5-20251001","max_tokens":300,"messages":[{"role":"user","content":prompt}]})
        r.raise_for_status()
        return r.json()["content"][0]["text"].strip()

def _rule_based(question, article):
    q = question.lower()
    for key,ans in RULE_ANSWERS.items():
        if key in q: return ans
    cat  = article.category if article else "this topic"
    tags = ", ".join((article.tags or [])[:4]) if article else ""
    return (f"This question relates to {cat}. Key concepts: {tags or 'refer to the article'}. "
            f"For exams, focus on: key entities, important numbers/dates, policy/constitutional relevance. "
            f"Relevant for: {', '.join((article.target_exams or ['UPSC','SSC'])[:3]) if article else 'UPSC/SSC'}.")

async def answer_doubt(article_id, question, db):
    art = db.query(Article).filter(Article.id==article_id).first()
    context = ""
    if art:
        quick = art.quick_json or {}
        context = f"Title: {art.title}\nCategory: {art.category}\nWhy important: {art.why_important}\nKey facts: {'; '.join(quick.get('key_facts',[]))}\nBackground: {quick.get('background','')}\nKeywords: {', '.join(art.tags or [])}"
    answer, source = None, "rule-based"
    if ANTHROPIC_KEY:
        try: answer=await _anthropic_answer(question,context); source="Claude AI"
        except Exception as e: print(f"[DOUBT] Anthropic: {e}")
    if not answer and OPENAI_KEY:
        try: answer=await _openai_answer(question,context); source="GPT-4o mini"
        except Exception as e: print(f"[DOUBT] OpenAI: {e}")
    if not answer:
        answer=_rule_based(question,art); source="rule-based"
    return {"question":question,"answer":answer,"source":source,"article_id":article_id,
            "category":art.category if art else "General",
            "exam_tip":f"Exam tip: This relates to {art.category if art else 'current affairs'} — high priority for {', '.join((art.target_exams or ['UPSC'])[:2]) if art else 'UPSC/SSC'}."}
