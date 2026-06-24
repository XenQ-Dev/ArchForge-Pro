"""Global in-process session state — set once at login, read everywhere."""
from __future__ import annotations

_user: dict | None = None
_token: str | None = None


def set_current_user(user: dict, token: str) -> None:
    global _user, _token
    _user  = user
    _token = token


def get_current_user() -> dict | None:
    return _user


def get_current_user_id() -> int | None:
    return _user["id"] if _user else None


def get_current_token() -> str | None:
    return _token


def clear_session() -> None:
    global _user, _token
    _user  = None
    _token = None
