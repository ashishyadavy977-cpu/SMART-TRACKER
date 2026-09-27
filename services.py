from datetime import date, datetime, timedelta
from models import Achievement, Announcement, Assignment, Attendance, Budget, CalendarEvent, Exam, Expense, FocusSession, Goal, Habit, Notification, ProductivityScore, StudySession, StudyTarget, Task
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
    habits = {item.completed_date for habit in Habit.query.filter_by(user_id=user_id).all() for item in habit.completions}
    focus = {item.completed_at.date() for item in FocusSession.query.filter_by(user_id=user_id, status="completed").filter(FocusSession.mode.in_({"focus", "custom"})).all() if item.completed_at}
    def run(days):
        count = 0; cursor = date.today()
        while cursor in days: count += 1; cursor -= timedelta(days=1)
        return count
    activity = studies | completed | habits | focus
    longest = 0
    cursor = date.today()
    while cursor in activity:
        longest += 1; cursor -= timedelta(days=1)
    all_dates = sorted(activity)
    run_length = 0; previous = None
    for item in all_dates:
        run_length = run_length + 1 if previous and (item - previous).days == 1 else 1
        longest = max(longest, run_length); previous = item
    week_start = date.today() - timedelta(days=date.today().weekday())
    return {"study": run(studies), "tasks": run(completed), "goals": run(goals), "habits": run(habits), "focus": run(focus), "current": run(activity), "longest": longest, "today": len({"study" if date.today() in studies else None, "tasks" if date.today() in completed else None, "habits" if date.today() in habits else None, "focus" if date.today() in focus else None} - {None}), "week": sum(item >= week_start for item in activity)}


def recommendations(user_id):
    tasks = Task.query.filter_by(user_id=user_id).all(); attendance = Attendance.query.filter_by(user_id=user_id).all(); goals = Goal.query.filter_by(user_id=user_id).all(); studies = StudySession.query.filter_by(user_id=user_id).all()
    results = []; total = sum(a.total_classes for a in attendance); attended = sum(a.attended_classes for a in attendance)
    if total and attended / total < .75: results.append(("Attendance needs attention", "Your attendance is below 75%. Focus on attending upcoming classes.", "warning"))
    if sum(t.status != "completed" and t.due_date < date.today() for t in tasks) >= 2: results.append(("Overdue tasks", "You have several overdue tasks. Prioritize the nearest deadlines.", "danger"))
    if sum(s.duration for s in studies if s.study_date >= date.today() - timedelta(days=7)) < 5: results.append(("Study target", "Your study time is lower than your target. Consider scheduling a study session.", "info"))
    if any(g.status != "completed" and 0 <= (g.target_date - date.today()).days <= 7 for g in goals): results.append(("Goal deadline approaching", "One of your goals is approaching its deadline.", "success"))
    return results


def refresh_notifications(user_id):
    today = date.today(); existing = {(n.title, n.message) for n in Notification.query.filter_by(user_id=user_id).all()}
    items = []
    for title, message, kind in recommendations(user_id): items.append((title, message, kind))
    for task in Task.query.filter_by(user_id=user_id, status="pending").all():
        if 0 <= (task.due_date - today).days <= 2: items.append(("Task due soon", f"{task.title} is due on {task.due_date.strftime('%d %b %Y')}.", "info"))
    for exam in Exam.query.filter_by(user_id=user_id, status="upcoming").all():
        days = (exam.exam_date - today).days
        if days == 1: items.append(("Exam tomorrow", f"{exam.exam_name} ({exam.subject}) is tomorrow.", "danger"))
        elif 0 <= days <= 3: items.append(("Exam within 3 days", f"{exam.exam_name} ({exam.subject}) is on {exam.exam_date.strftime('%d %b %Y')}.", "warning"))
    for assignment in Assignment.query.filter_by(user_id=user_id).all():
        days = (assignment.due_date - today).days
        if assignment.status != "submitted" and days < 0:
            items.append(("Assignment overdue", f"{assignment.title} was due on {assignment.due_date.strftime('%d %b %Y')}.", "danger"))
        elif assignment.status != "submitted" and days == 1:
            items.append(("Assignment due tomorrow", f"{assignment.title} is due tomorrow.", "warning"))
    for habit in Habit.query.filter_by(user_id=user_id).all():
        if date.today() not in habit.completion_dates():
            items.append(("Habit reminder", f"Remember to complete {habit.name} today.", "info"))
    if not StudySession.query.filter_by(user_id=user_id, study_date=today).first():
        items.append(("Study reminder", "You have not logged a study session today.", "info"))
    budget = Budget.query.filter_by(user_id=user_id).first()
    month_start = today.replace(day=1)
    spent = sum(item.amount for item in Expense.query.filter_by(user_id=user_id).all() if item.expense_date >= month_start)
    if budget and budget.monthly_amount > 0:
        percentage = spent / budget.monthly_amount * 100
        threshold = 100 if percentage >= 100 else 90 if percentage >= 90 else 75 if percentage >= 75 else 50 if percentage >= 50 else 0
        if threshold:
            items.append(("Budget alert", f"You have used {threshold}% of your monthly budget.", "danger" if threshold >= 90 else "warning"))
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
