from calendar import monthrange
from datetime import date, datetime, timedelta

from models import Attendance, Budget, Exam, Expense, Goal, Note, ProductivityScore, StudySession, Task


PRODUCTIVITY_WEIGHTS = {
    "tasks": 30,
    "study": 25,
    "attendance": 20,
    "goals": 15,
    "exam_preparation": 10,
}


def _clamp(value, minimum=0, maximum=100):
    return max(minimum, min(maximum, value))


def _date_range(query, column, start, end):
    return query.filter(column >= start, column <= end)


def calculate_productivity_score(data):
    score = (
        data["task_completion"] * PRODUCTIVITY_WEIGHTS["tasks"]
        + data["study_activity"] * PRODUCTIVITY_WEIGHTS["study"]
        + data["attendance_rate"] * PRODUCTIVITY_WEIGHTS["attendance"]
        + data["goal_progress"] * PRODUCTIVITY_WEIGHTS["goals"]
        + data["exam_preparation"] * PRODUCTIVITY_WEIGHTS["exam_preparation"]
    )
    return round(_clamp(score))


def _period_dates(start, end):
    labels = []
    cursor = start
    while cursor <= end:
        labels.append(cursor)
        cursor += timedelta(days=1)
    return labels


def _month_labels(end, count=6):
    labels = []
    year, month = end.year, end.month
    for _ in range(count):
        labels.append((year, month))
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    return list(reversed(labels))


def _month_start(year, month):
    return date(year, month, 1)


def _activity(items, icon, label, item_date):
    return {"icon": icon, "label": label, "date": item_date.isoformat()}


