"""Monthly Mock Test — 100 questions, 2 hours, negative marking, all-India rank."""
import datetime
from sqlalchemy.orm import Session
from .database import Article, MockTest, MockTestAttempt, User, new_id

def _month_label(dt=None):
    return (dt or datetime.datetime.utcnow()).strftime("%Y-%m")

def _month_name(label):
    import calendar
    y,m = label.split("-"); return f"{calendar.month_name[int(m)]} {y}"

def _get_or_create(db, label, exam_type):
    t = db.query(MockTest).filter(MockTest.month_label==label,MockTest.exam_type==exam_type).first()
    return t or _build(db, label, exam_type)

def _build(db, label, exam_type):
    y,m = int(label.split("-")[0]), int(label.split("-")[1])
    start = datetime.datetime(y,m,1)
    end   = datetime.datetime(y,m+1,1) if m<12 else datetime.datetime(y+1,1,1)
    articles = db.query(Article).filter(Article.include==True,Article.published_at>=start,Article.published_at<end).order_by(Article.importance_score.desc()).limit(200).all()
    if len(articles) < 20:
        articles = db.query(Article).filter(Article.include==True).order_by(Article.importance_score.desc()).limit(200).all()
    questions, seen = [], set()
    for a in articles:
        for mcq in (a.mcqs_json or []):
            q = mcq.get("question","")
            if q in seen or not mcq.get("options"): continue
            seen.add(q)
            questions.append({"question":q,"options":mcq.get("options",[]),"answer":mcq.get("answer",""),
                "explanation":mcq.get("explanation",""),"category":a.category,"source":a.title[:60],"article_id":a.id,"marks":2})
        if len(questions)>=100: break
    static = [
        {"question":"Which Article abolishes untouchability?","options":["Article 15","Article 17","Article 14","Article 21"],"answer":"Article 17","explanation":"Art 17 abolishes untouchability.","category":"Polity","source":"Static","marks":2},
        {"question":"IMF headquarter is in?","options":["New York","Geneva","Washington D.C.","London"],"answer":"Washington D.C.","explanation":"IMF HQ Washington D.C.","category":"International Relations","source":"Static","marks":2},
        {"question":"India's first indigenous aircraft carrier?","options":["INS Vikramaditya","INS Vikrant","INS Viraat","INS Chakra"],"answer":"INS Vikrant","explanation":"INS Vikrant is India's first domestic carrier.","category":"Defence","source":"Static","marks":2},
        {"question":"Ganga Action Plan launched in?","options":["1980","1986","1992","1995"],"answer":"1986","explanation":"GAP 1986 under Rajiv Gandhi.","category":"Environment","source":"Static","marks":2},
        {"question":"MUDRA stands for?","options":["Micro Units Development Refinance Agency","Multi-Use Development Reserve Agency","Micro Unified Development Refinance Authority","None"],"answer":"Micro Units Development Refinance Agency","explanation":"MUDRA loans for micro enterprises.","category":"Government Schemes","source":"Static","marks":2},
    ]
    for q in static:
        if q["question"] not in seen: questions.append(q); seen.add(q["question"])
        if len(questions)>=100: break
    test = MockTest(id=new_id(),month_label=label,exam_type=exam_type,questions=questions[:100])
    db.add(test); db.commit(); db.refresh(test)
    return test

def get_mock_test(db, exam_type="UPSC", month=None):
    label = month or _month_label()
    t = _get_or_create(db, label, exam_type)
    return {"id":t.id,"month_label":t.month_label,"exam_type":t.exam_type,"total_questions":len(t.questions),"duration_mins":120,"questions":t.questions,"created_at":t.created_at.isoformat()}

def submit_mock_attempt(db, user_id, test_id, answers, time_taken=0):
    test = db.query(MockTest).filter(MockTest.id==test_id).first()
    if not test: return {"error":"Test not found"}
    correct=wrong=unattempted=0; marks=0.0; result_answers=[]
    for ans in answers:
        idx,chosen = ans.get("q_index",-1), ans.get("chosen","")
        if 0<=idx<len(test.questions):
            q = test.questions[idx]; ok = chosen==q["answer"]; m = q.get("marks",2)
            if not chosen: unattempted+=1
            elif ok: correct+=1; marks+=m
            else: wrong+=1; marks-=m/3
            result_answers.append({"q_index":idx,"chosen":chosen,"correct":q["answer"],"is_correct":ok})
    total=len(test.questions); max_marks=total*2
    score_pct=round(max(0,marks)/max_marks*100,1)
    attempt = MockTestAttempt(id=new_id(),user_id=user_id,test_id=test_id,month_label=test.month_label,
        exam_type=test.exam_type,score_pct=score_pct,correct=correct,total=total,time_taken=time_taken,answers=result_answers)
    db.add(attempt); db.commit()
    all_a = db.query(MockTestAttempt).filter(MockTestAttempt.test_id==test_id).order_by(MockTestAttempt.score_pct.desc()).all()
    rank = next((i+1 for i,a in enumerate(all_a) if a.id==attempt.id), len(all_a))
    cats={}
    for ra in result_answers:
        cat=test.questions[ra["q_index"]].get("category","General"); cats.setdefault(cat,{"c":0,"t":0}); cats[cat]["t"]+=1
        if ra.get("is_correct"): cats[cat]["c"]+=1
    weak=[c for c,v in cats.items() if v["t"]>0 and v["c"]/v["t"]<0.4]
    return {"score_pct":score_pct,"marks_scored":round(marks,1),"max_marks":max_marks,"correct":correct,"wrong":wrong,
            "unattempted":unattempted,"total":total,"time_taken_secs":time_taken,"rank":rank,"total_attempts":len(all_a),
            "weak_areas":weak,"result_answers":result_answers,
            "feedback":"Outstanding! 🏆" if score_pct>=80 else "Good score! Review weak areas." if score_pct>=60 else "Keep practising." if score_pct>=40 else "Revise more. Attempt daily quizzes first."}

def get_mock_leaderboard(db, test_id=None, month=None, exam_type="UPSC"):
    q = db.query(MockTestAttempt)
    if test_id: q=q.filter(MockTestAttempt.test_id==test_id)
    elif month: q=q.filter(MockTestAttempt.month_label==month,MockTestAttempt.exam_type==exam_type)
    attempts = q.order_by(MockTestAttempt.score_pct.desc()).limit(50).all()
    result=[]
    for i,a in enumerate(attempts):
        user=db.query(User).filter(User.id==a.user_id).first()
        result.append({"rank":i+1,"user_name":user.name if user else "Student","score_pct":a.score_pct,"correct":a.correct,"total":a.total,"time_taken":a.time_taken})
    return result
