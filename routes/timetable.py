from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy.exc import SQLAlchemyError

from common import db, login_required, student_query
from models import Timetable


timetable_bp = Blueprint("timetable", __name__)
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _parse_time(value):
    try:
        return datetime.strptime(value, "%H:%M").time()
    except (TypeError, ValueError):
        return None


def _timetable_form(record=None):
    day = request.form.get("day", "").strip().title()
    subject = request.form.get("subject", "").strip()
    start_time = _parse_time(request.form.get("start_time"))
    end_time = _parse_time(request.form.get("end_time"))
    if day not in DAYS or not subject or not start_time or not end_time:
        flash("Day, subject, and valid start and end times are required.", "danger")
        return None
    if start_time >= end_time:
        flash("End time must be after start time.", "danger")
        return None
    record = record or Timetable(user_id=session["user_id"])
    record.day = day
    record.subject = subject
    record.faculty = request.form.get("faculty", "").strip()
    record.room = request.form.get("room", "").strip()
    record.start_time = start_time
    record.end_time = end_time
    return record


@timetable_bp.get("/timetable")
@login_required
def list_timetable():
    records = student_query(Timetable).order_by(Timetable.start_time).all()
    weekly = {day: [record for record in records if record.day == day] for day in DAYS}
    return render_template("timetable/index.html", weekly=weekly, days=DAYS, today_name=datetime.today().strftime("%A"))


@timetable_bp.route("/timetable/add", methods=["GET", "POST"])
@login_required
def add_timetable():
    if request.method == "POST":
        record = _timetable_form()
        if record:
            try:
                db.session.add(record)
                db.session.commit()
                flash("Class added to your timetable.", "success")
                return redirect(url_for("timetable.list_timetable"))
            except SQLAlchemyError:
                db.session.rollback()
                flash("The timetable class could not be saved.", "danger")
    return render_template("timetable/form.html", timetable=None, days=DAYS)


@timetable_bp.route("/timetable/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_timetable(id):
    record = student_query(Timetable).filter_by(id=id).first_or_404()
    if request.method == "POST" and _timetable_form(record):
        try:
            db.session.commit()
            flash("Timetable class updated.", "success")
            return redirect(url_for("timetable.list_timetable"))
        except SQLAlchemyError:
            db.session.rollback()
            flash("The timetable class could not be updated.", "danger")
    return render_template("timetable/form.html", timetable=record, days=DAYS)


@timetable_bp.post("/timetable/delete/<int:id>")
@login_required
def delete_timetable(id):
    record = student_query(Timetable).filter_by(id=id).first_or_404()
    try:
        db.session.delete(record)
        db.session.commit()
        flash("Timetable class deleted.", "success")
    except SQLAlchemyError:
        db.session.rollback()
        flash("The timetable class could not be deleted.", "danger")
    return redirect(url_for("timetable.list_timetable"))
