import json

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from common import db, login_required, student_query
from models import QuizAttempt

quiz_bp = Blueprint("quiz", __name__)


def generate_questions(subject, topic, difficulty, count):
    topic = topic or subject
    bank = [
        {"question": f"Which statement best describes {topic} in {subject}?", "options": [f"It is a core concept of {subject}", "It is unrelated to the subject", "It is only a grading method", "It is a file format"], "answer": 0},
        {"question": f"What is a useful first step when studying {topic}?", "options": ["Define the key terms", "Skip all examples", "Memorize without context", "Avoid practice"], "answer": 0},
        {"question": f"Which approach usually improves understanding of {topic}?", "options": ["Apply it to a worked example", "Read only the title", "Ignore feedback", "Study without reviewing"], "answer": 0},
        {"question": f"Which evidence best shows progress in {topic}?", "options": ["Solving a new problem correctly", "Opening a textbook", "Changing the font", "Skipping a question"], "answer": 0},
        {"question": f"What should you do after making an error in {topic}?", "options": ["Review the reasoning and retry", "Delete the notes", "Avoid the topic", "Guess again without checking"], "answer": 0},
    ]
    if difficulty == "hard":
        bank[0]["options"] = [f"It connects principles of {subject} to new problems", "It is only a definition", "It cannot be tested", "It replaces all practice"]
    elif difficulty == "easy":
        bank[0]["options"] = [f"It is a basic area of {subject}", "It is a password", "It is a calendar view", "It is an expense"]
    return [{**item, "id": index} for index, item in enumerate((bank * ((count + len(bank) - 1) // len(bank)))[:count])]


@quiz_bp.get("/quiz")
@login_required
def quiz_page():
    history = student_query(QuizAttempt).order_by(QuizAttempt.created_at.desc()).limit(10).all()
    questions = session.get("quiz_questions")
    return render_template("quiz.html", questions=questions, quiz_subject=session.get("quiz_subject", ""), quiz_topic=session.get("quiz_topic", ""), quiz_difficulty=session.get("quiz_difficulty", "medium"), history=history, result=None)


@quiz_bp.post("/quiz/generate")
@login_required
def generate_quiz():
    subject = request.form.get("subject", "").strip(); topic = request.form.get("topic", "").strip(); difficulty = request.form.get("difficulty", "medium")
    count = request.form.get("count", type=int) or 5
    if not subject or difficulty not in {"easy", "medium", "hard"} or not 1 <= count <= 10:
        flash("Choose a subject, valid difficulty, and 1 to 10 questions.", "danger")
        return redirect(url_for("quiz.quiz_page"))
    session["quiz_questions"] = generate_questions(subject, topic, difficulty, count)
    session["quiz_subject"] = subject; session["quiz_topic"] = topic; session["quiz_difficulty"] = difficulty
    return redirect(url_for("quiz.quiz_page"))


@quiz_bp.post("/quiz/submit")
@login_required
def submit_quiz():
    questions = session.get("quiz_questions") or []
    if not questions:
        flash("Generate a quiz before submitting.", "warning")
        return redirect(url_for("quiz.quiz_page"))
    answers = [request.form.get(f"answer_{item['id']}", "") for item in questions]
    score = sum(str(item["answer"]) == answer for item, answer in zip(questions, answers))
    total = len(questions); percentage = round(score / total * 100, 1) if total else 0
    attempt = QuizAttempt(user_id=session["user_id"], subject=session.get("quiz_subject", ""), topic=session.get("quiz_topic", ""), difficulty=session.get("quiz_difficulty", "medium"), questions=json.dumps(questions), answers=json.dumps(answers), score=score, total_questions=total, percentage=percentage)
    db.session.add(attempt); db.session.commit()
    result = {"score": score, "total": total, "percentage": percentage, "answers": answers, "questions": questions}
    session.pop("quiz_questions", None)
    history = student_query(QuizAttempt).order_by(QuizAttempt.created_at.desc()).limit(10).all()
    return render_template("quiz.html", questions=None, quiz_subject=attempt.subject, quiz_topic=attempt.topic, quiz_difficulty=attempt.difficulty, history=history, result=result)
