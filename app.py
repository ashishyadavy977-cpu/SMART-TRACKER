from datetime import date, timedelta
from flask import Flask, flash, redirect, render_template, request, session, url_for
from config import Config
from models import Attendance, Expense, Goal, StudySession, Task, User
from common import db, login_required, parse_date, student_query

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

@app.context_processor
def inject_globals():
    return {"today": date.today(), "current_user": db.session.get(User, session["user_id"]) if session.get("user_id") else None}

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
    return render_template("dashboard.html", user=user, tasks=tasks, studies=studies, attendance=attendance, expenses=expenses, goals=goals, today_hours=sum(item.duration for item in studies if item.study_date == date.today()), monthly_expenses=monthly_expenses, attendance_pct=round(attended / total_classes * 100, 1) if total_classes else 0, goal_pct=round(completed_goals), recommendations=recommendations)

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = current_user()
    if request.method == "POST":
        user.name = request.form.get("name", user.name).strip(); user.course = request.form.get("course", user.course).strip(); user.semester = request.form.get("semester", user.semester).strip(); db.session.commit(); flash("Profile updated.", "success"); return redirect(url_for("profile"))
    return render_template("profile.html", user=user)

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
app.register_blueprint(tasks_bp)
app.register_blueprint(study_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(expenses_bp)
app.register_blueprint(goals_bp)
app.register_blueprint(admin_bp)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
