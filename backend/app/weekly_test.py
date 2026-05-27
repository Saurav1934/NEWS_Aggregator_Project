"""Weekly Test — auto-generates a 25-question quiz every week from filtered articles."""
import datetime
from sqlalchemy.orm import Session
from .database import Article, WeeklyTest, WeeklyTestAttempt, new_id


def _week_label(dt=None):
    d = (dt or datetime.datetime.utcnow()).isocalendar()
    return f"{d[0]}-W{d[1]:02d}"


def _get_or_create(db, label):
    test = db.query(WeeklyTest).filter(WeeklyTest.week_label == label).first()
    return test or _build(db, label)


def _build(db, label):
    year, w = int(label.split("-W")[0]), int(label.split("-W")[1])
    week_start = datetime.datetime.fromisocalendar(year, w, 1)
    week_end   = week_start + datetime.timedelta(days=7)
    articles = (db.query(Article).filter(Article.include==True,
        Article.published_at>=week_start, Article.published_at<week_end)
        .order_by(Article.importance_score.desc()).limit(50).all())
    if len(articles) < 10:
        articles = db.query(Article).filter(Article.include==True).order_by(Article.importance_score.desc()).limit(50).all()
    questions, seen = [], set()
    for a in articles:
        for mcq in (a.mcqs_json or []):
            q = mcq.get("question","")
            if q in seen: continue
            seen.add(q)
            questions.append({"question":q,"options":mcq.get("options",[]),"answer":mcq.get("answer",""),
                "explanation":mcq.get("explanation",""),"category":a.category,"source":a.title[:60],"article_id":a.id})
        if len(questions) >= 25: break
    _bank = [
        {"question":"Which body decides India's repo rate?","options":["Finance Ministry","MPC","SEBI","NABARD"],"answer":"MPC","explanation":"Monetary Policy Committee sets repo rate.","category":"Economy","source":"Static"},
        {"question":"Article 21 of the Constitution deals with?","options":["Right to Equality","Right to Life","Right to Education","Right to Speech"],"answer":"Right to Life","explanation":"Art 21 — Right to Life and Personal Liberty.","category":"Polity","source":"Static"},
        {"question":"GII is published by?","options":["World Bank","UNDP","WIPO","IMF"],"answer":"WIPO","explanation":"WIPO publishes GII annually.","category":"Reports & Indexes","source":"Static"},
        {"question":"ISRO HQ is in?","options":["Mumbai","Bengaluru","Chennai","Hyderabad"],"answer":"Bengaluru","explanation":"ISRO HQ is in Bengaluru.","category":"Science & Technology","source":"Static"},
        {"question":"Paris Agreement relates to?","options":["Nuclear weapons","Climate change","Trade","Human rights"],"answer":"Climate change","explanation":"Paris Agreement 2015 on climate action.","category":"Environment","source":"Static"},
    ]
    for i, q in enumerate(_bank):
        if len(questions) >= 25: break
        if q["question"] not in seen: questions.append(q); seen.add(q["question"])
    test = WeeklyTest(id=new_id(), week_label=label, questions=questions[:25])
    db.add(test); db.commit(); db.refresh(test)
    return test


def get_current_week_test(db):
    t = _get_or_create(db, _week_label())
    return {"id":t.id,"week_label":t.week_label,"total_questions":len(t.questions),"questions":t.questions,"created_at":t.created_at.isoformat()}


def submit_weekly_attempt(db, user_id, test_id, answers):
    test = db.query(WeeklyTest).filter(WeeklyTest.id==test_id).first()
    if not test: return {"error":"Test not found"}
    correct, result_answers = 0, []
    for ans in answers:
        idx, chosen = ans.get("q_index",-1), ans.get("chosen","")
        if 0 <= idx < len(test.questions):
            ok = chosen == test.questions[idx]["answer"]
            if ok: correct += 1
            result_answers.append({"q_index":idx,"chosen":chosen,"correct":test.questions[idx]["answer"],"is_correct":ok})
    total = len(test.questions)
    score = round(correct/total*100) if total else 0
    db.add(WeeklyTestAttempt(id=new_id(),user_id=user_id,test_id=test_id,
        week_label=test.week_label,score_pct=score,correct=correct,total=total,answers=result_answers))
    db.commit()
    cats = {}
    for ra in result_answers:
        cat = test.questions[ra["q_index"]].get("category","General")
        cats.setdefault(cat,{"c":0,"t":0})
        cats[cat]["t"] += 1
        if ra["is_correct"]: cats[cat]["c"] += 1
    weak = [c for c,v in cats.items() if v["t"]>0 and v["c"]/v["t"]<0.5]
    return {"score_pct":score,"correct":correct,"total":total,"weak_areas":weak,"result_answers":result_answers,
            "feedback":"Excellent! 🎉" if score>=80 else "Good effort. Focus on weak areas." if score>=50 else "Keep revising — consistency is key."}


def get_weekly_leaderboard(db, week_label=None):
    label = week_label or _week_label()
    attempts = db.query(WeeklyTestAttempt).filter(WeeklyTestAttempt.week_label==label).order_by(WeeklyTestAttempt.score_pct.desc()).limit(20).all()
    return [{"rank":i+1,"user_id":a.user_id,"score_pct":a.score_pct,"correct":a.correct,"total":a.total} for i,a in enumerate(attempts)]
