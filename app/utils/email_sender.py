"""SMTP email sender — reads config from settings table or config.py fallback."""
from __future__ import annotations
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


def _load_smtp_config() -> dict | None:
    """Return SMTP config dict from config.py, then DB settings, or None."""
    # 1. Try config.py (developer override, gitignored)
    try:
        import config as cfg
        return {
            "host": getattr(cfg, "SMTP_HOST", "smtp.gmail.com"),
            "port": int(getattr(cfg, "SMTP_PORT", 587)),
            "user": cfg.SMTP_USER,
            "password": cfg.SMTP_PASS,
        }
    except (ImportError, AttributeError):
        pass

    # 2. Try DB settings
    try:
        from app.models.settings_model import get_setting
        user = get_setting("smtp_user", "")
        pwd  = get_setting("smtp_pass", "")
        if user and pwd:
            return {
                "host": get_setting("smtp_host", "smtp.gmail.com"),
                "port": int(get_setting("smtp_port", "587")),
                "user": user,
                "password": pwd,
            }
    except Exception:
        pass

    return None


def send_email(to: str, subject: str, body_html: str) -> bool:
    """Send an HTML email. Returns True on success, False on failure."""
    cfg = _load_smtp_config()
    if not cfg:
        logger.warning("SMTP not configured — email not sent")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = cfg["user"]
    msg["To"]      = to
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=10) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(cfg["user"], cfg["password"])
            smtp.sendmail(cfg["user"], to, msg.as_string())
        logger.info("Email sent to %s [%s]", to, subject)
        return True
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to, exc)
        return False


def smtp_configured() -> bool:
    return _load_smtp_config() is not None


# ── Email templates ───────────────────────────────────────────────────────────

_BASE = """
<div style="background:#000;padding:40px 0;font-family:'Courier New',monospace;">
  <div style="max-width:480px;margin:0 auto;background:#0a0a0a;border:1px solid #222;padding:40px;">
    <p style="color:#444;font-size:10px;letter-spacing:3px;margin:0 0 24px">
      ARCHFORGE PRO  //  CONSTRUCTION COST ESTIMATION SYSTEM
    </p>
    {content}
    <hr style="border:none;border-top:1px solid #1a1a1a;margin:32px 0"/>
    <p style="color:#333;font-size:9px;letter-spacing:2px;margin:0">
      This email was sent by ArchForge Pro. Do not reply.
    </p>
  </div>
</div>
"""


def verification_email(name: str, code: str) -> str:
    content = f"""
    <h1 style="color:#fff;font-size:22px;letter-spacing:4px;margin:0 0 8px">
      VERIFY YOUR EMAIL
    </h1>
    <p style="color:#555;font-size:11px;letter-spacing:2px;margin:0 0 32px">
      Welcome, {name}. Enter this code to activate your account.
    </p>
    <div style="background:#111;border:1px solid #222;padding:28px;text-align:center;margin:0 0 24px">
      <span style="color:#fff;font-size:38px;letter-spacing:16px;font-weight:700">
        {code}
      </span>
    </div>
    <p style="color:#444;font-size:10px;letter-spacing:1px;margin:0">
      This code expires in 15 minutes. If you did not create an account, ignore this email.
    </p>
    """
    return _BASE.format(content=content)


def reset_email(code: str) -> str:
    content = f"""
    <h1 style="color:#fff;font-size:22px;letter-spacing:4px;margin:0 0 8px">
      RESET PASSWORD
    </h1>
    <p style="color:#555;font-size:11px;letter-spacing:2px;margin:0 0 32px">
      Use this code to reset your ArchForge Pro password.
    </p>
    <div style="background:#111;border:1px solid #222;padding:28px;text-align:center;margin:0 0 24px">
      <span style="color:#fff;font-size:38px;letter-spacing:16px;font-weight:700">
        {code}
      </span>
    </div>
    <p style="color:#444;font-size:10px;letter-spacing:1px;margin:0">
      This code expires in 15 minutes. If you did not request a reset, ignore this email.
    </p>
    """
    return _BASE.format(content=content)
