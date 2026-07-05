import json
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app import db
from app.security import generate_item_id, generate_token


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TodoList(db.Model):
    __tablename__ = "lists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, default="Untitled list")
    share_token: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, default=generate_token
    )
    password_hash: Mapped[str | None] = mapped_column(String(256), nullable=True)
    password_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    access_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    items_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    @property
    def is_locked(self) -> bool:
        return bool(self.password_hash)

    def get_items(self) -> list[dict]:
        try:
            data = json.loads(self.items_json)
            if isinstance(data, list):
                return data
        except (json.JSONDecodeError, TypeError):
            pass
        return []

    def set_items(self, items: list[dict]) -> None:
        self.items_json = json.dumps(items)
        self.updated_at = utcnow()

    @staticmethod
    def _sort_items(items: list[dict]) -> list[dict]:
        return sorted(items, key=lambda i: i.get("text", "").casefold())

    def add_item(self, text: str) -> dict:
        text = text.strip()[:500]
        if not text:
            raise ValueError("Item text cannot be empty")
        items = self.get_items()
        item = {"id": generate_item_id(), "text": text, "completed": False}
        items.append(item)
        self.set_items(self._sort_items(items))
        return item

    def toggle_item(self, item_id: str) -> bool:
        items = self.get_items()
        found = False
        for item in items:
            if item.get("id") == item_id:
                item["completed"] = not item.get("completed", False)
                found = True
                break
        if found:
            self.set_items(items)
        return found

    def delete_item(self, item_id: str) -> bool:
        items = self.get_items()
        new_items = [i for i in items if i.get("id") != item_id]
        if len(new_items) == len(items):
            return False
        self.set_items(new_items)
        return True

    def update_item_text(self, item_id: str, text: str) -> bool:
        text = text.strip()
        if not text:
            return False
        items = self.get_items()
        found = False
        for item in items:
            if item.get("id") == item_id:
                item["text"] = text
                found = True
                break
        if found:
            self.set_items(items)
        return found

    def to_export_dict(self, secret_key: str) -> dict:
        from app.security import decrypt_list_password

        data = {
            "title": self.title,
            "share_token": self.share_token,
            "locked": self.is_locked,
            "items": [
                {"text": i.get("text", ""), "completed": bool(i.get("completed", False))}
                for i in self.get_items()
            ],
        }
        if self.is_locked:
            data["password"] = decrypt_list_password(secret_key, self.password_encrypted)
        return data

    @classmethod
    def from_import_dict(
        cls, data: dict, secret_key: str, share_token: str | None = None
    ) -> "TodoList":
        from app.security import encrypt_list_password, hash_list_password, is_valid_share_token

        todo_list = cls(title=data.get("title", "Imported list")[:200])
        token = share_token or data.get("share_token")
        if token and is_valid_share_token(str(token)):
            todo_list.share_token = str(token)
        items = []
        for raw in data.get("items", []):
            if not isinstance(raw, dict):
                continue
            text = str(raw.get("text", "")).strip()
            if not text:
                continue
            items.append(
                {
                    "id": generate_item_id(),
                    "text": text[:500],
                    "completed": bool(raw.get("completed", False)),
                }
            )
        todo_list.set_items(items)
        password = data.get("password")
        if password:
            todo_list.password_hash = hash_list_password(str(password))
            todo_list.password_encrypted = encrypt_list_password(secret_key, str(password))
            todo_list.access_version = 1
        return todo_list

    def bump_access_version(self) -> None:
        self.access_version = (self.access_version or 0) + 1

    def set_list_password(self, secret_key: str, password: str) -> None:
        from app.security import encrypt_list_password, hash_list_password

        self.password_hash = hash_list_password(password)
        self.password_encrypted = encrypt_list_password(secret_key, password)
        self.bump_access_version()

    def clear_list_password(self) -> None:
        self.password_hash = None
        self.password_encrypted = None
        self.bump_access_version()
