"""ArchForge Pro — Login Window. Pixel-art UI recreating the reference template."""
from __future__ import annotations
import re

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QMessageBox,
    QDialog, QApplication,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon

from app.models.user_model import (
    create_user, get_user_by_email, verify_password,
    mark_verified, update_password, create_session,
    create_code, verify_code,
)
from app.utils.email_sender import send_email, smtp_configured, verification_email, reset_email
from app.utils.fonts import pixel_family
from app.utils.brand_icons import apple_icon, google_icon
from app.utils.node_field import NodeFieldBackground

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _qss() -> str:
    PIX = pixel_family()
    return f"""
QMainWindow, QDialog {{ background-color:#000000; }}
QWidget {{ background-color:transparent; color:#cdcdcd; font-family:"{PIX}"; }}

QFrame#card {{
    background-color:#161616;
    border:1px solid #3a3a3a;
    border-radius:10px;
}}

QLabel#h1   {{ color:#ffffff; font-family:"{PIX}"; font-size:17px; }}
QLabel#sub  {{ color:#8a8a8a; font-family:"{PIX}"; font-size:8px; line-height:160%; }}
QLabel#lbl  {{ color:#ffffff; font-family:"{PIX}"; font-size:9px; }}
QLabel#or   {{ color:#7a7a7a; font-family:"{PIX}"; font-size:8px; }}
QLabel#err  {{ color:#e0564f; font-family:"{PIX}"; font-size:7px; }}
QLabel#foot {{ color:#6a6a6a; font-family:"{PIX}"; font-size:8px; }}

QLineEdit {{
    background-color:#2b2b2b;
    color:#ffffff;
    border:1px solid #444444;
    border-bottom:3px solid #141414;
    border-radius:6px;
    padding:11px 12px;
    font-family:"{PIX}"; font-size:9px;
    selection-background-color:#555555;
}}
QLineEdit:focus {{ border:1px solid #6a6a6a; border-bottom:3px solid #141414; }}
QLineEdit::placeholder {{ color:#5a5a5a; }}

QPushButton#oauth {{
    background-color:#2b2b2b;
    color:#ffffff;
    border:1px solid #4a4a4a;
    border-bottom:4px solid #121212;
    border-radius:7px;
    padding:8px 12px;
    font-family:"{PIX}"; font-size:9px;
}}
QPushButton#oauth:hover   {{ background-color:#333333; border-color:#5e5e5e; }}
QPushButton#oauth:pressed {{ background-color:#222222; border-bottom:1px solid #121212; }}

QPushButton#primary {{
    background-color:#2e2e2e;
    color:#ffffff;
    border:1px solid #6c6c6c;
    border-bottom:4px solid #121212;
    border-radius:7px;
    padding:9px 12px;
    font-family:"{PIX}"; font-size:10px;
}}
QPushButton#primary:hover   {{ background-color:#383838; border-color:#8a8a8a; }}
QPushButton#primary:pressed {{ background-color:#252525; border-bottom:1px solid #121212; }}

QPushButton#link {{
    background:transparent; color:#9a9a9a; border:none; padding:0;
    font-family:"{PIX}"; font-size:8px; text-decoration:underline;
}}
QPushButton#link:hover {{ color:#ffffff; }}

QFrame#hline {{ background-color:#333333; max-height:1px; min-height:1px; border:none; }}
"""


# ── widget helpers ────────────────────────────────────────────────────────────

def _lbl(text: str, cls: str, center: bool = False) -> QLabel:
    w = QLabel(text)
    w.setObjectName(cls)
    if center:
        w.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return w


def _input(ph: str, pw: bool = False) -> QLineEdit:
    w = QLineEdit()
    w.setPlaceholderText(ph)
    w.setMinimumHeight(40)
    if pw:
        w.setEchoMode(QLineEdit.EchoMode.Password)
    return w


def _hline() -> QFrame:
    f = QFrame()
    f.setObjectName("hline")
    f.setFixedHeight(1)
    return f


def _send_code(email: str, name: str, purpose: str) -> str:
    code = create_code(email, purpose)
    if smtp_configured():
        if purpose == "verify":
            send_email(email, "ArchForge Pro — Verify email", verification_email(name, code))
        else:
            send_email(email, "ArchForge Pro — Reset password", reset_email(code))
        return ""
    return code


# ── code entry dialog ─────────────────────────────────────────────────────────