def build_analytics(user_id, start, end):
    tasks = _date_range(Task.query.filter_by(user_id=user_id), Task.created_at, datetime.combine(start, datetime.min.time()), datetime.combine(end, datetime.max.time())).all()
    all_tasks = Task.query.filter_by(user_id=user_id).all()
    studies = _date_range(StudySession.query.filter_by(user_id=user_id), StudySession.study_date, start, end).all()
    attendance = _date_range(Attendance.query.filter_by(user_id=user_id), Attendance.created_at, datetime.combine(start, datetime.min.time()), datetime.combine(end, datetime.max.time())).all()
    expenses = _date_range(Expense.query.filter_by(user_id=user_id), Expense.expense_date, start, end).all()
    goals = Goal.query.filter_by(user_id=user_id).all()
    exams = Exam.query.filter_by(user_id=user_id).all()
    notes = _date_range(Note.query.filter_by(user_id=user_id), Note.created_at, datetime.combine(start, datetime.min.time()), datetime.combine(end, datetime.max.time())).all()

    completed_tasks = [task for task in tasks if task.status == "completed"]
    pending_tasks = [task for task in all_tasks if task.status != "completed"]
    overdue_tasks = [task for task in pending_tasks if task.due_date < date.today()]
    high_priority = [task for task in pending_tasks if task.priority == "high"]
    total_classes = sum(item.total_classes for item in attendance)
    attended_classes = sum(item.attended_classes for item in attendance)
    attendance_rate = attended_classes / total_classes if total_classes else 0
    total_study_hours = sum(item.duration for item in studies)
    days = max((end - start).days + 1, 1)
    subject_study = {}
    for item in studies:
        subject_study[item.subject] = subject_study.get(item.subject, 0) + item.duration
    subject_attendance = {}
    for item in attendance:
        record = subject_attendance.setdefault(item.subject, [0, 0])
        record[0] += item.attended_classes
        record[1] += item.total_classes
    attendance_subjects = [{"subject": subject, "percentage": round(values[0] / values[1] * 100, 1) if values[1] else 0, "attended": values[0], "total": values[1]} for subject, values in sorted(subject_attendance.items())]
    goal_progress = sum(goal.progress for goal in goals) / len(goals) / 100 if goals else 0
    upcoming_exams = [exam for exam in exams if exam.status == "upcoming" and exam.exam_date >= date.today()]
    completed_exams = [exam for exam in exams if exam.status == "completed"]
    exam_subjects = {exam.subject for exam in exams}
    exam_preparation = _clamp(sum(subject_study.get(subject, 0) for subject in exam_subjects) / max(len(exam_subjects) * 10, 1)) if exam_subjects else 0
    score_data = {
        "task_completion": len(completed_tasks) / len(tasks) if tasks else 0,
        "study_activity": _clamp(total_study_hours / max(days * 2, 1)),
        "attendance_rate": attendance_rate,
        "goal_progress": goal_progress,
        "exam_preparation": exam_preparation,
    }

    daily_dates = _period_dates(start, end)
    task_by_day = {day: 0 for day in daily_dates}
    study_by_day = {day: 0 for day in daily_dates}
    expense_by_day = {day: 0 for day in daily_dates}
    for task in completed_tasks:
        created = task.created_at.date()
        if created in task_by_day:
            task_by_day[created] += 1
    for study in studies:
        study_by_day[study.study_date] += study.duration
    for expense in expenses:
        expense_by_day[expense.expense_date] += expense.amount
    expense_categories = {}
    for expense in expenses:
        expense_categories[expense.category] = expense_categories.get(expense.category, 0) + expense.amount

    budget_record = Budget.query.filter_by(user_id=user_id).first()
    monthly_expenses = sum(item.amount for item in Expense.query.filter_by(user_id=user_id).filter(Expense.expense_date >= date.today().replace(day=1)).all())
    budget_amount = budget_record.monthly_amount if budget_record else 0
    recent = []
    for task in completed_tasks:
        recent.append((_activity(task, "check2-square", f"Task completed: {task.title}", task.created_at.date()), task.created_at))
    for study in studies:
        recent.append((_activity(study, "book", f"Study session: {study.subject}", study.study_date), datetime.combine(study.study_date, datetime.min.time())))
    for goal in goals:
        recent.append((_activity(goal, "bullseye", f"Goal updated: {goal.title}", goal.created_at.date()), goal.created_at))
    for expense in expenses:
        recent.append((_activity(expense, "wallet2", f"Expense added: {expense.category}", expense.expense_date), datetime.combine(expense.expense_date, datetime.min.time())))
    for exam in exams:
        recent.append((_activity(exam, "journal-bookmark", f"Exam added: {exam.exam_name}", exam.created_at.date()), exam.created_at))
    for note in notes:
        recent.append((_activity(note, "journal-text", f"Note uploaded: {note.title}", note.created_at.date()), note.created_at))
    recent_activity = [item for item, _ in sorted(recent, key=lambda pair: pair[1], reverse=True)[:8]]

    insights = []
    if high_priority:
        insights.append({"type": "warning", "text": f"You have {len(high_priority)} pending high-priority task{'s' if len(high_priority) != 1 else ''}."})
    low_attendance = [item for item in attendance_subjects if item["percentage"] < 75]
    if low_attendance:
        insights.append({"type": "danger", "text": f"Attendance in {low_attendance[0]['subject']} is below the 75% threshold."})
    if total_study_hours and total_study_hours >= days * 2:
        insights.append({"type": "success", "text": "Your study activity is meeting the two-hour daily benchmark."})
    if budget_amount and monthly_expenses >= budget_amount * 0.8:
        insights.append({"type": "warning", "text": "Your expenses are approaching your monthly budget."})
    near_goal = next((goal for goal in goals if goal.status != "completed" and goal.progress >= 75), None)
    if near_goal:
        insights.append({"type": "success", "text": f"You are close to completing your {near_goal.title} goal."})
    if not insights:
        insights.append({"type": "info", "text": "Add a study session, task, or goal to unlock more personal insights."})

    return {
        "range": {"start": start.isoformat(), "end": end.isoformat(), "days": days},
        "summary": {"productivity_score": calculate_productivity_score(score_data), "study_hours": round(total_study_hours, 1), "tasks_completed": len(completed_tasks), "attendance": round(attendance_rate * 100, 1), "goals_completed": sum(goal.status == "completed" for goal in goals), "expenses": round(sum(item.amount for item in expenses), 2)},
        "study": {"total_hours": round(total_study_hours, 1), "average_daily_hours": round(total_study_hours / days, 1), "most_studied": max(subject_study, key=subject_study.get, default="None yet"), "least_studied": min(subject_study, key=subject_study.get, default="None yet"), "sessions": len(studies), "trend": {"labels": [day.isoformat() for day in daily_dates], "values": [round(study_by_day[day], 1) for day in daily_dates]}, "subjects": {"labels": list(subject_study), "values": [round(value, 1) for value in subject_study.values()]}},
        "tasks": {"total": len(all_tasks), "completed": len([task for task in all_tasks if task.status == "completed"]), "pending": len(pending_tasks) - len(overdue_tasks), "overdue": len(overdue_tasks), "completion_percentage": round(len([task for task in all_tasks if task.status == "completed"]) / len(all_tasks) * 100, 1) if all_tasks else 0, "high_priority_pending": len(high_priority), "status": {"labels": ["Completed", "Pending", "Overdue"], "values": [len([task for task in all_tasks if task.status == "completed"]), len(pending_tasks) - len(overdue_tasks), len(overdue_tasks)]}, "priorities": {"labels": ["Low", "Medium", "High"], "values": [sum(task.status != "completed" and task.priority == priority for task in all_tasks) for priority in ["low", "medium", "high"]]}},
        "attendance": {"overall_percentage": round(attendance_rate * 100, 1), "total_classes": total_classes, "attended": attended_classes, "missed": max(total_classes - attended_classes, 0), "low_subjects": low_attendance, "subjects": attendance_subjects, "threshold": 75},
        "expenses": {"total": round(sum(item.amount for item in expenses), 2), "current_month": round(monthly_expenses, 2), "average_daily": round(sum(item.amount for item in expenses) / days, 2), "budget": round(budget_amount, 2), "remaining": round(max(budget_amount - monthly_expenses, 0), 2), "budget_used": round(monthly_expenses / budget_amount * 100, 1) if budget_amount else 0, "categories": {"labels": list(expense_categories), "values": [round(value, 2) for value in expense_categories.values()]}, "trend": {"labels": [f"{year}-{month:02d}" for year, month in _month_labels(end)], "values": [round(sum(item.amount for item in Expense.query.filter_by(user_id=user_id).filter(Expense.expense_date >= _month_start(year, month), Expense.expense_date <= date(year, month, monthrange(year, month)[1])).all()), 2) for year, month in _month_labels(end)]}},
        "goals": {"total": len(goals), "active": sum(goal.status == "active" for goal in goals), "completed": sum(goal.status == "completed" for goal in goals), "overdue": sum(goal.status != "completed" and goal.target_date < date.today() for goal in goals), "average_progress": round(sum(goal.progress for goal in goals) / len(goals), 1) if goals else 0, "items": [{"title": goal.title, "progress": goal.progress, "status": goal.status} for goal in goals if goal.status == "active"]},
        "exams": {"upcoming": len(upcoming_exams), "completed": len(completed_exams), "items": [{"name": exam.exam_name, "subject": exam.subject, "date": exam.exam_date.isoformat(), "days_remaining": max((exam.exam_date - date.today()).days, 0), "preparation": round(_clamp(subject_study.get(exam.subject, 0) / 10) * 100, 1)} for exam in sorted(upcoming_exams, key=lambda item: item.exam_date)[:6]]},
        "productivity": {"score": calculate_productivity_score(score_data), "weights": PRODUCTIVITY_WEIGHTS, "components": {key: round(value * 100, 1) for key, value in score_data.items()}, "trend": {"labels": [item.recorded_date.isoformat() for item in ProductivityScore.query.filter_by(user_id=user_id).filter(ProductivityScore.recorded_date >= start, ProductivityScore.recorded_date <= end).order_by(ProductivityScore.recorded_date).all()], "values": [item.score for item in ProductivityScore.query.filter_by(user_id=user_id).filter(ProductivityScore.recorded_date >= start, ProductivityScore.recorded_date <= end).order_by(ProductivityScore.recorded_date).all()]}},
        "insights": insights,
        "recent_activity": recent_activity,
    }
