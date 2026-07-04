import secrets
import uuid

from flask import session
from itsdangerous import BadSignature, URLSafeSerializer
from werkzeug.security import check_password_hash


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def generate_item_id() -> str:
    return str(uuid.uuid4())


def _serializer(secret_key: str) -> URLSafeSerializer:
    return URLSafeSerializer(secret_key, salt="sl-csrf")


def generate_csrf_token(secret_key: str) -> str:
    token = _serializer(secret_key).dumps({"nonce": secrets.token_hex(16)})
    session["csrf_token"] = token
    return token


def validate_csrf_token(secret_key: str, token: str | None) -> bool:
    if not token:
        return False
    try:
        _serializer(secret_key).loads(token)
    except BadSignature:
        return False
    return session.get("csrf_token") == token


def check_host_password(password_hash: str, password: str) -> bool:
    if not password_hash:
        return False
    return check_password_hash(password_hash, password)


def hash_list_password(password: str) -> str:
    from werkzeug.security import generate_password_hash

    return generate_password_hash(password)


def encrypt_list_password(secret_key: str, password: str) -> str:
    return URLSafeSerializer(secret_key, salt="sl-list-pw").dumps(password)


def decrypt_list_password(secret_key: str, encrypted: str | None) -> str | None:
    if not encrypted:
        return None
    try:
        return URLSafeSerializer(secret_key, salt="sl-list-pw").loads(encrypted)
    except BadSignature:
        return None


def check_list_password(password_hash: str | None, password: str) -> bool:
    if not password_hash:
        return True
    if not password:
        return False
    return check_password_hash(password_hash, password)
