import os
from pathlib import Path

from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

DEV_SECRET_KEYS = frozenset(
    {
        "dev-change-me-in-production",
        "dev-local-secret-change-me",
    }
)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'simple_lists.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    APP_BASE_URL = os.environ.get("APP_BASE_URL", "").rstrip("/")
    GIT_REPO_URL = "https://github.com/NiklasO-dev/simple-lists"
    HOST_PASSWORD = os.environ.get("HOST_PASSWORD", "")
    HOST_PASSWORD_HASH = generate_password_hash(HOST_PASSWORD) if HOST_PASSWORD else ""


def is_dev_mode() -> bool:
    if os.environ.get("SL_ALLOW_DEV_SECRET", "").lower() in ("1", "true", "yes"):
        return True
    return os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")


def validate_config(secret_key: str, host_password: str) -> None:
    if is_dev_mode():
        return
    if not secret_key or secret_key in DEV_SECRET_KEYS:
        raise RuntimeError(
            "SECRET_KEY must be set to a strong random value in production. "
            "Set SL_ALLOW_DEV_SECRET=1 only for local development."
        )
    if not host_password:
        raise RuntimeError(
            "HOST_PASSWORD must be set when starting the container. "
            "This password protects the host management area."
        )
