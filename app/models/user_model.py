"""User, session, and verification-code CRUD."""
from __future__ import annotations
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional
from .database import get_connection


# ── Password hashing (PBKDF2-SHA256, 260k iterations) ────────────────────────

def _hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    if salt is None:
        salt = secrets.token_hex(32)
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 260_000
    )
    return dk.hex(), salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    dk, _ = _hash_password(password, salt)
    return secrets.compare_digest(dk, stored_hash)


# ── Users ─────────────────────────────────────────────────────────────────────

def create_user(email: str, display_name: str, password: str) -> int:
    pw_hash, salt = _hash_password(password)
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO users(email, display_name, password_hash, salt)
               VALUES(?,?,?,?)""",
            (email.lower().strip(), display_name.strip(), pw_hash, salt),
        )
        conn.commit()
        return cur.lastrowid


def get_user_by_email(email: str) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email=?", (email.lower().strip(),)
        ).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE id=?", (user_id,)
        ).fetchone()
        return dict(row) if row else None


def mark_verified(email: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET is_verified=1 WHERE email=?", (email.lower().strip(),)
        )
        conn.commit()


def update_password(email: str, new_password: str) -> None:
    pw_hash, salt = _hash_password(new_password)
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET password_hash=?, salt=? WHERE email=?",
            (pw_hash, salt, email.lower().strip()),
        )
        conn.commit()


# ── Sessions ──────────────────────────────────────────────────────────────────

def create_session(user_id: int) -> str:
    token = str(uuid.uuid4())
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO sessions(user_id, token) VALUES(?,?)", (user_id, token)
        )
        conn.commit()
    return token


def get_session_user(token: str) -> Optional[dict]:
    """Return the user for a token, or None if invalid/expired/unverified."""
    with get_connection() as conn:
        row = conn.execute(
            """SELECT u.* FROM users u
               JOIN sessions s ON s.user_id = u.id
               WHERE s.token=? AND u.is_verified=1""",
            (token,),
        ).fetchone()
        return dict(row) if row else None


def delete_session(token: str) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM sessions WHERE token=?", (token,))
        conn.commit()


# ── Verification / reset codes ────────────────────────────────────────────────

def create_code(email: str, purpose: str) -> str:
    """Generate a 5-digit code, invalidate old ones, return the new code."""
    code = str(secrets.randbelow(90_000) + 10_000)  # 10000-99999
    expires = (datetime.now() + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        conn.execute(
            "UPDATE verification_codes SET used=1 WHERE email=? AND purpose=? AND used=0",
            (email.lower().strip(), purpose),
        )
        conn.execute(
            "INSERT INTO verification_codes(email, code, purpose, expires_at) VALUES(?,?,?,?)",
            (email.lower().strip(), code, purpose, expires),
        )
        conn.commit()
    return code


def verify_code(email: str, code: str, purpose: str) -> bool:
    """Check code validity; marks it used on success."""
    with get_connection() as conn:
        row = conn.execute(
            """SELECT id FROM verification_codes
               WHERE email=? AND code=? AND purpose=? AND used=0
                 AND expires_at > datetime('now','localtime')""",
            (email.lower().strip(), code, purpose),
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE verification_codes SET used=1 WHERE id=?", (row[0],)
            )
            conn.commit()
            return True
        return False
