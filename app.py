from datetime import date, datetime, timedelta
import json
from flask import Flask, flash, redirect, make_response, render_template, request, session, url_for
from werkzeug.utils import secure_filename
from pathlib import Path
from config import Config
from models import Announcement, Attendance, Expense, Goal, Notification, StudySession, Task, User, UserProfile
from common import db, login_required, parse_date, student_query
from services import record_score, refresh_notifications, score_label, streaks

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

@app.context_processor
def inject_globals():
    user = db.session.get(User, session["user_id"]) if session.get("user_id") else None
    unread = Notification.query.filter_by(user_id=user.id, is_read=False).count() if user else 0
    return {"today": date.today(), "current_user": user, "unread_notifications": unread}

def current_user():
    return db.session.get(User, session["user_id"])

@app.route("/")
def index():
    return redirect(url_for("dashboard")) if session.get("user_id") else render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(request.form.get("password", "")) and user.status == "active":
            session.clear(); session.update(user_id=user.id, role=user.role)
            return redirect(request.args.get("next") or (url_for("admin.admin_dashboard") if user.role == "admin" else url_for("dashboard")))
        flash("Invalid credentials or inactive account.", "danger")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name, email, password = request.form.get("name", "").strip(), request.form.get("email", "").strip().lower(), request.form.get("password", "")
        if not name or len(password) < 8 or not request.form.get("course") or not request.form.get("semester"):
            flash("Complete every field. Passwords must be at least 8 characters.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("That email is already registered.", "warning")
        else:
            user = User(name=name, email=email, course=request.form["course"].strip(), semester=request.form["semester"].strip())
            user.set_password(password); db.session.add(user); db.session.commit()
            flash("Account created. You can now sign in.", "success"); return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear(); flash("You have been signed out.", "success"); return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user(); tasks = student_query(Task).all(); studies = student_query(StudySession).all(); attendance = student_query(Attendance).all(); expenses = student_query(Expense).all(); goals = student_query(Goal).all()
    month_start = date.today().replace(day=1)
    total_classes = sum(item.total_classes for item in attendance); attended = sum(item.attended_classes for item in attendance)
    monthly_expenses = sum(item.amount for item in expenses if item.expense_date >= month_start)
    completed_goals = sum(item.progress for item in goals) / len(goals) if goals else 0
    recommendations = []
    if total_classes and attended / total_classes < .75: recommendations.append("Your attendance is below 75%. Try attending upcoming classes regularly.")
    if len([item for item in tasks if item.status != "completed"]) >= 3: recommendations.append("You have several pending tasks. Prioritize tasks with the nearest deadline.")
    if sum(item.duration for item in studies if item.study_date == date.today()) < 2: recommendations.append("Your study hours are lower than your target. Consider creating a daily study schedule.")
    previous_month = sum(item.amount for item in expenses if month_start - timedelta(days=31) <= item.expense_date < month_start)
    if previous_month and monthly_expenses > previous_month: recommendations.append("Your spending has increased this month. Review your expense categories.")
    refresh_notifications(user.id); score = record_score(user.id)
    return render_template("dashboard.html", user=user, tasks=tasks, studies=studies, attendance=attendance, expenses=expenses, goals=goals, today_hours=sum(item.duration for item in studies if item.study_date == date.today()), monthly_expenses=monthly_expenses, attendance_pct=round(attended / total_classes * 100, 1) if total_classes else 0, goal_pct=round(completed_goals), recommendations=recommendations, productivity_score=score, productivity_label=score_label(score), streaks=streaks(user.id), announcements=Announcement.query.filter(Announcement.expiry_date >= date.today()).order_by(Announcement.created_at.desc()).limit(3).all())

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = current_user()
    if request.method == "POST":
        user.name = request.form.get("name", user.name).strip(); user.course = request.form.get("course", user.course).strip(); user.semester = request.form.get("semester", user.semester).strip(); db.session.commit(); flash("Profile updated.", "success"); return redirect(url_for("profile"))
    return render_template("profile.html", user=user)

@app.post("/profile/password")
@login_required
def change_password():
    user = current_user()
    if not user.check_password(request.form.get("current_password", "")):
        flash("Current password is incorrect.", "danger")
    elif len(request.form.get("new_password", "")) < 8:
        flash("New password must be at least 8 characters.", "danger")
    elif request.form.get("new_password") != request.form.get("confirm_password"):
        flash("New passwords do not match.", "danger")
    else:
        user.set_password(request.form["new_password"]); db.session.commit(); flash("Password changed successfully.", "success")
    return redirect(url_for("profile"))

@app.post("/profile/photo")
@login_required
def upload_profile_photo():
    photo = request.files.get("photo")
    allowed = {"jpg", "jpeg", "png", "webp"}
    extension = photo.filename.rsplit(".", 1)[-1].lower() if photo and photo.filename and "." in photo.filename else ""
    if not photo or extension not in allowed:
        flash("Upload a JPG, PNG, or WEBP image.", "danger")
        return redirect(url_for("profile"))
    upload_dir = Path(app.static_folder) / "uploads"; upload_dir.mkdir(exist_ok=True)
    filename = f"profile-{session['user_id']}.{extension}"; photo.save(upload_dir / secure_filename(filename))
    profile_record = UserProfile.query.filter_by(user_id=session["user_id"]).first() or UserProfile(user_id=session["user_id"])
    profile_record.photo_filename = filename; db.session.add(profile_record); db.session.commit(); flash("Profile photo updated.", "success")
    return redirect(url_for("profile"))

@app.get("/backup/export")
@login_required
def export_backup():
    user_id = session["user_id"]
    models = {"tasks": Task, "study_sessions": StudySession, "attendance": Attendance, "expenses": Expense, "goals": Goal, "notifications": Notification}
    snapshot = {"version": 1, "exported_at": datetime.utcnow().isoformat(), "records": {}}
    for name, model in models.items():
        snapshot["records"][name] = [{column.name: (field_value.isoformat() if isinstance(field_value, (date, datetime)) else field_value) for column in model.__table__.columns if column.name != "user_id" for field_value in [getattr(record, column.name)]} for record in model.query.filter_by(user_id=user_id).all()]
    response = make_response(json.dumps(snapshot, indent=2), 200)
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    response.headers["Content-Disposition"] = "attachment; filename=smart_tracker_backup.json"
    return response

@app.post("/backup/restore")
@login_required
def restore_backup():
    upload = request.files.get("backup")
    try:
        snapshot = json.loads(upload.read()) if upload else None
        records = snapshot["records"] if snapshot and snapshot.get("version") == 1 else None
        if not isinstance(records, dict): raise ValueError
        models = {"tasks": Task, "study_sessions": StudySession, "attendance": Attendance, "expenses": Expense, "goals": Goal, "notifications": Notification}
        user_id = session["user_id"]
        for name, model in models.items():
            model.query.filter_by(user_id=user_id).delete(synchronize_session=False)
            for item in records.get(name, []):
                values = {column.name: value for column, value in ((column, item.get(column.name)) for column in model.__table__.columns) if column.name not in {"id", "user_id"} and value is not None}
                for column in model.__table__.columns:
                    if column.name in values and column.type.python_type in {date, datetime}:
                        values[column.name] = column.type.python_type.fromisoformat(values[column.name])
                db.session.add(model(user_id=user_id, **values))
        db.session.commit(); flash("Backup restored successfully.", "success")
    except (TypeError, ValueError, KeyError, json.JSONDecodeError):
        db.session.rollback(); flash("The backup file is invalid.", "danger")
    return redirect(url_for("profile"))

@app.route("/reports")
@login_required
def reports():
    records = {"tasks": student_query(Task).all(), "studies": student_query(StudySession).all(), "attendance": student_query(Attendance).all(), "expenses": student_query(Expense).all(), "goals": student_query(Goal).all()}
    return render_template("reports.html", **records)

@app.errorhandler(404)
def not_found(error): return render_template("error.html", code=404, message="The page you requested could not be found."), 404
@app.errorhandler(500)
def server_error(error): db.session.rollback(); return render_template("error.html", code=500, message="Something went wrong on the server."), 500

from routes.tasks import tasks_bp
from routes.study import study_bp
from routes.attendance import attendance_bp
from routes.expenses import expenses_bp
from routes.goals import goals_bp
from routes.admin import admin_bp
from routes.smart import smart_bp
app.register_blueprint(tasks_bp)
app.register_blueprint(study_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(expenses_bp)
app.register_blueprint(goals_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(smart_bp)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
