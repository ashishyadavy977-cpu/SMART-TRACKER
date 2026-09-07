from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, flash, redirect, render_template, request, send_from_directory, session, url_for
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename

from common import db, login_required, student_query
from models import Note


notes_bp = Blueprint("notes", __name__)
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "txt", "png", "jpg", "jpeg"}


def notes_upload_dir():
    directory = Path(current_app.static_folder) / "uploads" / "notes"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def extension_for(filename):
    return filename.rsplit(".", 1)[-1].lower() if filename and "." in filename else ""


def _note_details(note=None):
    title = request.form.get("title", "").strip()
    subject = request.form.get("subject", "").strip()
    if not title or not subject:
        flash("Title and subject are required.", "danger")
        return None
    note = note or Note(user_id=session["user_id"])
    note.title = title
    note.subject = subject
    note.description = request.form.get("description", "").strip()
    return note


def remove_note_file(filename):
    if filename:
        path = notes_upload_dir() / filename
        if path.is_file():
            path.unlink()


@notes_bp.get("/notes")
@login_required
def list_notes():
    query = student_query(Note)
    search = request.args.get("q", "").strip()
    subject = request.args.get("subject", "").strip()
    favorite = request.args.get("favorite", "")
    if search:
        term = f"%{search}%"
        query = query.filter(Note.title.ilike(term) | Note.subject.ilike(term) | Note.description.ilike(term))
    if subject:
        query = query.filter_by(subject=subject)
    if favorite == "1":
        query = query.filter_by(is_favorite=True)
    notes = query.order_by(Note.created_at.desc()).all()
    subjects = [item[0] for item in db.session.query(Note.subject).filter_by(user_id=session["user_id"]).distinct().order_by(Note.subject).all()]
    return render_template("notes/index.html", notes=notes, subjects=subjects, search=search, subject=subject, favorite=favorite)


@notes_bp.route("/notes/upload", methods=["GET", "POST"])
@login_required
def upload_note():
    if request.method == "POST":
        note = _note_details()
        upload = request.files.get("file")
        original_filename = upload.filename.strip() if upload and upload.filename else ""
        extension = extension_for(original_filename)
        if note and not upload:
            flash("Choose a file to upload.", "danger")
            note = None
        elif note and extension not in ALLOWED_EXTENSIONS:
            flash("Allowed files: PDF, DOC, DOCX, TXT, PNG, JPG, and JPEG.", "danger")
            note = None
        if note and upload:
            safe_original = secure_filename(original_filename)
            if not safe_original:
                flash("The uploaded filename is invalid.", "danger")
            else:
                stored_filename = f"{uuid4().hex}.{extension}"
                upload.save(notes_upload_dir() / stored_filename)
                note.filename = stored_filename
                note.original_filename = safe_original
                note.file_type = extension
                note.file_size = (notes_upload_dir() / stored_filename).stat().st_size
                try:
                    db.session.add(note)
                    db.session.commit()
                    flash("Note uploaded.", "success")
                    return redirect(url_for("notes.list_notes"))
                except SQLAlchemyError:
                    db.session.rollback()
                    (notes_upload_dir() / stored_filename).unlink(missing_ok=True)
                    flash("The note could not be saved.", "danger")
    return render_template("notes/form.html", note=None)


@notes_bp.route("/notes/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_note(id):
    note = student_query(Note).filter_by(id=id).first_or_404()
    if request.method == "POST":
        if _note_details(note):
            try:
                db.session.commit()
                flash("Note details updated.", "success")
                return redirect(url_for("notes.list_notes"))
            except SQLAlchemyError:
                db.session.rollback()
                flash("The note could not be updated.", "danger")
    return render_template("notes/form.html", note=note)


@notes_bp.post("/notes/delete/<int:id>")
@login_required
def delete_note(id):
    note = student_query(Note).filter_by(id=id).first_or_404()
    stored_filename = note.filename
    try:
        db.session.delete(note)
        db.session.commit()
        remove_note_file(stored_filename)
        flash("Note deleted.", "success")
    except SQLAlchemyError:
        db.session.rollback()
        flash("The note could not be deleted.", "danger")
    return redirect(url_for("notes.list_notes"))


@notes_bp.get("/notes/download/<int:id>")
@login_required
def download_note(id):
    note = student_query(Note).filter_by(id=id).first_or_404()
    path = notes_upload_dir() / note.filename
    if not path.is_file():
        flash("The uploaded file is no longer available.", "danger")
        return redirect(url_for("notes.list_notes"))
    return send_from_directory(notes_upload_dir(), note.filename, as_attachment=True, download_name=note.original_filename)


@notes_bp.post("/notes/favorite/<int:id>")
@login_required
def toggle_favorite(id):
    note = student_query(Note).filter_by(id=id).first_or_404()
    note.is_favorite = not note.is_favorite
    try:
        db.session.commit()
        flash("Note favorite updated.", "success")
    except SQLAlchemyError:
        db.session.rollback()
        flash("The note favorite could not be updated.", "danger")
    return redirect(request.referrer or url_for("notes.list_notes"))
