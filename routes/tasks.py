from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from common import db, login_required, parse_date, student_query
from models import Task

tasks_bp = Blueprint("tasks", __name__)

def task_form(task=None):
    if request.method == "POST":
        title = request.form.get("title", "").strip(); due = parse_date(request.form.get("due_date"))
        priority = request.form.get("priority", "medium").lower()
        status = request.form.get("status", "pending").lower()
        if not title or not due: flash("Title and a valid due date are required.", "danger"); return None
        if priority not in {"high", "medium", "low"} or status not in {"pending", "completed"}: flash("Choose a valid task priority and status.", "danger"); return None
        if task is None: task = Task(user_id=session["user_id"])
        task.title = title; task.description = request.form.get("description", "").strip(); task.priority = priority; task.due_date = due; task.status = status
        return task
    return task

@tasks_bp.route("/tasks")
@login_required
def list_tasks():
    query = student_query(Task)
    search = request.args.get("q", "").strip(); status = request.args.get("status", ""); priority = request.args.get("priority", "").lower()
    if search: query = query.filter(Task.title.ilike(f"%{search}%"))
    if status: query = query.filter_by(status=status)
    if priority: query = query.filter_by(priority=priority)
    return render_template("tasks/list.html", tasks=query.order_by(Task.due_date).all(), search=search, status=status, priority=priority)

@tasks_bp.route("/tasks/add", methods=["GET", "POST"])
@login_required
def add_task():
    if request.method == "POST":
        task = task_form()
        if task: db.session.add(task); db.session.commit(); flash("Task added.", "success"); return redirect(url_for("tasks.list_tasks"))
    return render_template("tasks/form.html", task=None)

@tasks_bp.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    task = student_query(Task).filter_by(id=task_id).first_or_404()
    if request.method == "POST" and task_form(task): db.session.commit(); flash("Task updated.", "success"); return redirect(url_for("tasks.list_tasks"))
    return render_template("tasks/form.html", task=task)

@tasks_bp.route("/tasks/<int:task_id>/complete", methods=["POST"])
@login_required
def complete_task(task_id):
    task = student_query(Task).filter_by(id=task_id).first_or_404(); task.status = "completed" if task.status != "completed" else "pending"; db.session.commit(); return redirect(request.referrer or url_for("tasks.list_tasks"))

@tasks_bp.route("/tasks/<int:task_id>/delete", methods=["POST"])
@login_required
def delete_task(task_id):
    task = student_query(Task).filter_by(id=task_id).first_or_404(); db.session.delete(task); db.session.commit(); flash("Task deleted.", "success"); return redirect(url_for("tasks.list_tasks"))