class _CodeDlg(QDialog):
    def __init__(self, email: str, purpose: str, fallback: str, parent=None):
        super().__init__(parent, Qt.WindowType.Dialog)
        self.setWindowTitle("Verify Code")
        self.setFixedSize(420, 300)
        self.setStyleSheet(_qss())
        self._email, self._purpose = email, purpose
        PIX = pixel_family()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(34, 30, 34, 30)
        lay.setSpacing(12)

        lay.addWidget(_lbl("ENTER CODE", "h1", center=True))
        if fallback:
            lay.addWidget(_lbl("SMTP off — dev code:", "sub", center=True))
            big = QLabel(fallback)
            big.setAlignment(Qt.AlignmentFlag.AlignCenter)
            big.setStyleSheet(
                f'color:#ffffff;font-family:"{PIX}";font-size:24px;letter-spacing:6px;'
                "background:#2b2b2b;border:1px solid #444;border-radius:6px;padding:12px;"
            )
            lay.addWidget(big)
        else:
            lay.addWidget(_lbl(f"Code sent to {email}", "sub", center=True))

        self._code = _input("_____")
        self._code.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._code.setMaxLength(5)
        self._code.setStyleSheet(
            f'font-family:"{PIX}";font-size:16px;letter-spacing:8px;'
            "background:#2b2b2b;border:1px solid #444;border-bottom:3px solid #141414;"
            "border-radius:6px;color:#fff;padding:10px;"
        )
        lay.addWidget(self._code)

        self._err = _lbl("", "err", center=True)
        self._err.hide()
        lay.addWidget(self._err)

        btn = QPushButton("VERIFY")
        btn.setObjectName("primary")
        btn.setMinimumHeight(42)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._verify)
        lay.addWidget(btn)

    def _verify(self):
        c = self._code.text().strip()
        if len(c) != 5 or not c.isdigit():
            self._err.setText("Enter the 5-digit code."); self._err.show(); return
        if verify_code(self._email, c, self._purpose):
            self.accept()
        else:
            self._err.setText("Invalid or expired code."); self._err.show()


# ── forgot-password dialog ────────────────────────────────────────────────────

class _ForgotDlg(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Dialog)
        self.setWindowTitle("Reset Password")
        self.setFixedSize(420, 430)
        self.setStyleSheet(_qss())
        self._pending = ""

        lay = QVBoxLayout(self)
        lay.setContentsMargins(34, 28, 34, 28)
        lay.setSpacing(10)

        lay.addWidget(_lbl("RESET PASSWORD", "h1", center=True))
        lay.addSpacing(6)
        lay.addWidget(_lbl("Email", "lbl"))
        self._ef = _input("you@example.com")
        lay.addWidget(self._ef)

        sb = QPushButton("SEND CODE")
        sb.setObjectName("primary")
        sb.setMinimumHeight(40)
        sb.setCursor(Qt.CursorShape.PointingHandCursor)
        sb.clicked.connect(self._send)
        lay.addWidget(sb)

        lay.addWidget(_hline())

        lay.addWidget(_lbl("Code", "lbl"))
        self._cf = _input("5-digit code"); self._cf.setEnabled(False)
        lay.addWidget(self._cf)
        lay.addWidget(_lbl("New password", "lbl"))
        self._pf = _input("min 8 chars", pw=True); self._pf.setEnabled(False)
        lay.addWidget(self._pf)
        self._cpf = _input("confirm", pw=True); self._cpf.setEnabled(False)
        lay.addWidget(self._cpf)

        self._err = _lbl("", "err"); self._err.hide()
        lay.addWidget(self._err)

        self._rb = QPushButton("RESET PASSWORD")
        self._rb.setObjectName("primary")
        self._rb.setMinimumHeight(40)
        self._rb.setEnabled(False)
        self._rb.setCursor(Qt.CursorShape.PointingHandCursor)
        self._rb.clicked.connect(self._reset)
        lay.addWidget(self._rb)

    def _send(self):
        email = self._ef.text().strip().lower()
        if not _EMAIL_RE.match(email): self._show("Invalid email."); return
        if not get_user_by_email(email): self._show("No account found."); return
        fb = _send_code(email, "", "reset")
        self._pending = email
        for w in (self._cf, self._pf, self._cpf): w.setEnabled(True)
        self._rb.setEnabled(True)
        self._show(f"Code sent." if not fb else f"Dev code: {fb}", ok=True)

    def _reset(self):
        c, p, cp = self._cf.text().strip(), self._pf.text(), self._cpf.text()
        if len(c) != 5: self._show("Enter the 5-digit code."); return
        if len(p) < 8:  self._show("Password min 8 chars."); return
        if p != cp:     self._show("Passwords don't match."); return
        if not verify_code(self._pending, c, "reset"): self._show("Invalid code."); return
        update_password(self._pending, p)
        QMessageBox.information(self, "Done", "Password reset. Log in now.")
        self.accept()

    def _show(self, m, ok=False):
        self._err.setText(m)
        self._err.setStyleSheet(f"color:{'#3fae6a' if ok else '#e0564f'};font-size:7px;")
        self._err.show()


