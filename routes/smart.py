from datetime import date, datetime, timedelta
from csv import writer
from io import BytesIO, StringIO
from flask import Blueprint, jsonify, flash, make_response, redirect, render_template, request, session, url_for
from common import admin_required, db, login_required, parse_date, student_query
from models import Achievement, Announcement, Attendance, Budget, Expense, Goal, Notification, ProductivityScore, StudySession, StudyTarget, Task, User
from services import award, recommendations, record_score, refresh_notifications, score_for, score_label, streaks

smart_bp = Blueprint("smart", __name__)

@smart_bp.route("/calendar")
@login_required
def calendar(): return render_template("calendar.html")

@smart_bp.route("/api/calendar")
@login_required
def calendar_events():
    events = [{"id": f"task-{x.id}", "title": x.title, "start": x.due_date.isoformat(), "color": "#ef8e55", "url": url_for("tasks.edit_task", task_id=x.id)} for x in student_query(Task).all()]
    events += [{"id": f"goal-{x.id}", "title": f"Goal: {x.title}", "start": x.target_date.isoformat(), "color": "#75873b"} for x in student_query(Goal).all()]
    events += [{"id": f"study-{x.id}", "title": f"Study: {x.subject}", "start": x.study_date.isoformat(), "color": "#4d8c7b"} for x in student_query(StudySession).all()]
    return jsonify(events)

@smart_bp.post("/api/calendar/tasks/<int:task_id>")
@login_required
def move_calendar_task(task_id):
    task = student_query(Task).filter_by(id=task_id).first_or_404()
    due_date = parse_date(request.json.get("date") if request.is_json else request.form.get("date"))
    if not due_date:
        return jsonify({"error": "A valid date is required."}), 400
    task.due_date = due_date
    db.session.commit()
    return jsonify({"id": task.id, "date": task.due_date.isoformat()})

@smart_bp.route("/notifications")
@login_required
def notifications():
    refresh_notifications(session["user_id"]); return render_template("notifications.html", notifications=student_query(Notification).order_by(Notification.created_at.desc()).all())

@smart_bp.post("/notifications/<int:notification_id>/read")
@login_required
def mark_notification(notification_id):
    item = student_query(Notification).filter_by(id=notification_id).first_or_404(); item.is_read = True; db.session.commit(); return redirect(request.referrer or url_for("smart.notifications"))

@smart_bp.post("/notifications/read-all")
@login_required
def mark_all_notifications():
    student_query(Notification).filter_by(is_read=False).update({"is_read": True}); db.session.commit(); return redirect(url_for("smart.notifications"))

@smart_bp.post("/notifications/<int:notification_id>/delete")
@login_required
def delete_notification(notification_id):
    item = student_query(Notification).filter_by(id=notification_id).first_or_404(); db.session.delete(item); db.session.commit(); return redirect(url_for("smart.notifications"))

@smart_bp.route("/recommendations")
@login_required
def recommendation_page(): return render_template("recommendations.html", recommendations=recommendations(session["user_id"]))

@smart_bp.route("/productivity")
@login_required
def productivity():
    score = record_score(session["user_id"]); history = student_query(ProductivityScore).order_by(ProductivityScore.recorded_date).all(); return render_template("productivity.html", score=score, label=score_label(score), streaks=streaks(session["user_id"]), history=history)

@smart_bp.route("/study-targets", methods=["GET", "POST"])
@login_required
def study_targets():
    if request.method == "POST":
        start = parse_date(request.form.get("start_date")); end = parse_date(request.form.get("end_date")); hours = request.form.get("target_hours", type=float)
        if not request.form.get("subject", "").strip() or not start or not end or not hours or hours <= 0 or end < start: flash("Enter valid target details.", "danger")
        else: db.session.add(StudyTarget(user_id=session["user_id"], subject=request.form["subject"].strip(), target_hours=hours, start_date=start, end_date=end)); db.session.commit(); flash("Study target created.", "success"); return redirect(url_for("smart.study_targets"))
    targets = student_query(StudyTarget).order_by(StudyTarget.end_date.desc()).all(); actual = {x.id: sum(s.duration for s in student_query(StudySession).filter(StudySession.subject == x.subject, StudySession.study_date >= x.start_date, StudySession.study_date <= x.end_date).all()) for x in targets}
    return render_template("study_targets.html", targets=targets, actual=actual)

