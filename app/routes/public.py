from flask import Blueprint, current_app, redirect, render_template, request, send_from_directory, url_for

from app.auth import is_host_authenticated
from app.pwa import manifest_response

bp = Blueprint("public", __name__)


@bp.route("/health")
def health():
    return {"status": "ok"}


@bp.route("/manifest.webmanifest")
def manifest():
    return manifest_response(
        name="Simple Lists",
        short_name="Lists",
        start_url="/",
    )


@bp.route("/sw.js")
def service_worker():
    response = send_from_directory(current_app.static_folder, "sw.js", mimetype="application/javascript")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Service-Worker-Allowed"] = "/"
    return response


@bp.route("/")
def index():
    if is_host_authenticated():
        return redirect(url_for("host.dashboard"))
    return render_template("index.html")


def app_base_url() -> str:
    base = current_app.config.get("APP_BASE_URL") or ""
    if base:
        return base.rstrip("/")
    return request.url_root.rstrip("/")


def build_share_url(share_token: str) -> str:
    return f"{app_base_url()}{url_for('list.view', share_token=share_token)}"


@bp.app_context_processor
def url_helpers():
    return {"build_share_url": build_share_url, "app_base_url": app_base_url}
