from datetime import date, timedelta

from flask import Blueprint, jsonify, render_template, request, session

from analytics_service import build_analytics
from common import login_required, parse_date
from services import record_score

analytics_bp = Blueprint("analytics", __name__)


def _analytics_range():
    today = date.today()
    preset = request.args.get("range", "last30")
    if preset == "today":
        return today, today
    if preset == "week":
        return today - timedelta(days=today.weekday()), today
    if preset == "month":
        return today.replace(day=1), today
    if preset == "last30":
        return today - timedelta(days=29), today
    if preset == "custom":
        start = parse_date(request.args.get("start"))
        end = parse_date(request.args.get("end"))
        if start and end and start <= end and (end - start).days <= 366:
            return start, end
    raise ValueError("Choose a valid date range of one year or less.")


def _payload():
    start, end = _analytics_range()
    return build_analytics(session["user_id"], start, end)


@analytics_bp.get("/analytics")
@login_required
def analytics_page():
    record_score(session["user_id"])
    return render_template("analytics.html")


@analytics_bp.get("/api/analytics/dashboard")
@login_required
def analytics_dashboard_api():
    try:
        return jsonify(_payload())
    except ValueError as error:
        return jsonify({"error": str(error)}), 400


@analytics_bp.get("/api/analytics/<section>")
@login_required
def analytics_section_api(section):
    allowed = {"summary", "study", "tasks", "attendance", "expenses", "goals", "exams", "productivity"}
    if section not in allowed:
        return jsonify({"error": "Analytics section not found."}), 404
    try:
        return jsonify(_payload()[section])
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
