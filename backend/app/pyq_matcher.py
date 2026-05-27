"""PYQ Matcher — links today's articles to past UPSC/SSC questions."""
import re
from sqlalchemy.orm import Session
from .database import Article, PYQ, new_id

SEED_PYQS = [
    {"exam":"UPSC","year":2023,"paper":"Prelims GS1","question":"With reference to the Monetary Policy Committee (MPC), which statement is correct?\n1. It is a statutory body.\n2. It decides the Cash Reserve Ratio.","options":["1 only","2 only","Both 1 and 2","Neither 1 nor 2"],"answer":"1 only","explanation":"MPC is statutory under RBI Act. CRR is decided by RBI Governor, not MPC.","category":"Economy","keywords":["monetary policy","mpc","rbi","repo rate","crr"]},
    {"exam":"UPSC","year":2022,"paper":"Prelims GS1","question":"'Right to Privacy' is protected under which Article?","options":["Article 15","Article 19","Article 21","Article 29"],"answer":"Article 21","explanation":"Puttaswamy v. UoI (2017) — privacy is part of Art 21.","category":"Polity","keywords":["right to privacy","article 21","fundamental right","puttaswamy"]},
    {"exam":"UPSC","year":2023,"paper":"Prelims GS3","question":"Objective of 'National Hydrogen Mission'?","options":["Hydrogen as fuel for vehicles only","Make India a global hub for green hydrogen","Replace LPG with hydrogen in households","Use hydrogen in nuclear reactors"],"answer":"Make India a global hub for green hydrogen","explanation":"NHM 2021 aims to make India a global hub for green hydrogen production and export.","category":"Environment","keywords":["hydrogen","green hydrogen","national hydrogen mission","renewable"]},
    {"exam":"UPSC","year":2022,"paper":"Prelims GS2","question":"Which is NOT a member of BRICS?","options":["Brazil","Russia","Indonesia","South Africa"],"answer":"Indonesia","explanation":"BRICS: Brazil, Russia, India, China, South Africa. Indonesia is not a member.","category":"International Relations","keywords":["brics","brazil","russia","china","south africa"]},
    {"exam":"UPSC","year":2023,"paper":"Prelims GS3","question":"Chandrayaan-3 landed on which region of the Moon?","options":["North Pole","Equatorial region","South Polar region","Far side"],"answer":"South Polar region","explanation":"Chandrayaan-3 landed near the lunar south pole on 23 August 2023.","category":"Science & Technology","keywords":["chandrayaan","isro","moon","lunar","south pole","space"]},
    {"exam":"UPSC","year":2021,"paper":"Prelims GS2","question":"PM Jan Dhan Yojana was launched primarily to?","options":["Provide loans to farmers","Ensure financial inclusion","Provide subsidised food","Provide free healthcare"],"answer":"Ensure financial inclusion","explanation":"PMJDY 2014 aims at financial inclusion — basic banking for all.","category":"Government Schemes","keywords":["jan dhan","financial inclusion","bank account","pmjdy"]},
    {"exam":"SSC","year":2023,"paper":"CGL Tier 1","question":"Which country tops the Global Innovation Index 2023?","options":["USA","Germany","Switzerland","Japan"],"answer":"Switzerland","explanation":"Switzerland topped GII 2023 published by WIPO.","category":"Reports & Indexes","keywords":["global innovation index","gii","wipo","innovation","rank"]},
    {"exam":"Banking","year":2023,"paper":"IBPS PO","question":"MPC of RBI consists of how many members?","options":["4","5","6","7"],"answer":"6","explanation":"MPC has 6 members — 3 from RBI + 3 external.","category":"Economy","keywords":["mpc","rbi","monetary policy","members","governor"]},
    {"exam":"UPSC","year":2023,"paper":"Prelims GS3","question":"PM Surya Ghar Muft Bijli Yojana targets how many households?","options":["50 lakh","75 lakh","1 crore","2 crore"],"answer":"1 crore","explanation":"PM Surya Ghar: 1 crore target, Ministry of New and Renewable Energy.","category":"Government Schemes","keywords":["surya ghar","solar","rooftop","mnre","bijli yojana"]},
    {"exam":"UPSC","year":2022,"paper":"Prelims GS2","question":"India-UAE CEPA came into effect in which year?","options":["2020","2021","2022","2023"],"answer":"2022","explanation":"India-UAE CEPA signed Feb 2022, in force May 2022.","category":"International Relations","keywords":["cepa","uae","trade","agreement","bilateral"]},
    {"exam":"UPSC","year":2023,"paper":"Prelims GS3","question":"Which of the following is correct about COP28?\n1. Held in Dubai.\n2. Loss and Damage Fund was operationalised.","options":["1 only","2 only","Both 1 and 2","Neither"],"answer":"Both 1 and 2","explanation":"COP28 in Dubai (UAE) 2023; Loss and Damage Fund operationalised.","category":"Environment","keywords":["cop28","climate","dubai","loss and damage","unfccc","paris"]},
    {"exam":"SSC","year":2022,"paper":"CGL Tier 1","question":"India's GDP growth rate for FY2022-23?","options":["6.5%","7.0%","7.5%","8.0%"],"answer":"7.0%","explanation":"India's GDP estimated at 7.0% for FY23.","category":"Economy","keywords":["gdp","growth rate","economy","fiscal","fy23"]},
]

def seed_pyqs(db):
    if db.query(PYQ).count() > 0: return
    for p in SEED_PYQS:
        db.add(PYQ(id=new_id(),exam=p["exam"],year=p["year"],paper=p["paper"],question=p["question"],
            options=p["options"],answer=p["answer"],explanation=p["explanation"],category=p["category"],keywords=p["keywords"]))
    db.commit()

def _overlap(kws, text):
    t = text.lower()
    return sum(1 for k in kws if k.lower() in t)

def match_pyqs(article_id, db, limit=5):
    art = db.query(Article).filter(Article.id==article_id).first()
    if not art: return []
    search = f"{art.title} {art.category} {' '.join(art.tags or [])}"
    scored = []
    for pyq in db.query(PYQ).all():
        s = _overlap(pyq.keywords or [], search)
        if art.category == pyq.category: s += 2
        if s > 0: scored.append((s, pyq))
    scored.sort(key=lambda x: -x[0])
    return [{"pyq_id":p.id,"exam":p.exam,"year":p.year,"paper":p.paper,"question":p.question,"options":p.options,
             "answer":p.answer,"explanation":p.explanation,"category":p.category,"relevance":s,
             "match_note":f"Matched on {s} keyword(s) — {p.exam} {p.year}"} for s,p in scored[:limit]]

def search_pyqs(query, db, exam=None, limit=10):
    q = db.query(PYQ)
    if exam: q = q.filter(PYQ.exam==exam)
    scored = [(p, _overlap(query.lower().split(), p.question.lower()+" "+" ".join(p.keywords or []))) for p in q.all()]
    scored = sorted([(p,s) for p,s in scored if s>0], key=lambda x:-x[1])
    return [{"pyq_id":p.id,"exam":p.exam,"year":p.year,"paper":p.paper,"question":p.question,
             "options":p.options,"answer":p.answer,"explanation":p.explanation,"category":p.category} for p,_ in scored[:limit]]
