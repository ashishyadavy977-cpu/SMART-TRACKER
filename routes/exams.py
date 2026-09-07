from datetime import datetime, date, timedelta

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from common import db, login_required, parse_date, student_query
from models import Assignment, Exam
from services import refresh_notifications

exams_bp = Blueprint("exams", __name__)


def _exam_form(exam=None):
    subject = request.form.get("subject", "").strip()
    exam_name = request.form.get("exam_name", "").strip()
    exam_date = parse_date(request.form.get("exam_date"))
    exam_time_value = request.form.get("exam_time", "").strip()
    total_marks_value = request.form.get("total_marks", "").strip()
    status = request.form.get("status", "upcoming").lower()
    if not subject or not exam_name or not exam_date or not total_marks_value:
        flash("Subject, exam name, date, and total marks are required.", "danger")
        return None
    try:
        total_marks = int(total_marks_value)
    except ValueError:
        total_marks = 0
    if total_marks <= 0 or status not in {"upcoming", "completed"}:
        flash("Enter valid exam details.", "danger")
        return None
    exam_time = None
    if exam_time_value:
        try:
            exam_time = datetime.strptime(exam_time_value, "%H:%M").time()
        except ValueError:
            flash("Enter a valid exam time.", "danger")
            return None
    if exam is None:
        exam = Exam(user_id=session["user_id"])
    exam.subject = subject
    exam.exam_name = exam_name
    exam.exam_date = exam_date
    exam.exam_time = exam_time
    exam.total_marks = total_marks
    exam.status = status
    exam.notes = request.form.get("notes", "").strip()
    return exam


def _assignment_form(assignment=None):
    subject = request.form.get("subject", "").strip()
    title = request.form.get("title", "").strip()
    due_date = parse_date(request.form.get("due_date"))
    priority = request.form.get("priority", "medium").lower()
    status = request.form.get("status", "pending").lower()
    if not subject or not title or not due_date:
        flash("Subject, title, and a valid due date are required.", "danger")
        return None
    if priority not in {"low", "medium", "high"} or status not in {"pending", "in progress", "submitted"}:
        flash("Choose a valid assignment priority and status.", "danger")
        return None
    if assignment is None:
        assignment = Assignment(user_id=session["user_id"])
    assignment.subject = subject
    assignment.title = title
    assignment.description = request.form.get("description", "").strip()
    assignment.due_date = due_date
    assignment.priority = priority
    assignment.status = status
    return assignment


@exams_bp.route("/exams")
@login_required
def list_exams():
    refresh_notifications(session["user_id"])
    all_exams = student_query(Exam).all()
    query = student_query(Exam)
    search = request.args.get("q", "").strip()
    filter_name = request.args.get("filter", "all")
    if search:
        query = query.filter(Exam.subject.ilike(f"%{search}%") | Exam.exam_name.ilike(f"%{search}%"))
    if filter_name in {"upcoming", "completed"}:
        query = query.filter_by(status=filter_name)
    elif filter_name == "week":
        query = query.filter(Exam.exam_date.between(date.today(), date.today() + timedelta(days=7)), Exam.status == "upcoming")
    exams = query.order_by(Exam.exam_date, Exam.exam_time).all()
    today = date.today()
    upcoming = [item for item in all_exams if item.status == "upcoming"]
    return render_template("exams/index.html", exams=exams, search=search, filter_name=filter_name, week_end=today + timedelta(days=7), total_upcoming=len(upcoming), this_week=sum(today <= item.exam_date <= today + timedelta(days=7) for item in upcoming), completed_count=sum(item.status == "completed" for item in all_exams), next_exam=min(upcoming, key=lambda item: (item.exam_date, item.exam_time or datetime.min.time()), default=None))


@exams_bp.route("/exams/add", methods=["GET", "POST"])
@login_required
def add_exam():
    if request.method == "POST":
        exam = _exam_form()
        if exam:
            db.session.add(exam)
            db.session.commit()
            flash("Exam added.", "success")
            return redirect(url_for("exams.list_exams"))
    return render_template("exams/form.html", exam=None)


@exams_bp.route("/exams/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_exam(id):
    exam = student_query(Exam).filter_by(id=id).first_or_404()
    if request.method == "POST" and _exam_form(exam):
        db.session.commit()
        flash("Exam updated.", "success")
        return redirect(url_for("exams.list_exams"))
    return render_template("exams/form.html", exam=exam)


@exams_bp.post("/exams/delete/<int:id>")
@login_required
def delete_exam(id):
    exam = student_query(Exam).filter_by(id=id).first_or_404()
    db.session.delete(exam)
    db.session.commit()
    flash("Exam deleted.", "success")
    return redirect(url_for("exams.list_exams"))


@exams_bp.route("/assignments")
@login_required
def list_assignments():
    refresh_notifications(session["user_id"])
    all_assignments = student_query(Assignment).all()
    query = student_query(Assignment)
    search = request.args.get("q", "").strip()
    subject = request.args.get("subject", "").strip()
    priority = request.args.get("priority", "").lower()
    status = request.args.get("status", "").lower()
    overdue = request.args.get("overdue", "")
    if search:
        query = query.filter(Assignment.subject.ilike(f"%{search}%") | Assignment.title.ilike(f"%{search}%"))
    if subject:
        query = query.filter_by(subject=subject)
    if priority in {"low", "medium", "high"}:
        query = query.filter_by(priority=priority)
    if status in {"pending", "in progress", "submitted"}:
        query = query.filter_by(status=status)
    if overdue == "1":
        query = query.filter(Assignment.due_date < date.today(), Assignment.status != "submitted")
    assignments = query.order_by(Assignment.due_date).all()
    subjects = [item[0] for item in db.session.query(Assignment.subject).filter_by(user_id=session["user_id"]).distinct().order_by(Assignment.subject).all()]
    return render_template("assignments/index.html", assignments=assignments, subjects=subjects, search=search, subject=subject, priority=priority, status=status, overdue=overdue, total_assignments=len(all_assignments), pending_count=sum(item.status == "pending" for item in all_assignments), in_progress_count=sum(item.status == "in progress" for item in all_assignments), submitted_count=sum(item.status == "submitted" for item in all_assignments), overdue_count=sum(item.status != "submitted" and item.due_date < date.today() for item in all_assignments))


@exams_bp.route("/assignments/add", methods=["GET", "POST"])
@login_required
def add_assignment():
    if request.method == "POST":
        assignment = _assignment_form()
        if assignment:
            db.session.add(assignment)
            db.session.commit()
            flash("Assignment added.", "success")
            return redirect(url_for("exams.list_assignments"))
    return render_template("assignments/form.html", assignment=None)


@exams_bp.route("/assignments/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_assignment(id):
    assignment = student_query(Assignment).filter_by(id=id).first_or_404()
    if request.method == "POST" and _assignment_form(assignment):
        db.session.commit()
        flash("Assignment updated.", "success")
        return redirect(url_for("exams.list_assignments"))
    return render_template("assignments/form.html", assignment=assignment)


@exams_bp.post("/assignments/delete/<int:id>")
@login_required
def delete_assignment(id):
    assignment = student_query(Assignment).filter_by(id=id).first_or_404()
    db.session.delete(assignment)
    db.session.commit()
    flash("Assignment deleted.", "success")
    return redirect(url_for("exams.list_assignments"))
