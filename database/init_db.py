from datetime import date, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app, db
from models import Attendance, Expense, Goal, StudySession, Task, User

with app.app_context():
    db.create_all()
    if not User.query.filter_by(email="admin@smarttracker.local").first():
        admin=User(name="System Admin",email="admin@smarttracker.local",course="Administration",semester="N/A",role="admin"); admin.set_password("Admin@12345"); db.session.add(admin)
    student=User.query.filter_by(email="student@smarttracker.local").first()
    if not student:
        student=User(name="Aarav Mehta",email="student@smarttracker.local",course="BSc Computer Science",semester="Semester 6"); student.set_password("Student@12345"); db.session.add(student); db.session.flush()
        db.session.add_all([Task(user_id=student.id,title="Finish database normalization",description="Review 3NF examples",priority="high",due_date=date.today()+timedelta(days=2)),Task(user_id=student.id,title="Submit operating systems lab",priority="medium",due_date=date.today()+timedelta(days=5)),Task(user_id=student.id,title="Read software testing chapter",priority="low",due_date=date.today()-timedelta(days=1))])
        db.session.add_all([StudySession(user_id=student.id,subject="Database Systems",topic="Indexes",duration=1.5,study_date=date.today()),StudySession(user_id=student.id,subject="Web Technology",topic="Flask",duration=2,study_date=date.today()-timedelta(days=1)),StudySession(user_id=student.id,subject="Data Structures",topic="Graphs",duration=1,study_date=date.today()-timedelta(days=2))])
        db.session.add_all([Attendance(user_id=student.id,subject="Database Systems",total_classes=20,attended_classes=17),Attendance(user_id=student.id,subject="Web Technology",total_classes=18,attended_classes=12)])
        db.session.add_all([Expense(user_id=student.id,amount=280,category="Food",description="Campus lunch",expense_date=date.today()),Expense(user_id=student.id,amount=650,category="Education",description="Reference book",expense_date=date.today()-timedelta(days=4))])
        db.session.add_all([Goal(user_id=student.id,title="Complete final year project",description="Ship a polished tracker",target_date=date.today()+timedelta(days=40),progress=68),Goal(user_id=student.id,title="Reach 80% attendance",target_date=date.today()+timedelta(days=60),progress=42)])
    db.session.commit(); print("Database ready. Demo accounts created if missing.")
