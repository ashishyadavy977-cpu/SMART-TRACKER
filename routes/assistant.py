from flask import Blueprint, jsonify, render_template, request, session

from ai_assistant import ask_assistant
from common import login_required
from models import User
from common import db

assistant_bp = Blueprint("assistant", __name__)


@assistant_bp.get("/assistant")
@login_required
def assistant_page():
    user = db.session.get(User, session["user_id"])
    return render_template("assistant.html", user=user)


@assistant_bp.post("/assistant/ask")
@login_required
def assistant_ask():
    question = request.form.get("message", "").strip() if not request.is_json else str(request.json.get("message", "")).strip()
    if not question:
        message = "Please enter a question first."
        return jsonify({"answer": message, "ok": False}), 400
    if len(question) > 1200:
        return jsonify({"answer": "Please keep your question under 1200 characters.", "ok": False}), 400
    user = db.session.get(User, session["user_id"])
    answer, powered_by_ai = ask_assistant(question, user.name)
    return jsonify({"answer": answer, "powered_by_ai": powered_by_ai, "ok": True})