# ── register dialog ───────────────────────────────────────────────────────────

class _RegisterDlg(QDialog):
    registered = pyqtSignal(dict, str)

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Dialog)
        self.setWindowTitle("Create Account")
        self.setFixedSize(420, 470)
        self.setStyleSheet(_qss())

        lay = QVBoxLayout(self)
        lay.setContentsMargins(34, 28, 34, 28)
        lay.setSpacing(9)

        lay.addWidget(_lbl("CREATE ACCOUNT", "h1", center=True))
        lay.addSpacing(6)

        self._nf = _input("Full name")
        self._ef = _input("Email address")
        self._pf = _input("Password (min 8)", pw=True)
        self._cf = _input("Confirm password", pw=True)
        for t, w in [("Name", self._nf), ("Email", self._ef),
                     ("Password", self._pf), ("Confirm", self._cf)]:
            lay.addWidget(_lbl(t, "lbl")); lay.addWidget(w)

        self._err = _lbl("", "err"); self._err.hide()
        lay.addWidget(self._err)

        btn = QPushButton("CREATE ACCOUNT")
        btn.setObjectName("primary")
        btn.setMinimumHeight(42)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._register)
        lay.addWidget(btn)

    def _register(self):
        name  = self._nf.text().strip()
        email = self._ef.text().strip().lower()
        p, cp = self._pf.text(), self._cf.text()
        if not name:                   self._show("Enter your full name."); return
        if not _EMAIL_RE.match(email): self._show("Enter a valid email."); return
        if get_user_by_email(email):   self._show("Account already exists."); return
        if len(p) < 8:                 self._show("Password min 8 chars."); return
        if p != cp:                    self._show("Passwords don't match."); return
        create_user(email, name, p)
        fb = _send_code(email, name, "verify")
        if _CodeDlg(email, "verify", fb, self).exec() == QDialog.DialogCode.Accepted:
            mark_verified(email)
            user = get_user_by_email(email)
            token = create_session(user["id"])
            self.registered.emit(dict(user), token)
            self.accept()

    def _show(self, m):
        self._err.setText(m); self._err.show()


# ── Login Window ──────────────────────────────────────────────────────────────