@smart_bp.post("/study-targets/<int:target_id>/delete")
@login_required
def delete_target(target_id):
    target = student_query(StudyTarget).filter_by(id=target_id).first_or_404(); db.session.delete(target); db.session.commit(); return redirect(url_for("smart.study_targets"))

@smart_bp.route("/budget", methods=["GET", "POST"])
@login_required
def budget():
    item = Budget.query.filter_by(user_id=session["user_id"]).first()
    if request.method == "POST":
        amount = request.form.get("monthly_amount", type=float)
        if not amount or amount <= 0: flash("Enter a valid monthly budget.", "danger")
        else:
            if not item: item = Budget(user_id=session["user_id"]); db.session.add(item)
            item.monthly_amount = amount; db.session.commit(); flash("Budget updated.", "success"); return redirect(url_for("smart.budget"))
    month_start = date.today().replace(day=1); spent = sum(x.amount for x in student_query(Expense).filter(Expense.expense_date >= month_start).all())
    return render_template("budget.html", budget=item, spent=spent)

@smart_bp.route("/api/analytics")
@login_required
def analytics():
    uid = session["user_id"]; days = int(request.args.get("days", 30)); start = date.today() - timedelta(days=days - 1); labels = [(start + timedelta(days=i)).isoformat() for i in range(days)]
    studies = student_query(StudySession).all(); tasks = student_query(Task).all(); expenses = student_query(Expense).all(); scores = student_query(ProductivityScore).all()
    return jsonify({"labels": labels, "study": [sum(x.duration for x in studies if x.study_date == date.fromisoformat(d)) for d in labels], "tasks": [sum(x.status == "completed" and x.created_at.date() == date.fromisoformat(d) for x in tasks) for d in labels], "expenses": [sum(x.amount for x in expenses if x.expense_date == date.fromisoformat(d)) for d in labels], "scores": [{"date": x.recorded_date.isoformat(), "score": x.score} for x in scores]})

@smart_bp.route("/reports/<report_type>.pdf")
@login_required
def pdf_report(report_type):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    allowed = {"overall", "tasks", "study", "attendance", "expenses", "goals", "productivity"}
    if report_type not in allowed: return make_response("Report not found", 404)
    user = db.session.get(User, session["user_id"]); buffer = BytesIO(); pdf = canvas.Canvas(buffer, pagesize=letter); pdf.setTitle(f"Smart Tracker {report_type.title()} Report")
    pdf.setFont("Helvetica-Bold", 18); pdf.drawString(54, 740, f"Smart Tracker - {report_type.title()} Report"); pdf.setFont("Helvetica", 11); pdf.drawString(54, 718, f"Student: {user.name}    Date: {date.today().isoformat()}")
    rows = [("Tasks", Task, lambda x: len(x)), ("Study hours", StudySession, lambda x: round(sum(y.duration for y in x), 1)), ("Attendance records", Attendance, lambda x: len(x)), ("Expenses", Expense, lambda x: round(sum(y.amount for y in x), 2)), ("Goals", Goal, lambda x: len(x))]
    y = 675
    for label, model, calc in rows:
        values = model.query.filter_by(user_id=user.id).all(); pdf.drawString(70, y, f"{label}: {calc(values)}"); y -= 25
    if report_type == "productivity": pdf.drawString(70, y, f"Productivity score: {score_for(user.id)}/100")
    pdf.showPage(); pdf.save(); buffer.seek(0); return make_response(buffer.getvalue(), 200, {"Content-Type": "application/pdf", "Content-Disposition": f"attachment; filename=smart_tracker_{report_type}.pdf"})

