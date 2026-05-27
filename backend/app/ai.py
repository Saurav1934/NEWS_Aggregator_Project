"""
AI layer — rule-based by default, OpenAI if OPENAI_API_KEY is set.
"""
import os, re, json, hashlib

OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")

# ── keyword scoring ────────────────────────────────────────────────────────────
EXAM_KEYWORDS = {
    "Economy":               ["rbi","repo rate","gdp","inflation","budget","fiscal","gst","sebi","sensex","nifty","fdi","fii","forex","trade deficit","cpi","wpi","monetary","credit","banking","nbfc","msme","npa","rupee"],
    "Polity":                ["supreme court","high court","parliament","constitution","amendment","president","governor","election","eci","bill","act","lok sabha","rajya sabha","fundamental","directive principle","article","upsc","ias","ips","tribunal"],
    "International Relations":["india-","summit","bilateral","treaty","un ","imf","world bank","g20","g7","brics","sco","asean","nato","foreign minister","mea","diplomatic","sanction","trade deal","cepa","fta"],
    "Science & Technology":  ["isro","nasa","satellite","launch","mission","ai ","artificial intelligence","quantum","semiconductor","5g","drone","space","rocket","chandrayaan","gaganyaan","nuclear","research","patent"],
    "Environment":           ["climate","carbon","emission","biodiversity","cop","ipcc","forest","pollution","renewable","solar","wind energy","glacier","wetland","tiger","wildlife","deforestation","paris agreement","net zero"],
    "Government Schemes":    ["yojana","scheme","mission","programme","launch","pm ","minister","ministry","crore","lakh","beneficiar","portal","digital india","make in india","startup india","mudra","jan dhan"],
    "Reports & Indexes":     ["index","rank","report","survey","data","statistic","global","world ","position","score","released","published","wipo","wef","transparency"],
    "Defence":               ["army","navy","air force","defence","military","weapon","exercise","drdo","missile","fighter","frigate","submarine","border","lac","loc","security"],
    "Sports":                ["gold","silver","bronze","medal","olympic","championship","world cup","tournament","cricket","hockey","badminton","chess","athlete","player"],
    "Awards":                ["award","prize","honour","bharat ratna","padma","nobel","oscar","fellowship","recognition"],
}

EXAM_BLOCKLIST = ["celebrity","bollywood","film release","box office","fashion","lifestyle","recipe","horoscope","match score"]

# Extra keyword hits for Hindi-medium exam relevance
HINDI_EXAM_KEYWORDS = [
    "सरकार", "योजना", "मंत्री", "राज्य", "चुनाव", "अदालत", "संविधान",
    "अर्थव्यवस्था", "बजट", "रिजर्व बैंक", "परीक्षा", "SSC", "UPSC",
]

EXAM_MAP = {
    "Economy":               ["UPSC","SSC","Banking","Railway"],
    "Polity":                ["UPSC","State PSC","SSC"],
    "International Relations":["UPSC","State PSC"],
    "Science & Technology":  ["UPSC","SSC","Railway","Defence"],
    "Environment":           ["UPSC","State PSC","SSC"],
    "Government Schemes":    ["UPSC","SSC","Banking","Railway","State PSC","Defence"],
    "Reports & Indexes":     ["UPSC","SSC","Banking"],
    "Defence":               ["UPSC","Defence","SSC"],
    "Sports":                ["SSC","Railway","Banking","Defence"],
    "Awards":                ["SSC","Railway","Banking"],
}


def _lower(text):
    return (text or "").lower()


def apply_source_boost(score: float, boost: float) -> float:
    return min(10.0, round(score + boost, 1))


def classify(title, content="", language="en"):
    body = _lower(title + " " + content)

    # Blocklist check
    for bad in EXAM_BLOCKLIST:
        if bad in body:
            return "Entertainment", 1.0, False, ["Not exam-relevant"]

    scores = {}
    for cat, kws in EXAM_KEYWORDS.items():
        hit = sum(1 for k in kws if k in body)
        if hit:
            scores[cat] = hit

    if not scores and language == "hi":
        hi_hits = sum(1 for k in HINDI_EXAM_KEYWORDS if k in (title + " " + content))
        if hi_hits:
            return "General", min(10.0, 5.0 + hi_hits * 0.5), True, ["Hindi source — SSC/State PSC relevant"]

    if not scores:
        return "General", 3.0, False, ["No clear exam relevance found"]

    best_cat = max(scores, key=scores.get)
    hit_count = scores[best_cat]
    importance = min(10.0, 4.0 + hit_count * 1.2)
    include = importance >= 5.5

    tags = [k for k in EXAM_KEYWORDS.get(best_cat, []) if k in body][:6]
    return best_cat, round(importance, 1), include, tags


