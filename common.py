from datetime import datetime
from functools import wraps
from flask import flash, redirect, request, session, url_for
from models import User
from models.models import db


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("login", next=request.path))
        user = db.session.get(User, session["user_id"])
        if not user or user.status != "active":
            session.clear()
            flash("Your account is inactive.", "danger")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Administrator access is required.", "danger")
            return redirect(url_for("dashboard"))
        return view(*args, **kwargs)
    return wrapped


def parse_date(value, fallback=None):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return fallback


def student_query(model):
    return model.query.filter_by(user_id=session["user_id"])
