from flask import Blueprint, flash, redirect, render_template, request, url_for, session
from common import db, login_required, parse_date, student_query
from models import StudySession
study_bp = Blueprint("study", __name__)
@study_bp.route("/study")
@login_required
def list_study():
    subject = request.args.get("subject", "").strip(); query = student_query(StudySession)
    if subject: query = query.filter(StudySession.subject.ilike(f"%{subject}%"))
    records = query.order_by(StudySession.study_date.desc()).all()
    return render_template("study/list.html", records=records, subject=subject, total_hours=sum(item.duration for item in records))
@study_bp.route("/study/add", methods=["GET", "POST"])
@login_required
def add_study():
    if request.method == "POST":
        study_date = parse_date(request.form.get("study_date")); duration = request.form.get("duration", type=float)
        if not request.form.get("subject", "").strip() or not study_date or not duration or duration <= 0: flash("Enter a subject, valid date, and positive duration.", "danger")
        else:
            db.session.add(StudySession(user_id=session["user_id"], subject=request.form["subject"].strip(), topic=request.form.get("topic", "").strip(), duration=duration, study_date=study_date, notes=request.form.get("notes", "").strip())); db.session.commit(); flash("Study session recorded.", "success"); return redirect(url_for("study.list_study"))
    return render_template("study/form.html")
@study_bp.post("/study/<int:record_id>/delete")
@login_required
def delete_study(record_id):
    record = student_query(StudySession).filter_by(id=record_id).first_or_404(); db.session.delete(record); db.session.commit(); return redirect(url_for("study.list_study"))
