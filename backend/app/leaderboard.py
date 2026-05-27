"""Leaderboard — XP-based ranking weekly/monthly/alltime."""
import datetime
from .database import User, WeeklyTestAttempt, MockTestAttempt, RevisionSchedule, ReadLog, new_id

XP_READ_ARTICLE  = 5
XP_REVISION_DONE = 10
XP_STREAK_BONUS  = 20

def award_xp(user, amount, db):
    user.xp_points = (user.xp_points or 0) + amount
    db.commit()

def _week_label(dt=None):
    d = (dt or datetime.datetime.utcnow()).isocalendar()
    return f"{d[0]}-W{d[1]:02d}"

def _month_label(dt=None):
    return (dt or datetime.datetime.utcnow()).strftime("%Y-%m")

def get_leaderboard(db, period="weekly", exam_type="UPSC", limit=20):
    users = db.query(User).filter(User.email != None).all()
    rows = []
    for user in users:
        score = _score(user, db, period, exam_type)
        rows.append({"user_id":user.id,"user_name":user.name,"exam_type":user.target_exam,
                     "xp_points":user.xp_points or 0,"streak_days":user.streak_days or 0,"score":score})
    rows.sort(key=lambda x: (-x["score"],-x["xp_points"]))
    for i,r in enumerate(rows): r["rank"]=i+1
    label = _week_label() if period=="weekly" else (_month_label() if period=="monthly" else "All time")
    return {"period":period,"period_label":label,"exam_type":exam_type,"entries":rows[:limit]}

def _score(user, db, period, exam_type):
    now = datetime.datetime.utcnow()
    since = now-datetime.timedelta(days=7) if period=="weekly" else (now-datetime.timedelta(days=30) if period=="monthly" else datetime.datetime(2020,1,1))
    reads = db.query(ReadLog).filter(ReadLog.user_id==user.id, ReadLog.read_at>=since).count()
    xp = reads * XP_READ_ARTICLE
    revs = db.query(RevisionSchedule).filter(RevisionSchedule.user_id==user.id,RevisionSchedule.completed==True,RevisionSchedule.created_at>=since).all()
    xp += len(revs) * XP_REVISION_DONE
    if period=="weekly":
        attempts = db.query(WeeklyTestAttempt).filter(WeeklyTestAttempt.user_id==user.id,WeeklyTestAttempt.week_label==_week_label()).all()
    elif period=="monthly":
        attempts = db.query(MockTestAttempt).filter(MockTestAttempt.user_id==user.id,MockTestAttempt.month_label==_month_label()).all()
    else: attempts=[]
    if attempts: xp += int(sum(a.score_pct for a in attempts)/len(attempts))
    xp += ((user.streak_days or 0)//7)*XP_STREAK_BONUS
    return xp

def get_user_rank(user_id, db, period="weekly", exam_type="UPSC"):
    board = get_leaderboard(db, period, exam_type, limit=200)
    entry = next((e for e in board["entries"] if e["user_id"]==user_id), None)
    return {"rank":entry["rank"] if entry else None,"total_users":len(board["entries"]),
            "score":entry["score"] if entry else 0,"xp_points":entry["xp_points"] if entry else 0,
            "period":period,"period_label":board["period_label"]}
