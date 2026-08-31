import os
import secrets

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Fail loudly in production if no SECRET_KEY is set; fall back to a random
    # per-process key in dev so the app is never left with a hardcoded default.
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:////tmp/hectorhosting.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Session / cookie hardening ---
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("FORCE_HTTPS", "true").lower() == "true"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 2  # 2 hours

    # --- CSRF ---
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

    FORCE_HTTPS = os.environ.get("FORCE_HTTPS", "true").lower() == "true"
    CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "support@hectorhosting.example")
