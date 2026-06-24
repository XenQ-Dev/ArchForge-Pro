# config.example.py — copy this to config.py and fill in your values
# config.py is gitignored and never committed.
#
# SMTP — used to send verification and password-reset emails.
# For Gmail: enable 2FA on your Google account, then create an App Password at
#   https://myaccount.google.com/apppasswords
# Use that App Password (16 chars, no spaces) as SMTP_PASS.

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "your-app-email@gmail.com"
SMTP_PASS = "xxxx xxxx xxxx xxxx"   # Gmail App Password

# Without config.py, ArchForge Pro runs in dev mode:
# verification codes are shown on-screen instead of being emailed.
