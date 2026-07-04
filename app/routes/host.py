import json
from datetime import datetime, timezone

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from io import BytesIO

from app import db
from app.auth import (
    grant_list_access,
    has_list_access,
    host_required,
    login_host,
    logout_host,
    require_csrf,
    verify_host_password,
)
from app.models import TodoList
from app.routes.public import build_share_url

bp = Blueprint("host", __name__, url_prefix="/host")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        require_csrf()
        password = request.form.get("password", "")
        if verify_host_password(password):
            login_host()
            next_url = request.args.get("next") or request.form.get("next")
            if next_url and next_url.startswith("/host"):
                return redirect(next_url)
            return redirect(url_for("host.dashboard"))
        flash("Incorrect password.", "error")
    return render_template("host/login.html")


@bp.post("/logout")
def logout():
    require_csrf()
    logout_host()
    return redirect(url_for("public.index"))


@bp.route("/")
@host_required
def dashboard():
    lists = TodoList.query.order_by(TodoList.updated_at.desc()).all()
    return render_template("host/dashboard.html", lists=lists)


@bp.post("/lists")
@host_required
def create_list():
    require_csrf()
    title = (request.form.get("title") or "New list").strip()[:200] or "New list"
    todo_list = TodoList(title=title)
    db.session.add(todo_list)
    db.session.commit()
    return redirect(url_for("host.edit_list", list_id=todo_list.id))


@bp.route("/lists/<int:list_id>")
@host_required
def edit_list(list_id: int):
    todo_list = db.get_or_404(TodoList, list_id)
    return render_template(
        "host/list_edit.html",
        todo_list=todo_list,
        share_url=build_share_url(todo_list.share_token),
    )


@bp.post("/lists/<int:list_id>/settings")
@host_required
def update_settings(list_id: int):
    require_csrf()
    todo_list = db.get_or_404(TodoList, list_id)
    title = (request.form.get("title") or "").strip()[:200]
    if title:
        todo_list.title = title

    lock_action = request.form.get("lock_action", "keep")
    if lock_action == "set":
        password = request.form.get("list_password", "")
        if password:
            todo_list.set_list_password(current_app.config["SECRET_KEY"], password)
        else:
            flash("Enter a password to lock the list, or choose another option.", "error")
    elif lock_action == "remove":
        todo_list.clear_list_password()

    if request.form.get("regenerate_token"):
        from app.security import generate_token

        todo_list.share_token = generate_token()

    db.session.commit()
    flash("Settings saved.", "success")
    return redirect(url_for("host.edit_list", list_id=list_id))


@bp.post("/lists/<int:list_id>/delete")
@host_required
def delete_list(list_id: int):
    require_csrf()
    todo_list = db.get_or_404(TodoList, list_id)
    db.session.delete(todo_list)
    db.session.commit()
    flash("List deleted.", "success")
    return redirect(url_for("host.dashboard"))


@bp.post("/lists/<int:list_id>/items")
@host_required
def add_item(list_id: int):
    require_csrf()
    todo_list = db.get_or_404(TodoList, list_id)
    text = request.form.get("text", "")
    try:
        todo_list.add_item(text)
        db.session.commit()
    except ValueError:
        flash("Item text cannot be empty.", "error")
    return redirect(url_for("host.edit_list", list_id=list_id))


@bp.post("/lists/<int:list_id>/items/<item_id>/toggle")
@host_required
def toggle_item(list_id: int, item_id: str):
    require_csrf()
    todo_list = db.get_or_404(TodoList, list_id)
    todo_list.toggle_item(item_id)
    db.session.commit()
    return redirect(url_for("host.edit_list", list_id=list_id))


@bp.post("/lists/<int:list_id>/items/<item_id>/delete")
@host_required
def delete_item(list_id: int, item_id: str):
    require_csrf()
    todo_list = db.get_or_404(TodoList, list_id)
    todo_list.delete_item(item_id)
    db.session.commit()
    return redirect(url_for("host.edit_list", list_id=list_id))


@bp.get("/export")
@host_required
def export_lists():
    lists = TodoList.query.order_by(TodoList.created_at.asc()).all()
    export_data = {
        "version": 1,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "lists": [],
    }
    for todo_list in lists:
        export_data["lists"].append(
            todo_list.to_export_dict(current_app.config["SECRET_KEY"])
        )

    payload = json.dumps(export_data, indent=2, ensure_ascii=False)
    buffer = BytesIO(payload.encode("utf-8"))
    return send_file(
        buffer,
        mimetype="application/json",
        as_attachment=True,
        download_name="simple-lists-export.json",
    )


@bp.route("/import", methods=["GET", "POST"])
@host_required
def import_lists():
    if request.method == "GET":
        return render_template("host/import.html")

    require_csrf()
    mode = request.form.get("mode", "merge")
    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        flash("Choose a JSON file to import.", "error")
        return render_template("host/import.html"), 400

    try:
        raw = json.loads(uploaded.read().decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        flash("Invalid JSON file.", "error")
        return render_template("host/import.html"), 400

    if not isinstance(raw, dict) or "lists" not in raw:
        flash("Unrecognized export format — expected a JSON object with a lists array.", "error")
        return render_template("host/import.html"), 400

    lists_data = raw.get("lists", [])
    if not isinstance(lists_data, list):
        flash("Invalid lists array in export file.", "error")
        return render_template("host/import.html"), 400

    if mode == "replace":
        TodoList.query.delete()
        db.session.commit()

    imported = 0
    for entry in lists_data:
        if not isinstance(entry, dict):
            continue
        todo_list = TodoList.from_import_dict(entry, current_app.config["SECRET_KEY"])
        if mode == "merge":
            existing = TodoList.query.filter_by(share_token=todo_list.share_token).first()
            if existing:
                existing.title = todo_list.title
                existing.items_json = todo_list.items_json
                existing.password_hash = todo_list.password_hash
                existing.password_encrypted = todo_list.password_encrypted
            else:
                db.session.add(todo_list)
        else:
            db.session.add(todo_list)
        imported += 1

    db.session.commit()
    flash(f"Imported {imported} list(s).", "success")
    return redirect(url_for("host.dashboard"))