@smart_bp.route("/reports/<report_type>.csv")
@login_required
def csv_report(report_type):
    allowed = {"overall", "tasks", "study", "attendance", "expenses", "goals", "productivity"}
    if report_type not in allowed:
        return make_response("Report not found", 404)
    user_id = session["user_id"]
    sections = {
        "tasks": [("Title", "Description", "Priority", "Due date", "Status"), [(x.title, x.description or "", x.priority, x.due_date, x.status) for x in student_query(Task).order_by(Task.due_date).all()]],
        "study": [("Subject", "Topic", "Duration", "Date", "Notes"), [(x.subject, x.topic or "", x.duration, x.study_date, x.notes or "") for x in student_query(StudySession).order_by(StudySession.study_date).all()]],
        "attendance": [("Subject", "Total classes", "Attended", "Absent", "Percentage"), [(x.subject, x.total_classes, x.attended_classes, x.absent_classes, x.percentage) for x in student_query(Attendance).all()]],
        "expenses": [("Date", "Category", "Amount", "Description"), [(x.expense_date, x.category, x.amount, x.description or "") for x in student_query(Expense).order_by(Expense.expense_date).all()]],
        "goals": [("Title", "Target date", "Progress", "Status", "Description"), [(x.title, x.target_date, x.progress, x.status, x.description or "") for x in student_query(Goal).order_by(Goal.target_date).all()]],
    }
    output = StringIO(); csv_writer = writer(output)
    if report_type in sections:
        headers, rows = sections[report_type]; csv_writer.writerow(headers); csv_writer.writerows(rows)
    else:
        csv_writer.writerow(("Metric", "Value"))
        records = {"Tasks": Task, "Study sessions": StudySession, "Attendance records": Attendance, "Expenses": Expense, "Goals": Goal}
        for label, model in records.items():
            values = model.query.filter_by(user_id=user_id).all()
            value = round(sum(x.duration for x in values), 1) if model is StudySession else round(sum(x.amount for x in values), 2) if model is Expense else len(values)
            csv_writer.writerow((label, value))
        if report_type == "productivity": csv_writer.writerow(("Productivity score", score_for(user_id)))
    response = make_response(output.getvalue(), 200)
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = f"attachment; filename=smart_tracker_{report_type}.csv"
    return response

@smart_bp.route("/admin/announcements", methods=["GET", "POST"])
@admin_required
def announcements():
    if request.method == "POST":
        expiry = parse_date(request.form.get("expiry_date"))
        if not request.form.get("title", "").strip() or not request.form.get("message", "").strip() or not expiry: flash("Complete announcement details.", "danger")
        else: db.session.add(Announcement(title=request.form["title"].strip(), message=request.form["message"].strip(), priority=request.form.get("priority", "normal"), expiry_date=expiry)); db.session.commit(); flash("Announcement published.", "success"); return redirect(url_for("smart.announcements"))
    return render_template("admin/announcements.html", announcements=Announcement.query.order_by(Announcement.created_at.desc()).all())

@smart_bp.route("/admin/analytics")
@admin_required
def admin_analytics():
    users = User.query.filter_by(role="student").all(); tasks = Task.query.all(); studies = StudySession.query.all(); attendance = Attendance.query.all(); goals = Goal.query.all(); expenses = Expense.query.all(); scores = ProductivityScore.query.all()
    total_classes = sum(item.total_classes for item in attendance); attended = sum(item.attended_classes for item in attendance)
    return jsonify({"users": len(users), "active_users": sum(item.status == "active" for item in users), "tasks": len(tasks), "completed_tasks": sum(item.status == "completed" for item in tasks), "average_attendance": round(attended / total_classes * 100, 1) if total_classes else 0, "average_study_hours": round(sum(item.duration for item in studies) / len(users), 1) if users else 0, "goals": len(goals), "completed_goals": sum(item.status == "completed" for item in goals), "expenses": round(sum(item.amount for item in expenses), 2), "average_productivity": round(sum(item.score for item in scores) / len(scores), 1) if scores else 0})
