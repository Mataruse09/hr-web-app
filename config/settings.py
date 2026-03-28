import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ── Security ────────────────────────────────────────────
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-in-production-use-long-random-string')

    # ── MySQL ────────────────────────────────────────────────
    MYSQL_HOST     = os.getenv('MYSQL_HOST',     'localhost')
    MYSQL_USER     = os.getenv('MYSQL_USER',     'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DB       = os.getenv('MYSQL_DB',       'hr_system')
    MYSQL_PORT     = int(os.getenv('MYSQL_PORT', 3306))

    # ── Session ──────────────────────────────────────────────
    SESSION_PERMANENT            = True
    PERMANENT_SESSION_LIFETIME   = timedelta(hours=8)
    SESSION_COOKIE_HTTPONLY      = True
    SESSION_COOKIE_SAMESITE      = 'Lax'