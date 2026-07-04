from functools import wraps

from flask import abort, current_app, redirect, request, session, url_for

from app.security import check_host_password


def is_host_authenticated() -> bool:
    return session.get("host_authenticated") is True


def login_host() -> None:
    session["host_authenticated"] = True
    session.permanent = True


def logout_host() -> None:
    session.pop("host_authenticated", None)


def host_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not is_host_authenticated():
            return redirect(url_for("host.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def verify_host_password(password: str) -> bool:
    return check_host_password(current_app.config["HOST_PASSWORD_HASH"], password)


def list_session_key(share_token: str) -> str:
    return f"list_access_{share_token}"


def grant_list_access(share_token: str) -> None:
    session[list_session_key(share_token)] = True


def has_list_access(share_token: str, list_password_hash: str | None) -> bool:
    if not list_password_hash:
        return True
    return session.get(list_session_key(share_token)) is True


def require_csrf():
    from app.security import validate_csrf_token

    token = request.form.get("csrf_token")
    if not validate_csrf_token(current_app.config["SECRET_KEY"], token):
        abort(400)
