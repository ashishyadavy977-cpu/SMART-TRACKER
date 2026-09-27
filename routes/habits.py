from calendar import monthrange
from datetime import date, timedelta

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from common import db, login_required, student_query
from models import Habit, HabitCompletion

habits_bp = Blueprint("habits", __name__)


def _habit_form(habit=None):
    name = request.form.get("name", "").strip()
    if not name:
        flash("A habit name is required.", "danger")
        return None
    if habit is None:
        habit = Habit(user_id=session["user_id"])
    habit.name = name
    habit.description = request.form.get("description", "").strip()
    habit.color = request.form.get("color", "lime")
    return habit


@habits_bp.get("/habits")
@login_required
def list_habits():
    today = date.today()
    view = request.args.get("view", "week") if request.args.get("view") in {"week", "month"} else "week"
    start = today - timedelta(days=today.weekday()) if view == "week" else today.replace(day=1)
    end = start + timedelta(days=6) if view == "week" else today.replace(day=monthrange(today.year, today.month)[1])
    habits = student_query(Habit).order_by(Habit.created_at.desc()).all()
    return render_template("habits/index.html", habits=habits, today=today, start=start, end=end, view=view, days=[start + timedelta(days=index) for index in range((end - start).days + 1)])


@habits_bp.route("/habits/add", methods=["GET", "POST"])
@login_required
def add_habit():
    if request.method == "POST":
        habit = _habit_form()
        if habit:
            db.session.add(habit)
            db.session.commit()
            flash("Habit created.", "success")
            return redirect(url_for("habits.list_habits"))
    return render_template("habits/form.html", habit=None)


@habits_bp.route("/habits/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_habit(id):
    habit = student_query(Habit).filter_by(id=id).first_or_404()
    if request.method == "POST" and _habit_form(habit):
        db.session.commit()
        flash("Habit updated.", "success")
        return redirect(url_for("habits.list_habits"))
    return render_template("habits/form.html", habit=habit)


@habits_bp.post("/habits/delete/<int:id>")
@login_required
def delete_habit(id):
    habit = student_query(Habit).filter_by(id=id).first_or_404()
    db.session.delete(habit)
    db.session.commit()
    flash("Habit deleted.", "success")
    return redirect(url_for("habits.list_habits"))


@habits_bp.post("/habits/<int:id>/toggle")
@login_required
def toggle_habit(id):
    habit = student_query(Habit).filter_by(id=id).first_or_404()
    completed_date = request.form.get("completed_date", "")
    try:
        completed_date = date.fromisoformat(completed_date)
    except ValueError:
        flash("Choose a valid date.", "danger")
        return redirect(url_for("habits.list_habits"))
    completion = HabitCompletion.query.filter_by(habit_id=habit.id, completed_date=completed_date).first()
    if completion:
        db.session.delete(completion)
    else:
        db.session.add(HabitCompletion(habit_id=habit.id, completed_date=completed_date))
    db.session.commit()
    return redirect(request.referrer or url_for("habits.list_habits"))