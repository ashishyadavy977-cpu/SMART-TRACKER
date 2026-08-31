from flask import Blueprint, flash, redirect, render_template, request, url_for, session
from common import db, login_required, parse_date, student_query
from models import Goal
goals_bp = Blueprint("goals", __name__)
@goals_bp.route("/goals")
@login_required
def list_goals(): return render_template("goals/list.html", goals=student_query(Goal).order_by(Goal.target_date).all())
@goals_bp.route("/goals/add", methods=["GET", "POST"])
@login_required
def add_goal():
    if request.method == "POST":
        progress = request.form.get("progress", type=int, default=0); target = parse_date(request.form.get("target_date"))
        if not request.form.get("title", "").strip() or not target or progress < 0 or progress > 100: flash("Enter a title, valid target date, and progress from 0 to 100.", "danger")
        else:
            db.session.add(Goal(user_id=session["user_id"], title=request.form["title"].strip(), description=request.form.get("description", "").strip(), target_date=target, progress=progress, status="completed" if progress == 100 else "active")); db.session.commit(); flash("Goal created.", "success"); return redirect(url_for("goals.list_goals"))
    return render_template("goals/form.html")
@goals_bp.route("/goals/<int:goal_id>/edit", methods=["GET", "POST"])
@login_required
def edit_goal(goal_id):
    goal = student_query(Goal).filter_by(id=goal_id).first_or_404()
    if request.method == "POST":
        progress = request.form.get("progress", type=int); target = parse_date(request.form.get("target_date"))
        if target and progress is not None and 0 <= progress <= 100: goal.title=request.form["title"].strip(); goal.description=request.form.get("description", "").strip(); goal.target_date=target; goal.progress=progress; goal.status="completed" if progress == 100 else "active"; db.session.commit(); flash("Goal updated.", "success"); return redirect(url_for("goals.list_goals"))
        flash("Check the goal values.", "danger")
    return render_template("goals/form.html", goal=goal)
@goals_bp.post("/goals/<int:goal_id>/delete")
@login_required
def delete_goal(goal_id):
    goal = student_query(Goal).filter_by(id=goal_id).first_or_404(); db.session.delete(goal); db.session.commit(); return redirect(url_for("goals.list_goals"))
