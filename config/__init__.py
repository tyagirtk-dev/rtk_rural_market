"""
Application configuration.

All secrets and environment-specific values are read from environment
variables (see .env.example). Nothing sensitive is hard-coded here.
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def _bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in ("1", "true", "yes", "on")


class Config:
    # --- Core ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-key-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'database', 'rtk_rural_market.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Uploads ---
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    MAX_CONTENT_LENGTH = 6 * 1024 * 1024  # 6 MB per request
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

    # --- Sessions / cookies ---
    PERMANENT_SESSION_LIFETIME = timedelta(days=14)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _bool(os.environ.get("SESSION_COOKIE_SECURE"), default=False)
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    REMEMBER_COOKIE_HTTPONLY = True

    # --- Admin bootstrap ---
    ADMIN_MOBILE = os.environ.get("ADMIN_MOBILE", "9999999999")
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@rtkruralmarket.com")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

    # --- SMTP ---
    SMTP_HOST = os.environ.get("SMTP_HOST", "")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
    SMTP_USE_TLS = _bool(os.environ.get("SMTP_USE_TLS"), default=True)
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_FROM_NAME = os.environ.get("SMTP_FROM_NAME", "RTK Rural Market")
    SMTP_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL", SMTP_USERNAME)
    CONTACT_FORM_RECEIVER = os.environ.get("CONTACT_FORM_RECEIVER", SMTP_USERNAME)

    # --- SMS ---
    SMS_PROVIDER = os.environ.get("SMS_PROVIDER", "console")
    SMS_API_KEY = os.environ.get("SMS_API_KEY", "")
    SMS_API_SECRET = os.environ.get("SMS_API_SECRET", "")
    SMS_SENDER_ID = os.environ.get("SMS_SENDER_ID", "RTKRML")

    UPI_ID = os.environ.get("UPI_ID", "rtk0097-1@okhdfcbank")
    UPI_NAME = os.environ.get("UPI_NAME", "RTK Rural")

    # --- App-level settings ---
    BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:5000")
    DELIVERY_CHARGE = float(os.environ.get("DELIVERY_CHARGE", 40))
    FREE_DELIVERY_THRESHOLD = float(os.environ.get("FREE_DELIVERY_THRESHOLD", 500))
    OTP_EXPIRY_MINUTES = int(os.environ.get("OTP_EXPIRY_MINUTES", 5))

    # --- Rate limiting ---
    RATELIMIT_STORAGE_URI = "memory://"


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