class LoginWindow(QMainWindow):
    login_success = pyqtSignal(dict, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ArchForge Pro")
        self.setStyleSheet(_qss())
        geo = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(geo)
        self._build_ui()

    def _build_ui(self):
        root = QWidget()
        root.setStyleSheet("background-color:#000000;")
        self.setCentralWidget(root)
        self._root = root

        # interactive node-field background (sits behind everything)
        self._bg = NodeFieldBackground(root, dark=True)
        self._bg.lower()

        page = QVBoxLayout(root)
        page.setContentsMargins(0, 0, 0, 0)
        page.setSpacing(0)
        page.addStretch(1)

        # ── card ──────────────────────────────────────────────────────────────
        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(384)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(30, 30, 30, 26)
        cl.setSpacing(0)

        cl.addWidget(_lbl("Welcome back", "h1", center=True))
        cl.addSpacing(12)
        sub = _lbl("Login with your Apple or Google account", "sub", center=True)
        sub.setWordWrap(True)
        sub.setFixedWidth(230)
        sub_row = QHBoxLayout(); sub_row.addStretch(); sub_row.addWidget(sub); sub_row.addStretch()
        cl.addLayout(sub_row)
        cl.addSpacing(18)

        # Apple
        apple = QPushButton("  Login with Apple")
        apple.setObjectName("oauth")
        apple.setIcon(QIcon(apple_icon(18, "#ffffff")))
        apple.setIconSize(QSize(18, 18))
        apple.setMinimumHeight(42)
        apple.setEnabled(False)
        apple.setToolTip("Apple sign-in is not available on Windows")
        cl.addWidget(apple)
        cl.addSpacing(10)

        # Google
        google = QPushButton("  Login with Google")
        google.setObjectName("oauth")
        google.setIcon(QIcon(google_icon(18)))
        google.setIconSize(QSize(18, 18))
        google.setMinimumHeight(42)
        google.setEnabled(False)
        google.setToolTip("Google sign-in coming soon")
        cl.addWidget(google)
        cl.addSpacing(16)

        # Or continue with
        orr = QHBoxLayout(); orr.setSpacing(10)
        orr.addWidget(_hline(), 1)
        orr.addWidget(_lbl("Or continue with", "or"))
        orr.addWidget(_hline(), 1)
        cl.addLayout(orr)
        cl.addSpacing(16)

        # Email
        cl.addWidget(_lbl("Email", "lbl"))
        cl.addSpacing(7)
        self._email_f = _input("m@example.com")
        cl.addWidget(self._email_f)
        cl.addSpacing(14)

        # Password + forgot
        pw_row = QHBoxLayout(); pw_row.setContentsMargins(0, 0, 0, 0)
        pw_row.addWidget(_lbl("Password", "lbl"))
        pw_row.addStretch()
        forgot = QPushButton("Forgot password?")
        forgot.setObjectName("link")
        forgot.setCursor(Qt.CursorShape.PointingHandCursor)
        forgot.clicked.connect(lambda: _ForgotDlg(self).exec())
        pw_row.addWidget(forgot)
        cl.addLayout(pw_row)
        cl.addSpacing(7)
        self._pass_f = _input("", pw=True)
        self._pass_f.returnPressed.connect(self._login)
        cl.addWidget(self._pass_f)
        cl.addSpacing(10)

        self._err = _lbl("", "err", center=True)
        self._err.hide()
        cl.addWidget(self._err)
        cl.addSpacing(6)

        # Login
        login_btn = QPushButton("Login")
        login_btn.setObjectName("primary")
        login_btn.setMinimumHeight(44)
        login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        login_btn.clicked.connect(self._login)
        cl.addWidget(login_btn)
        cl.addSpacing(18)

        # Sign up
        su = QHBoxLayout(); su.setAlignment(Qt.AlignmentFlag.AlignCenter); su.setSpacing(6)
        su.addWidget(_lbl("Don't have an account?", "sub"))
        su_btn = QPushButton("Sign up")
        su_btn.setObjectName("link")
        su_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        su_btn.clicked.connect(self._signup)
        su.addWidget(su_btn)
        cl.addLayout(su)

        hc = QHBoxLayout(); hc.addStretch(1); hc.addWidget(card); hc.addStretch(1)
        page.addLayout(hc)
        page.addStretch(1)

        # ── footer (outside card) ───────────────────────────────────────────
        f1 = _lbl("Terms of Service", "foot", center=True)
        f2 = _lbl("and Privacy Policy.", "foot", center=True)
        f1.setStyleSheet("text-decoration:underline;")
        f2.setStyleSheet("text-decoration:underline;")
        page.addWidget(f1)
        page.addSpacing(3)
        page.addWidget(f2)
        page.addSpacing(26)

    def resizeEvent(self, event):  # type: ignore[override]
        super().resizeEvent(event)
        if hasattr(self, "_bg") and hasattr(self, "_root"):
            self._bg.setGeometry(0, 0, self._root.width(), self._root.height())
            self._bg.lower()

    # ── actions ───────────────────────────────────────────────────────────────

    def _login(self):
        email = self._email_f.text().strip().lower()
        pw = self._pass_f.text()
        if not email or not pw:
            self._show_err("Enter your email and password."); return
        user = get_user_by_email(email)
        if not user:
            self._show_err("No account found with that email."); return
        if not verify_password(pw, user["password_hash"], user["salt"]):
            self._show_err("Incorrect password."); return
        if not user["is_verified"]:
            self._show_err("Email not verified. Sign up again."); return
        token = create_session(user["id"])
        self.login_success.emit(dict(user), token)

    def _signup(self):
        dlg = _RegisterDlg(self)
        dlg.registered.connect(self.login_success.emit)
        dlg.exec()

    def _show_err(self, m):
        self._err.setText(m); self._err.show()
