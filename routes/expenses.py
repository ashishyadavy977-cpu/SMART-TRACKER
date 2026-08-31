from flask import Blueprint, flash, redirect, render_template, request, url_for, session
from common import db, login_required, parse_date, student_query
from models import Expense
expenses_bp = Blueprint("expenses", __name__)
@expenses_bp.route("/expenses")
@login_required
def list_expenses():
    category = request.args.get("category", ""); query = student_query(Expense)
    if category: query = query.filter_by(category=category)
    records = query.order_by(Expense.expense_date.desc()).all()
    return render_template("expenses/list.html", records=records, category=category, total=sum(item.amount for item in records))
@expenses_bp.route("/expenses/add", methods=["GET", "POST"])
@login_required
def add_expense():
    if request.method == "POST":
        amount = request.form.get("amount", type=float); expense_date = parse_date(request.form.get("expense_date"))
        if not amount or amount <= 0 or not expense_date: flash("Enter a positive amount and valid date.", "danger")
        else:
            db.session.add(Expense(user_id=session["user_id"], amount=amount, category=request.form.get("category", "Other"), description=request.form.get("description", "").strip(), expense_date=expense_date)); db.session.commit(); flash("Expense added.", "success"); return redirect(url_for("expenses.list_expenses"))
    return render_template("expenses/form.html")
@expenses_bp.post("/expenses/<int:record_id>/delete")
@login_required
def delete_expense(record_id):
    record = student_query(Expense).filter_by(id=record_id).first_or_404(); db.session.delete(record); db.session.commit(); return redirect(url_for("expenses.list_expenses"))
