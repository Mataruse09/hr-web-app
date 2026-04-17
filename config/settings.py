import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ── Security ────────────────────────────────────────────
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-in-production-use-long-random-string')

    # ── MySQL (Railway) ─────────────────────────────────────
    DB_HOST     = os.getenv('DB_HOST', 'mysql.railway.internal')
    DB_USER     = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME     = os.getenv('DB_NAME', 'railway')
    DB_PORT     = int(os.getenv('DB_PORT', 3306))

    # Full connection URL support (MySQL format)
    DATABASE_URL = os.getenv('DATABASE_URL')

    # ── Session ──────────────────────────────────────────────
    SESSION_PERMANENT          = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_HTTPONLY    = True
    SESSION_COOKIE_SAMESITE    = 'Lax'