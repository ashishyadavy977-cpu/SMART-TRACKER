from datetime import date, datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    course = db.Column(db.String(120), nullable=False)
    semester = db.Column(db.String(30), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")
    status = db.Column(db.String(20), nullable=False, default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    tasks = db.relationship("Task", backref="user", cascade="all, delete-orphan")
    study_sessions = db.relationship("StudySession", backref="user", cascade="all, delete-orphan")
    attendance = db.relationship("Attendance", backref="user", cascade="all, delete-orphan")
    expenses = db.relationship("Expense", backref="user", cascade="all, delete-orphan")
    goals = db.relationship("Goal", backref="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.String(20), default="medium", nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default="pending", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class StudySession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    subject = db.Column(db.String(120), nullable=False)
    topic = db.Column(db.String(180))
    duration = db.Column(db.Float, nullable=False)
    study_date = db.Column(db.Date, default=date.today, nullable=False)
    notes = db.Column(db.Text)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    subject = db.Column(db.String(120), nullable=False)
    total_classes = db.Column(db.Integer, nullable=False)
    attended_classes = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @property
    def absent_classes(self):
        return max(self.total_classes - self.attended_classes, 0)

    @property
    def percentage(self):
        return round((self.attended_classes / self.total_classes) * 100, 1) if self.total_classes else 0

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(30), nullable=False)
    description = db.Column(db.String(240))
    expense_date = db.Column(db.Date, default=date.today, nullable=False)

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text)
    target_date = db.Column(db.Date, nullable=False)
    progress = db.Column(db.Integer, default=0, nullable=False)
    status = db.Column(db.String(20), default="active", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
