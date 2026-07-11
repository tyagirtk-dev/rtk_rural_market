import secrets
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app

from models import db
from models.otp import OTP, PasswordResetToken
from services.sms_service import send_otp_sms


def issue_otp(mobile_number, purpose):
    """Invalidate previous unused OTPs of this purpose for the number, create + send a new one."""
    OTP.query.filter_by(mobile_number=mobile_number, purpose=purpose, is_used=False).update(
        {"is_used": True}
    )

    code = OTP.generate_code()
    expiry_minutes = current_app.config.get("OTP_EXPIRY_MINUTES", 5)
    otp = OTP(
        mobile_number=mobile_number,
        code_hash=generate_password_hash(code),
        purpose=purpose,
        expires_at=datetime.utcnow() + timedelta(minutes=expiry_minutes),
    )
    db.session.add(otp)
    db.session.commit()

    send_otp_sms(mobile_number, code, purpose=purpose)
    return otp


def verify_otp(mobile_number, code, purpose):
    """Returns (success: bool, error_message: str)."""
    otp = (
        OTP.query.filter_by(mobile_number=mobile_number, purpose=purpose, is_used=False)
        .order_by(OTP.created_at.desc())
        .first()
    )
    if not otp:
        return False, "No active OTP found. Please request a new one."
    if otp.is_expired():
        return False, "This OTP has expired. Please request a new one."
    if otp.attempts >= otp.max_attempts:
        return False, "Too many incorrect attempts. Please request a new OTP."

    if not check_password_hash(otp.code_hash, code):
        otp.attempts += 1
        db.session.commit()
        return False, "Incorrect OTP. Please try again."

    otp.is_used = True
    db.session.commit()
    return True, ""


def issue_password_reset_token(user):
    token = secrets.token_urlsafe(40)
    reset = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(minutes=15),
    )
    db.session.add(reset)
    db.session.commit()
    return token


def consume_password_reset_token(token):
    reset = PasswordResetToken.query.filter_by(token=token, is_used=False).first()
    if not reset or not reset.is_valid():
        return None
    reset.is_used = True
    db.session.commit()
    return reset.user_id
