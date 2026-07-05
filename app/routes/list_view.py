from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app import db
from app.auth import grant_list_access, has_list_access, require_csrf
from app.models import TodoList
from app.pwa import manifest_response
from app.rate_limit import clear_attempts, is_rate_limited, record_failed_attempt
from app.security import check_list_password

bp = Blueprint("list", __name__, url_prefix="/l")


@bp.context_processor
def list_pwa_context():
    if request.blueprint != "list" or not request.view_args:
        return {}
    share_token = request.view_args.get("share_token")
    if not share_token:
        return {}
    todo_list = TodoList.query.filter_by(share_token=share_token).first()
    if not todo_list:
        return {}
    return {
        "pwa_manifest_url": url_for("list.manifest", share_token=share_token),
        "pwa_short_name": todo_list.title,
    }


@bp.route("/<share_token>/manifest.webmanifest")
def manifest(share_token: str):
    todo_list = TodoList.query.filter_by(share_token=share_token).first()
    if not todo_list:
        abort(404)
    start_url = url_for("list.view", share_token=share_token)
    short_name = todo_list.title[:12] + "…" if len(todo_list.title) > 12 else todo_list.title
    return manifest_response(
        name=f"{todo_list.title} — Simple Lists",
        short_name=short_name,
        start_url=start_url,
        manifest_id=start_url,
    )


@bp.route("/<share_token>", methods=["GET", "POST"])
def view(share_token: str):
    todo_list = TodoList.query.filter_by(share_token=share_token).first()
    if not todo_list:
        abort(404)

    if todo_list.is_locked and not has_list_access(
        share_token, todo_list.password_hash, todo_list.access_version
    ):
        if request.method == "POST":
            require_csrf()
            scope = f"list_unlock:{share_token}"
            if is_rate_limited(scope):
                flash("Too many failed attempts. Please wait a few minutes and try again.", "error")
                return render_template("list/password.html", todo_list=todo_list), 429
            password = request.form.get("password", "")
            if check_list_password(todo_list.password_hash, password):
                clear_attempts(scope)
                grant_list_access(share_token, todo_list.access_version)
                return redirect(url_for("list.view", share_token=share_token))
            record_failed_attempt(scope)
            flash("Incorrect password.", "error")
        return render_template("list/password.html", todo_list=todo_list)

    return render_template("list/view.html", todo_list=todo_list)


@bp.post("/<share_token>/items")
def add_item(share_token: str):
    todo_list = _authorized_list(share_token)
    require_csrf()
    text = request.form.get("text", "")
    try:
        todo_list.add_item(text)
        db.session.commit()
    except ValueError:
        flash("Item text cannot be empty.", "error")
    return redirect(url_for("list.view", share_token=share_token))


@bp.post("/<share_token>/items/<item_id>/toggle")
def toggle_item(share_token: str, item_id: str):
    todo_list = _authorized_list(share_token)
    require_csrf()
    todo_list.toggle_item(item_id)
    db.session.commit()
    return redirect(url_for("list.view", share_token=share_token))


def _authorized_list(share_token: str) -> TodoList:
    todo_list = TodoList.query.filter_by(share_token=share_token).first()
    if not todo_list:
        abort(404)
    if todo_list.is_locked and not has_list_access(
        share_token, todo_list.password_hash, todo_list.access_version
    ):
        abort(403)
    return todo_list
