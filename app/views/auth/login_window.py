"""
ArchForge Pro — Login / Registration / Password-Reset Window.
Shown before MainWindow. Emits login_success(user_dict, token) on success.
"""
from __future__ import annotations
import re

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QMessageBox,
    QDialog, QDialogButtonBox, QApplication,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPainter, QPixmap, QPen

from app.models.user_model import (
    create_user, get_user_by_email, verify_password,
    mark_verified, update_password, create_session,
    create_code, verify_code,
)
from app.utils.email_sender import send_email, smtp_configured, verification_email, reset_email

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ── Shared QSS ────────────────────────────────────────────────────────────────

_QSS = """
QMainWindow, QDialog { background-color:#000000; }
QWidget { background-color:transparent; color:#ffffff;
          font-family:'Courier New',monospace; font-size:12px; }

QLabel#title  { font-size:22px; font-weight:700; letter-spacing:4px; color:#ffffff; }
QLabel#sub    { font-size:10px; letter-spacing:2px; color:#555555; }
QLabel#logo   { font-size:10px; letter-spacing:4px; color:#333333; }
QLabel#err    { font-size:10px; letter-spacing:1px; color:#cc3333; }
QLabel#link   { font-size:10px; letter-spacing:1px; color:#555555; }
QLabel#field_label { font-size:10px; letter-spacing:2px; color:#666666; }

QLineEdit {
    background-color:#0a0a0a; color:#ffffff;
    border:1px solid #222222; border-radius:0px;
    padding:10px 12px; font-family:'Courier New',monospace; font-size:12px;
}
QLineEdit:focus { border:1px solid #555555; }
QLineEdit::placeholder { color:#333333; }

QPushButton#primary {
    background-color:#ffffff; color:#000000;
    border:none; border-radius:0px; padding:11px 20px;
    font-family:'Courier New',monospace; font-weight:700;
    font-size:12px; letter-spacing:3px;
}
QPushButton#primary:hover   { background-color:#dddddd; }
QPushButton#primary:pressed { background-color:#bbbbbb; }

QPushButton#ghost {
    background-color:transparent; color:#444444;
    border:none; padding:6px 0px;
    font-family:'Courier New',monospace; font-size:10px; letter-spacing:2px;
}
QPushButton#ghost:hover { color:#ffffff; }

QFrame#card {
    background-color:#0a0a0a; border:1px solid #1e1e1e;
}
QFrame#sep { background-color:#1a1a1a; max-height:1px; }
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _field(placeholder: str, echo: QLineEdit.EchoMode = QLineEdit.EchoMode.Normal) -> QLineEdit:
    f = QLineEdit()
    f.setPlaceholderText(placeholder)
    f.setEchoMode(echo)
    f.setFixedHeight(42)
    return f


def _label(text: str, obj: str) -> QLabel:
    l = QLabel(text)
    l.setObjectName(obj)
    return l


def _btn(text: str, obj: str = "primary") -> QPushButton:
    b = QPushButton(text)
    b.setObjectName(obj)
    b.setFixedHeight(44)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


def _sep() -> QFrame:
    f = QFrame()
    f.setObjectName("sep")
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFixedHeight(1)
    return f


def _send_or_show(email: str, name: str, purpose: str) -> str:
    """Send a verification/reset code. If SMTP not configured, return the code so UI can show it."""
    code = create_code(email, purpose)
    if smtp_configured():
        if purpose == "verify":
            send_email(email, "ArchForge Pro — Verify your email", verification_email(name, code))
        else:
            send_email(email, "ArchForge Pro — Password reset code", reset_email(code))
        return ""          # code delivered by email — don't expose in UI
    return code            # SMTP not set up — show in dialog so dev can still test


# ── Code-entry dialog (verify / reset) ────────────────────────────────────────

class _CodeDialog(QDialog):
    """Generic 5-digit code entry dialog. Returns code string on accept."""

    def __init__(self, email: str, purpose: str, fallback_code: str, parent=None):
        super().__init__(parent, Qt.WindowType.Dialog)
        self.setWindowTitle("ENTER CODE")
        self.setFixedSize(420, 340)
        self.setStyleSheet(_QSS)
        self._email   = email
        self._purpose = purpose

        lay = QVBoxLayout(self)
        lay.setContentsMargins(36, 36, 36, 36)
        lay.setSpacing(14)

        lay.addWidget(_label("ENTER CODE", "title"))

        if fallback_code:
            # SMTP not configured — show code on screen
            note = QLabel(
                f"SMTP not configured.\nYour code is shown below (dev mode):"
            )
            note.setObjectName("sub")
            note.setWordWrap(True)
            lay.addWidget(note)

            code_lbl = QLabel(fallback_code)
            code_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            code_lbl.setStyleSheet(
                "color:#ffffff; font-size:32px; font-weight:700; letter-spacing:12px;"
                "background:#111; border:1px solid #222; padding:14px;"
            )
            lay.addWidget(code_lbl)
        else:
            sub = _label(f"A 5-digit code was sent to {email}", "sub")
            sub.setWordWrap(True)
            lay.addWidget(sub)

        self._code_field = _field("_ _ _ _ _")
        self._code_field.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._code_field.setStyleSheet(
            "font-size:20px; letter-spacing:8px; text-align:center;"
        )
        self._code_field.setMaxLength(5)
        lay.addWidget(self._code_field)

        self._err = _label("", "err")
        self._err.hide()
        lay.addWidget(self._err)

        verify_btn = _btn("VERIFY")
        verify_btn.clicked.connect(self._verify)
        lay.addWidget(verify_btn)

        resend_btn = _btn("Resend code", "ghost")
        resend_btn.clicked.connect(self._resend)
        resend_btn.setAlignment(Qt.AlignmentFlag.AlignCenter) if hasattr(resend_btn, "setAlignment") else None
        lay.addWidget(resend_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def _verify(self) -> None:
        code = self._code_field.text().strip()
        if len(code) != 5 or not code.isdigit():
            self._err.setText("Enter the 5-digit code.")
            self._err.show()
            return
        if verify_code(self._email, code, self._purpose):
            self.accept()
        else:
            self._err.setText("Invalid or expired code. Try again.")
            self._err.show()

    def _resend(self) -> None:
        fallback = _send_or_show(self._email, "", self._purpose)
        msg = "Code resent to your email." if not fallback else f"New code (dev): {fallback}"
        self._err.setText(msg)
        self._err.setStyleSheet("color:#27ae60; font-size:10px; letter-spacing:1px;")
        self._err.show()


# ── Reset-password dialog ─────────────────────────────────────────────────────

class _ResetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Dialog)
        self.setWindowTitle("RESET PASSWORD")
        self.setFixedSize(420, 460)
        self.setStyleSheet(_QSS)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(36, 36, 36, 36)
        lay.setSpacing(12)

        lay.addWidget(_label("RESET PASSWORD", "title"))
        lay.addWidget(_label("Enter your email to receive a reset code.", "sub"))
        lay.addSpacing(8)

        self._email_f = _field("Email address")
        lay.addWidget(self._email_f)

        send_btn = _btn("SEND CODE")
        send_btn.clicked.connect(self._send_code)
        lay.addWidget(send_btn)

        lay.addWidget(_sep())

        self._code_f  = _field("5-digit code")
        self._pass_f  = _field("New password", QLineEdit.EchoMode.Password)
        self._cpass_f = _field("Confirm new password", QLineEdit.EchoMode.Password)
        for w in (self._code_f, self._pass_f, self._cpass_f):
            w.setEnabled(False)
            lay.addWidget(w)

        self._err = _label("", "err")
        self._err.hide()
        lay.addWidget(self._err)

        reset_btn = _btn("RESET PASSWORD")
        reset_btn.clicked.connect(self._do_reset)
        lay.addWidget(reset_btn)
        self._reset_btn = reset_btn
        self._reset_btn.setEnabled(False)

        self._email_sent_to = ""

    def _send_code(self) -> None:
        email = self._email_f.text().strip().lower()
        if not _EMAIL_RE.match(email):
            self._show_err("Enter a valid email address.")
            return
        user = get_user_by_email(email)
        if not user:
            self._show_err("No account found with that email.")
            return
        fallback = _send_or_show(email, user["display_name"], "reset")
        self._email_sent_to = email
        for w in (self._code_f, self._pass_f, self._cpass_f):
            w.setEnabled(True)
        self._reset_btn.setEnabled(True)
        msg = f"Code sent to {email}." if not fallback else f"Dev mode — code: {fallback}"
        self._show_err(msg, ok=True)

    def _do_reset(self) -> None:
        code  = self._code_f.text().strip()
        pw    = self._pass_f.text()
        cpw   = self._cpass_f.text()
        if len(code) != 5 or not code.isdigit():
            self._show_err("Enter the 5-digit code.")
            return
        if len(pw) < 8:
            self._show_err("Password must be at least 8 characters.")
            return
        if pw != cpw:
            self._show_err("Passwords do not match.")
            return
        if not verify_code(self._email_sent_to, code, "reset"):
            self._show_err("Invalid or expired code.")
            return
        update_password(self._email_sent_to, pw)
        QMessageBox.information(self, "Success", "Password reset successfully. You can now log in.")
        self.accept()

    def _show_err(self, msg: str, ok: bool = False) -> None:
        self._err.setText(msg)
        if ok:
            self._err.setStyleSheet("color:#27ae60; font-size:10px; letter-spacing:1px;")
        else:
            self._err.setStyleSheet("color:#cc3333; font-size:10px; letter-spacing:1px;")
        self._err.show()


# ── Registration dialog ───────────────────────────────────────────────────────

class _RegisterDialog(QDialog):
    registered = pyqtSignal(dict, str)   # user, token

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Dialog)
        self.setWindowTitle("CREATE ACCOUNT")
        self.setFixedSize(420, 520)
        self.setStyleSheet(_QSS)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(36, 36, 36, 36)
        lay.setSpacing(12)

        lay.addWidget(_label("CREATE ACCOUNT", "title"))
        lay.addWidget(_label("Set up your ArchForge Pro account.", "sub"))
        lay.addSpacing(8)

        self._name_f  = _field("Full name")
        self._email_f = _field("Email address")
        self._pass_f  = _field("Password (min 8 chars)", QLineEdit.EchoMode.Password)
        self._cpass_f = _field("Confirm password", QLineEdit.EchoMode.Password)
        for w in (self._name_f, self._email_f, self._pass_f, self._cpass_f):
            lay.addWidget(w)

        self._err = _label("", "err")
        self._err.hide()
        lay.addWidget(self._err)

        reg_btn = _btn("CREATE ACCOUNT")
        reg_btn.clicked.connect(self._register)
        lay.addWidget(reg_btn)

        lay.addStretch()
        note = _label("Already have an account? Close this and log in.", "sub")
        note.setWordWrap(True)
        lay.addWidget(note)

    def _register(self) -> None:
        name  = self._name_f.text().strip()
        email = self._email_f.text().strip().lower()
        pw    = self._pass_f.text()
        cpw   = self._cpass_f.text()

        if not name:
            self._show_err("Enter your full name."); return
        if not _EMAIL_RE.match(email):
            self._show_err("Enter a valid email address."); return
        if get_user_by_email(email):
            self._show_err("An account with that email already exists."); return
        if len(pw) < 8:
            self._show_err("Password must be at least 8 characters."); return
        if pw != cpw:
            self._show_err("Passwords do not match."); return

        create_user(email, name, pw)
        fallback = _send_or_show(email, name, "verify")

        dlg = _CodeDialog(email, "verify", fallback, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            mark_verified(email)
            user = get_user_by_email(email)
            token = create_session(user["id"])
            self.registered.emit(dict(user), token)
            self.accept()

    def _show_err(self, msg: str) -> None:
        self._err.setText(msg)
        self._err.show()


# ── Login Window ──────────────────────────────────────────────────────────────

class LoginWindow(QMainWindow):
    login_success = pyqtSignal(dict, str)   # user_dict, token

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ARCHFORGE PRO — LOGIN")
        self.setFixedSize(480, 600)
        self.setStyleSheet(_QSS)
        self._center()
        self._build_ui()

    def _center(self) -> None:
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            (screen.width()  - 480) // 2,
            (screen.height() - 600) // 2,
        )

    def _build_ui(self) -> None:
        root = QWidget()
        root.setStyleSheet("background-color:#000000;")
        self.setCentralWidget(root)

        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch()

        # ── Card ──────────────────────────────────────────────────────────────
        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(380)
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(36, 36, 36, 36)
        card_lay.setSpacing(14)

        # Logo line
        logo = _label("ARCHFORGE PRO  //  v1.0.0", "logo")
        card_lay.addWidget(logo)
        card_lay.addWidget(_sep())
        card_lay.addSpacing(4)

        # Title
        card_lay.addWidget(_label("WELCOME BACK", "title"))
        card_lay.addWidget(_label("Sign in to your account.", "sub"))
        card_lay.addSpacing(8)

        # Email
        self._email_f = _field("m@example.com")
        card_lay.addWidget(_label("EMAIL", "field_label"))
        card_lay.addWidget(self._email_f)

        # Password row
        pw_row = QHBoxLayout()
        pw_row.setContentsMargins(0, 0, 0, 0)
        pw_row.addWidget(_label("PASSWORD", "field_label"))
        pw_row.addStretch()
        forgot_btn = _btn("Forgot password?", "ghost")
        forgot_btn.setFixedHeight(20)
        forgot_btn.clicked.connect(self._forgot_password)
        pw_row.addWidget(forgot_btn)
        card_lay.addLayout(pw_row)

        self._pass_f = _field("••••••••", QLineEdit.EchoMode.Password)
        self._pass_f.returnPressed.connect(self._login)
        card_lay.addWidget(self._pass_f)

        # Error label
        self._err = _label("", "err")
        self._err.hide()
        card_lay.addWidget(self._err)

        # Login button
        login_btn = _btn("LOGIN")
        login_btn.clicked.connect(self._login)
        card_lay.addWidget(login_btn)

        card_lay.addWidget(_sep())

        # Sign up link
        signup_row = QHBoxLayout()
        signup_row.addWidget(_label("Don't have an account?", "sub"))
        signup_btn = _btn("Sign up", "ghost")
        signup_btn.setFixedHeight(20)
        signup_btn.clicked.connect(self._signup)
        signup_row.addWidget(signup_btn)
        signup_row.addStretch()
        card_lay.addLayout(signup_row)

        # Center card
        h = QHBoxLayout()
        h.addStretch()
        h.addWidget(card)
        h.addStretch()
        outer.addLayout(h)
        outer.addStretch()

    # ── Actions ───────────────────────────────────────────────────────────────

    def _login(self) -> None:
        email = self._email_f.text().strip().lower()
        pw    = self._pass_f.text()

        if not email or not pw:
            self._show_err("Enter your email and password."); return

        user = get_user_by_email(email)
        if not user:
            self._show_err("No account found with that email."); return
        if not verify_password(pw, user["password_hash"], user["salt"]):
            self._show_err("Incorrect password."); return
        if not user["is_verified"]:
            self._show_err("Email not verified. Check your inbox or sign up again."); return

        token = create_session(user["id"])
        self.login_success.emit(dict(user), token)

    def _signup(self) -> None:
        dlg = _RegisterDialog(self)
        dlg.registered.connect(self.login_success.emit)
        dlg.exec()

    def _forgot_password(self) -> None:
        dlg = _ResetDialog(self)
        dlg.exec()

    def _show_err(self, msg: str) -> None:
        self._err.setText(msg)
        self._err.show()
