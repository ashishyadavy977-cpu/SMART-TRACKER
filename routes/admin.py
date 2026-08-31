from flask import Blueprint, flash, redirect, render_template, url_for
from sqlalchemy import func
from common import admin_required, db
from models import Attendance, Expense, Goal, StudySession, Task, User
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
@admin_bp.route("/login")
def admin_login(): return redirect(url_for("login"))
@admin_bp.route("/dashboard")
@admin_required
def admin_dashboard():
    students = User.query.filter_by(role="student").all(); tasks=Task.query.all(); studies=StudySession.query.all(); attendance=Attendance.query.all(); expenses=Expense.query.all()
    total=sum(x.total_classes for x in attendance); attended=sum(x.attended_classes for x in attendance)
    stats={"students":len(students),"tasks":len(tasks),"completed":sum(x.status=="completed" for x in tasks),"study_hours":round(sum(x.duration for x in studies),1),"attendance":round(attended/total*100,1) if total else 0,"expenses":round(sum(x.amount for x in expenses),2),"active":sum(x.status=="active" for x in students)}
    return render_template("admin/dashboard.html", stats=stats)
@admin_bp.route("/users")
@admin_required
def users(): return render_template("admin/users.html", users=User.query.filter_by(role="student").order_by(User.created_at.desc()).all())
@admin_bp.post("/users/<int:user_id>/toggle")
@admin_required
def toggle_user(user_id):
    user=User.query.filter_by(id=user_id, role="student").first_or_404(); user.status="inactive" if user.status=="active" else "active"; db.session.commit(); flash("User status updated.", "success"); return redirect(url_for("admin.users"))

@admin_bp.post("/<record_type>/<int:record_id>/delete")
@admin_required
def delete_record(record_type, record_id):
    models = {"tasks": Task, "study": StudySession, "attendance": Attendance, "expenses": Expense, "goals": Goal}
    model = models.get(record_type)
    if model is None:
        return redirect(url_for("admin.admin_dashboard"))
    record = model.query.filter_by(id=record_id).first_or_404()
    db.session.delete(record); db.session.commit(); flash("Record deleted.", "success")
    return redirect(url_for(f"admin.{record_type}"))

def admin_records(model, template): return render_template(template, records=model.query.order_by(model.id.desc()).all())
for endpoint, path, model, template in [("tasks","tasks",Task,"admin/records.html"),("study","study",StudySession,"admin/records.html"),("attendance","attendance",Attendance,"admin/records.html"),("expenses","expenses",Expense,"admin/records.html"),("goals","goals",Goal,"admin/records.html")]:
    admin_bp.add_url_rule(f"/{path}", endpoint, lambda model=model, template=template: admin_records(model, template), methods=["GET"])
