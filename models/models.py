import json
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
    bio = db.Column(db.Text)
    subjects = db.Column(db.Text)
    preferences = db.Column(db.Text)
    role = db.Column(db.String(20), nullable=False, default="student")
    status = db.Column(db.String(20), nullable=False, default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    tasks = db.relationship("Task", backref="user", cascade="all, delete-orphan")
    study_sessions = db.relationship("StudySession", backref="user", cascade="all, delete-orphan")
    attendance = db.relationship("Attendance", backref="user", cascade="all, delete-orphan")
    expenses = db.relationship("Expense", backref="user", cascade="all, delete-orphan")
    goals = db.relationship("Goal", backref="user", cascade="all, delete-orphan")
    exams = db.relationship("Exam", backref="user", cascade="all, delete-orphan")
    assignments = db.relationship("Assignment", backref="user", cascade="all, delete-orphan")
    habits = db.relationship("Habit", backref="user", cascade="all, delete-orphan")
    timetables = db.relationship("Timetable", backref="user", cascade="all, delete-orphan")
    notes = db.relationship("Note", backref="user", cascade="all, delete-orphan")
    profile = db.relationship("UserProfile", backref="user", uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    photo_filename = db.Column(db.String(255))

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(180), nullable=False)
    subject = db.Column(db.String(120))
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

class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    subject = db.Column(db.String(120), nullable=False)
    exam_name = db.Column(db.String(180), nullable=False)
    exam_date = db.Column(db.Date, nullable=False, index=True)
    exam_time = db.Column(db.Time)
    total_marks = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default="upcoming", nullable=False)
    priority = db.Column(db.String(20), default="medium", nullable=False)
    syllabus = db.Column(db.Text)
    topics = db.Column(db.Text, default="[]", nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @property
    def topic_items(self):
        try:
            items = json.loads(self.topics or "[]")
            return items if isinstance(items, list) else []
        except (TypeError, ValueError):
            return []

    @property
    def preparation_percentage(self):
        items = self.topic_items
        return round(sum(bool(item.get("completed")) for item in items) / len(items) * 100) if items else 0

    def set_topics(self, topic_names):
        existing = {item.get("name"): bool(item.get("completed")) for item in self.topic_items if item.get("name")}
        self.topics = json.dumps([{"name": name, "completed": existing.get(name, False)} for name in topic_names if name])

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    subject = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date, nullable=False, index=True)
    priority = db.Column(db.String(20), default="medium", nullable=False)
    status = db.Column(db.String(20), default="pending", nullable=False)
    file_name = db.Column(db.String(255))
    original_file_name = db.Column(db.String(255))
    file_type = db.Column(db.String(20))
    file_size = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    name = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(20), default="lime", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completions = db.relationship("HabitCompletion", backref="habit", cascade="all, delete-orphan")

    def completion_dates(self):
        return {item.completed_date for item in self.completions}

    def current_streak(self, today=None):
        cursor = today or date.today()
        dates = self.completion_dates()
        streak = 0
        while cursor in dates:
            streak += 1
            cursor = cursor.fromordinal(cursor.toordinal() - 1)
        return streak

    def longest_streak(self):
        dates = sorted(self.completion_dates())
        longest = current = 0
        previous = None
        for item in dates:
            current = current + 1 if previous and (item - previous).days == 1 else 1
            longest = max(longest, current)
            previous = item
        return longest

    def completion_percentage(self, start_date, end_date):
        total_days = max((end_date - start_date).days + 1, 1)
        completed = sum(start_date <= item <= end_date for item in self.completion_dates())
        return round(completed / total_days * 100, 1)


class HabitCompletion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey("habit.id"), nullable=False, index=True)
    completed_date = db.Column(db.Date, nullable=False, index=True)
    __table_args__ = (db.UniqueConstraint("habit_id", "completed_date", name="unique_habit_day"),)

class Timetable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    day = db.Column(db.String(12), nullable=False, index=True)
    subject = db.Column(db.String(120), nullable=False)
    faculty = db.Column(db.String(120))
    room = db.Column(db.String(60))
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    subject = db.Column(db.String(120), nullable=False, index=True)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(20), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    is_favorite = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    title = db.Column(db.String(160), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(30), default="info", nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user = db.relationship("User", backref=db.backref("notifications", cascade="all, delete-orphan"))

class StudyTarget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    subject = db.Column(db.String(120), nullable=False)
    target_hours = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user = db.relationship("User", backref=db.backref("study_targets", cascade="all, delete-orphan"))

class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    badge_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(240), nullable=False)
    points = db.Column(db.Integer, default=0, nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user = db.relationship("User", backref=db.backref("achievements", cascade="all, delete-orphan"))

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True)
    monthly_amount = db.Column(db.Float, nullable=False, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    user = db.relationship("User", backref=db.backref("budget", uselist=False, cascade="all, delete-orphan"))

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    message = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default="normal", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)

class ProductivityScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    score = db.Column(db.Integer, nullable=False)
    recorded_date = db.Column(db.Date, default=date.today, nullable=False)
    user = db.relationship("User", backref=db.backref("productivity_scores", cascade="all, delete-orphan"))


class FocusSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    mode = db.Column(db.String(20), nullable=False, default="focus")
    duration_minutes = db.Column(db.Integer, nullable=False)
    subject = db.Column(db.String(120))
    task_id = db.Column(db.Integer, db.ForeignKey("task.id"))
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignment.id"))
    goal_id = db.Column(db.Integer, db.ForeignKey("goal.id"))
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), nullable=False, default="completed")
    user = db.relationship("User", backref=db.backref("focus_sessions", cascade="all, delete-orphan"))


class CalendarEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    title = db.Column(db.String(180), nullable=False)
    event_date = db.Column(db.Date, nullable=False, index=True)
    event_time = db.Column(db.Time)
    event_type = db.Column(db.String(30), nullable=False, default="reminder")
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user = db.relationship("User", backref=db.backref("calendar_events", cascade="all, delete-orphan"))


class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    subject = db.Column(db.String(120), nullable=False)
    topic = db.Column(db.String(180))
    difficulty = db.Column(db.String(20), nullable=False, default="medium")
    questions = db.Column(db.Text, nullable=False)
    answers = db.Column(db.Text)
    score = db.Column(db.Integer, nullable=False, default=0)
    total_questions = db.Column(db.Integer, nullable=False, default=0)
    percentage = db.Column(db.Float, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user = db.relationship("User", backref=db.backref("quiz_attempts", cascade="all, delete-orphan"))
