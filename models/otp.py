import random
from datetime import datetime, timedelta
from . import db


class OTP(db.Model):
    """Generic OTP store, used for both signup verification and forgot-password identity checks."""
    __tablename__ = "otps"

    id = db.Column(db.Integer, primary_key=True)
    mobile_number = db.Column(db.String(15), nullable=False, index=True)
    code_hash = db.Column(db.String(255), nullable=False)
    purpose = db.Column(db.String(30), nullable=False)  # 'signup' or 'password_reset'
    attempts = db.Column(db.Integer, default=0, nullable=False)
    max_attempts = db.Column(db.Integer, default=5, nullable=False)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

    @staticmethod
    def generate_code():
        return f"{random.randint(0, 999999):06d}"

    def is_expired(self):
        return datetime.utcnow() > self.expires_at

    def is_valid(self):
        return (not self.is_used) and (not self.is_expired()) and self.attempts < self.max_attempts


class PasswordResetToken(db.Model):
    """Short-lived token issued after OTP verification, used to authorize the actual password change."""
    __tablename__ = "password_reset_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

    def is_valid(self):
        return (not self.is_used) and datetime.utcnow() <= self.expires_at