def quick_summary(title, category, language="en"):
    facts = {
        "Economy":               [f"Related to economic policy and financial governance","Check ministry and key numbers","Note the percentage or amount mentioned","Link to RBI/SEBI/Finance Ministry","Relevant for Banking and SSC exams"],
        "Polity":                [f"Constitutional dimension — check relevant Article","Note the court/body involved","Understand the judgment/amendment","Relevant for UPSC GS2 and State PSC","Precedent impact on governance"],
        "International Relations":[f"Note the two countries/blocs involved","Identify the agreement/summit/treaty","Check India's strategic interest","Link to India's foreign policy goals","Relevant for UPSC GS2"],
        "Science & Technology":  [f"Note the agency (ISRO/DRDO/NASA)","Identify the technology/mission name","Check first-of-its-kind claim","Relevance to India's S&T goals","Good for SSC, Railway, UPSC GS3"],
        "Environment":           [f"Note the international convention if any","Check species/ecosystem involved","Government response and policy","India's climate commitment","UPSC GS3 Environment paper"],
        "Government Schemes":    [f"Ministry that launched the scheme","Target beneficiaries","Budget allocation if mentioned","Portal/digital component","Very high probability exam question"],
    }
    bullets = facts.get(category, [f"Exam-relevant development in {category}","Note the key entities involved","Check the figures and dates","Understand the policy implication","Review related previous year questions"])
    if language == "hi":
        bullets = bullets + ["Original in Hindi — revise key terms in English for prelims"]
    return {
        "why_in_news": f"{title} — important development in {category}." + (
            " (Hindi source — translate key terms for exam notes.)" if language == "hi" else ""
        ),
        "key_facts": bullets,
        "background": f"This topic falls under {category} which is a recurring theme in government exams.",
        "exam_relevance": f"{category} — {', '.join(EXAM_MAP.get(category, ['UPSC','SSC']))}"
            + (" | Hindi medium: SSC, State PSC" if language == "hi" else ""),
        "keywords": [category.lower(), "current affairs", "government exam"]
            + (["hindi", "translation"] if language == "hi" else []),
        "revision_notes": f"{category}: {title[:80]}",
    }


def deep_summary(title, category, language="en"):
    qs = quick_summary(title, category, language)
    qs["background"] = (
        f"This development in {category} has constitutional, administrative, or policy implications "
        f"relevant to UPSC GS papers. Analyse the cause-effect chain and any related reports or acts."
    )
    qs["exam_relevance"] = f"UPSC Mains — {category} | GS Paper mapping: {'GS2' if category=='Polity' else 'GS3' if category in ('Economy','Environment','Science & Technology') else 'GS2/GS3'}"
    qs["keywords"] = qs["keywords"] + ["mains perspective","policy analysis","constitutional relevance"]
    qs["revision_notes"] = qs["revision_notes"] + " | Analyse: causes → government response → impact → way forward"
    return qs


def make_mcq(title, category):
    templates = {
        "Economy":               ("Which institution is associated with monetary policy in India?", ["Reserve Bank of India","SEBI","NITI Aayog","Finance Ministry"], "Reserve Bank of India"),
        "Polity":                ("The Supreme Court of India derives its original jurisdiction from which Article?","Article 131;Article 226;Article 32;Article 136".split(";"),"Article 131"),
        "International Relations":("Which ministry handles India's foreign policy?",["Ministry of External Affairs","Ministry of Home Affairs","Ministry of Defence","Ministry of Commerce"],"Ministry of External Affairs"),
        "Science & Technology":  ("ISRO stands for?",["Indian Space Research Organisation","Indian Science Research Organisation","Indian Solar Research Office","International Space Research Organisation"],"Indian Space Research Organisation"),
        "Environment":           ("The Paris Agreement is related to?",["Climate change","Nuclear disarmament","Trade barriers","Biodiversity"],"Climate change"),
        "Government Schemes":    ("Which ministry typically launches rural livelihood schemes in India?",["Ministry of Rural Development","Ministry of Finance","Ministry of Labour","NITI Aayog"],"Ministry of Rural Development"),
        "Defence":               ("DRDO stands for?",["Defence Research and Development Organisation","Department of Research and Defence Operations","Directorate of Research and Defence Output","Defence Radar and Detection Organisation"],"Defence Research and Development Organisation"),
        "Reports & Indexes":     ("The Global Innovation Index is published by?",["WIPO","World Bank","IMF","UNDP"],"WIPO"),
        "Sports":                ("Which body governs cricket in India?",["BCCI","IOA","SAI","NSF"],"BCCI"),
        "Awards":                ("The Bharat Ratna is awarded by?",["President of India","Prime Minister","Supreme Court","Parliament"],"President of India"),
    }
    q, opts, ans = templates.get(category, (f"This development is most relevant for which exam?", ["UPSC","SSC","Banking","Railway"], "UPSC"))
    return [{"question": q, "options": opts, "answer": ans, "explanation": f"Related to the article: {title[:60]}"}]


