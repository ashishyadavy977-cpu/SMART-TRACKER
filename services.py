from datetime import date, datetime, timedelta
from models import Achievement, Announcement, Attendance, Budget, Expense, Goal, Notification, ProductivityScore, StudySession, StudyTarget, Task
from models.models import db


def score_for(user_id):
    tasks = Task.query.filter_by(user_id=user_id).all(); studies = StudySession.query.filter_by(user_id=user_id).all(); attendance = Attendance.query.filter_by(user_id=user_id).all(); goals = Goal.query.filter_by(user_id=user_id).all()
    task_score = (sum(t.status == "completed" for t in tasks) / len(tasks) * 30) if tasks else 0
    total = sum(a.total_classes for a in attendance); attended = sum(a.attended_classes for a in attendance)
    attendance_score = (attended / total * 25) if total else 0
    goal_score = (sum(g.progress for g in goals) / len(goals) * .2) if goals else 0
    study_score = min(sum(s.duration for s in studies if s.study_date >= date.today() - timedelta(days=7)) / 10 * 20, 20)
    consistency_score = min(streaks(user_id)["study"] * 0.5, 5)
    return min(100, round(task_score + attendance_score + goal_score + study_score + consistency_score))


def score_label(score):
    return "Excellent" if score >= 80 else "Good" if score >= 60 else "Average" if score >= 40 else "Needs Improvement"


def streaks(user_id):
    studies = {s.study_date for s in StudySession.query.filter_by(user_id=user_id).all()}
    completed = {t.created_at.date() for t in Task.query.filter_by(user_id=user_id, status="completed").all()}
    goals = {g.created_at.date() for g in Goal.query.filter_by(user_id=user_id, status="completed").all()}
    def run(days):
        count = 0; cursor = date.today()
        while cursor in days: count += 1; cursor -= timedelta(days=1)
        return count
    return {"study": run(studies), "tasks": run(completed), "goals": run(goals)}


def recommendations(user_id):
    tasks = Task.query.filter_by(user_id=user_id).all(); attendance = Attendance.query.filter_by(user_id=user_id).all(); goals = Goal.query.filter_by(user_id=user_id).all(); studies = StudySession.query.filter_by(user_id=user_id).all()
    results = []; total = sum(a.total_classes for a in attendance); attended = sum(a.attended_classes for a in attendance)
    if total and attended / total < .75: results.append(("Attendance needs attention", "Your attendance is below 75%. Focus on attending upcoming classes.", "warning"))
    if sum(t.status != "completed" and t.due_date < date.today() for t in tasks) >= 2: results.append(("Overdue tasks", "You have several overdue tasks. Prioritize the nearest deadlines.", "danger"))
    if sum(s.duration for s in studies if s.study_date >= date.today() - timedelta(days=7)) < 5: results.append(("Study target", "Your study time is lower than your target. Consider scheduling a study session.", "info"))
    if any(g.status != "completed" and 0 <= (g.target_date - date.today()).days <= 7 for g in goals): results.append(("Goal deadline approaching", "One of your goals is approaching its deadline.", "success"))
    return results


def refresh_notifications(user_id):
    today = date.today(); existing = {(n.title, n.message) for n in Notification.query.filter_by(user_id=user_id, is_read=False).all()}
    items = []
    for title, message, kind in recommendations(user_id): items.append((title, message, kind))
    for task in Task.query.filter_by(user_id=user_id, status="pending").all():
        if 0 <= (task.due_date - today).days <= 2: items.append(("Task due soon", f"{task.title} is due on {task.due_date.strftime('%d %b %Y')}.", "info"))
    for title, message, kind in items:
        if (title, message) not in existing: db.session.add(Notification(user_id=user_id, title=title, message=message, type=kind))
    db.session.commit()


def award(user_id, name, description, points):
    if not Achievement.query.filter_by(user_id=user_id, badge_name=name).first(): db.session.add(Achievement(user_id=user_id, badge_name=name, description=description, points=points)); db.session.commit()


def record_score(user_id):
    today = date.today(); score = score_for(user_id); record = ProductivityScore.query.filter_by(user_id=user_id, recorded_date=today).first()
    if record: record.score = score
    else: db.session.add(ProductivityScore(user_id=user_id, score=score, recorded_date=today))
    db.session.commit(); return score
