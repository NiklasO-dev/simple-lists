import os

from flask import Flask, redirect, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import Config, validate_config

db = SQLAlchemy()


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)
    validate_config(app.config["SECRET_KEY"], app.config["HOST_PASSWORD"])

    if os.environ.get("BEHIND_PROXY", "1") == "1":
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    db.init_app(app)

    @app.before_request
    def set_request_globals():
        if request.path.startswith("/static"):
            return

    @app.context_processor
    def inject_globals():
        from app.auth import is_host_authenticated
        from app.security import generate_csrf_token

        return {
            "csrf_token": generate_csrf_token(app.config["SECRET_KEY"]),
            "is_host": is_host_authenticated(),
            "git_repo_url": app.config["GIT_REPO_URL"],
        }

    from app.routes.host import bp as host_bp
    from app.routes.list_view import bp as list_bp
    from app.routes.public import bp as public_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(host_bp)
    app.register_blueprint(list_bp)

    with app.app_context():
        db.create_all()

    return app