# ── OpenAI path (optional) ─────────────────────────────────────────────────────
async def ai_filter_and_summarise(
    title,
    content,
    source_name,
    language="en",
    source_boost=0.0,
    source_priority=5,
):
    """Try OpenAI; fall back to rule-based."""
    if OPENAI_KEY:
        try:
            result = await _openai_analyse(title, content, source_name, language, source_boost)
            return result
        except Exception as e:
            print(f"[AI] OpenAI failed ({e}), using rule-based fallback")

    cat, score, include, tags = classify(title, content, language)
    score = apply_source_boost(score, source_boost)
    if source_priority >= 10 and include:
        include = True
    elif source_priority <= 6 and score < 6.5:
        include = False

    lang_note = " Hindi source — useful for SSC/State PSC; translate key facts." if language == "hi" else ""
    why = f"Classified as {cat} ({score}/10) from {source_name}.{lang_note}"
    target = list(EXAM_MAP.get(cat, ["UPSC", "SSC"]))
    if language == "hi" and "State PSC" not in target:
        target.append("State PSC")

    return {
        "category": cat,
        "importance_score": score,
        "include": include,
        "why_important": why,
        "tags": tags,
        "target_exams": target,
        "quick": quick_summary(title, cat, language),
        "deep": deep_summary(title, cat, language),
        "mcqs": make_mcq(title, cat),
    }


async def _openai_analyse(title, content, source_name, language="en", source_boost=0.0):
    import httpx
    lang_instruction = (
        "Article is in Hindi. Translate key facts into English in summaries. "
        "Mark target_exams with SSC and State PSC where relevant."
        if language == "hi"
        else "Article is in English."
    )
    boost_note = (
        f"Source '{source_name}' is high-trust — lean toward include=true if borderline. "
        f"Add up to {source_boost} to importance_score (max 10)."
        if source_boost >= 0.8
        else f"Source priority boost: +{source_boost} to importance_score (max 10)."
    )
    prompt = f"""You are an expert government exam mentor for UPSC, SSC, Banking, Railway and State PSC exams in India.

Analyse this news article and return ONLY valid JSON (no markdown, no explanation).

Title: {title}
Source: {source_name}
Language: {language}
{lang_instruction}
{boost_note}
Content: {content[:1200]}

Return this exact JSON structure:
{{
  "category": "one of: Polity|Economy|International Relations|Science & Technology|Environment|Geography|Government Schemes|Reports & Indexes|Awards|Sports|Defence|History & Culture|Social Issues|Entertainment",
  "importance_score": <1-10 float>,
  "include": <true if importance>=6 and exam-relevant, else false>,
  "why_important": "<one sentence>",
  "tags": ["tag1","tag2","tag3"],
  "target_exams": ["UPSC","SSC","Banking","Railway","State PSC","Defence"],
  "quick": {{
    "why_in_news": "<1-2 sentences>",
    "key_facts": ["fact1","fact2","fact3","fact4","fact5"],
    "background": "<2 sentences>",
    "exam_relevance": "<paper/subject>",
    "keywords": ["kw1","kw2","kw3"],
    "revision_notes": "<one-liner memory hook>"
  }},
  "deep": {{
    "why_in_news": "<2-3 sentences>",
    "key_facts": ["fact1","fact2","fact3","fact4","fact5"],
    "background": "<3 sentences with constitutional/policy context>",
    "exam_relevance": "<UPSC GS paper + mains angle>",
    "keywords": ["kw1","kw2","kw3","kw4","kw5"],
    "revision_notes": "<analytical one-liner>"
  }},
  "mcqs": [{{
    "question": "<question>",
    "options": ["A","B","C","D"],
    "answer": "<correct option text>",
    "explanation": "<short explanation>"
  }}]
}}"""

    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"},
            json={"model":"gpt-4o-mini","messages":[{"role":"user","content":prompt}],"temperature":0.3,"max_tokens":1200}
        )
        r.raise_for_status()
        raw = r.json()["choices"][0]["message"]["content"]
        raw = re.sub(r"```json|```","",raw).strip()
        data = json.loads(raw)
        if "importance_score" in data:
            data["importance_score"] = apply_source_boost(
                float(data["importance_score"]), source_boost
            )
        return data
