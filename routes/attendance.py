from flask import Blueprint, flash, redirect, render_template, request, url_for, session
from common import db, login_required, student_query
from models import Attendance
attendance_bp = Blueprint("attendance", __name__)
@attendance_bp.route("/attendance")
@login_required
def list_attendance(): return render_template("attendance/list.html", records=student_query(Attendance).order_by(Attendance.subject).all())
@attendance_bp.route("/attendance/add", methods=["GET", "POST"])
@login_required
def add_attendance():
    if request.method == "POST":
        total = request.form.get("total_classes", type=int); attended = request.form.get("attended_classes", type=int)
        if not request.form.get("subject", "").strip() or not total or total < 1 or attended is None or attended < 0 or attended > total: flash("Enter valid class totals and attendance.", "danger")
        else:
            db.session.add(Attendance(user_id=session["user_id"], subject=request.form["subject"].strip(), total_classes=total, attended_classes=attended)); db.session.commit(); flash("Attendance saved.", "success"); return redirect(url_for("attendance.list_attendance"))
    return render_template("attendance/form.html")
@attendance_bp.post("/attendance/<int:record_id>/delete")
@login_required
def delete_attendance(record_id):
    record = student_query(Attendance).filter_by(id=record_id).first_or_404(); db.session.delete(record); db.session.commit(); return redirect(url_for("attendance.list_attendance"))
