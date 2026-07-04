import time
from collections import defaultdict

from flask import request

MAX_ATTEMPTS = 5
WINDOW_SECONDS = 300

_attempts: dict[str, list[float]] = defaultdict(list)


def _client_key(scope: str) -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    ip = forwarded.split(",")[0].strip() if forwarded else (request.remote_addr or "unknown")
    return f"{scope}:{ip}"


def is_rate_limited(scope: str) -> bool:
    key = _client_key(scope)
    now = time.time()
    recent = [t for t in _attempts[key] if now - t < WINDOW_SECONDS]
    _attempts[key] = recent
    return len(recent) >= MAX_ATTEMPTS


def record_failed_attempt(scope: str) -> None:
    _attempts[_client_key(scope)].append(time.time())


def clear_attempts(scope: str) -> None:
    _attempts.pop(_client_key(scope), None)
