import secrets
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user

from models import db
from models.user import User, DeviceSession
from forms.auth_forms import (
    RegistrationForm, OTPVerifyForm, LoginForm,
    ForgotPasswordRequestForm, ForgotPasswordVerifyForm, ResetPasswordForm
)
from services.otp_service import issue_otp, verify_otp, issue_password_reset_token, consume_password_reset_token
from services.email_service import send_welcome_email, send_password_changed_email
from services.notification_service import notify_user
from services.audit_service import log_action
from app import limiter

auth_bp = Blueprint("auth", __name__, template_folder="../templates/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = RegistrationForm()
    if form.validate_on_submit():
        mobile = form.mobile_number.data.strip()
        email = form.email.data.strip().lower()

        if User.query.filter_by(mobile_number=mobile).first():
            flash("An account with this mobile number already exists.", "danger")
            return render_template("auth/register.html", form=form)
        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return render_template("auth/register.html", form=form)

        # Stash pending signup details in the session; account is only created after OTP success.
        session["pending_signup"] = {
            "full_name": form.full_name.data.strip(),
            "mobile_number": mobile,
            "email": email,
            "password": form.password.data,  # only held transiently in server-side session
        }
        issue_otp(mobile, purpose="signup")
        flash("An OTP has been sent to your mobile number.", "info")
        return redirect(url_for("auth.verify_signup_otp"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/register/verify-otp", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
def verify_signup_otp():
    pending = session.get("pending_signup")
    if not pending:
        flash("Please start registration again.", "warning")
        return redirect(url_for("auth.register"))

    form = OTPVerifyForm()
    if form.validate_on_submit():
        ok, error = verify_otp(pending["mobile_number"], form.otp_code.data.strip(), purpose="signup")
        if not ok:
            flash(error, "danger")
            return render_template("auth/verify_otp.html", form=form, mobile=pending["mobile_number"])

        user = User(
            full_name=pending["full_name"],
            mobile_number=pending["mobile_number"],
            email=pending["email"],
            mobile_verified=True,
        )
        user.set_password(pending["password"])
        db.session.add(user)
        db.session.commit()

        session.pop("pending_signup", None)
        login_user(user, remember=True)
        _register_device_session(user)

        notify_user(user.id, "Welcome to RTK Rural Market!",
                    "Your account is ready. Start pre-booking fresh village products today.",
                    category="account")
        send_welcome_email(user)
        log_action(user.mobile_number, "signup", "New account created")

        flash("Account created successfully. Welcome!", "success")
        return redirect(url_for("main.home"))

    return render_template("auth/verify_otp.html", form=form, mobile=pending["mobile_number"])


@auth_bp.route("/register/resend-otp")
@limiter.limit("5 per hour")
def resend_signup_otp():
    pending = session.get("pending_signup")
    if not pending:
        return redirect(url_for("auth.register"))
    issue_otp(pending["mobile_number"], purpose="signup")
    flash("A new OTP has been sent.", "info")
    return redirect(url_for("auth.verify_signup_otp"))


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("15 per hour", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = LoginForm()
    if request.method == "POST":
        print("LOGIN FORM ERRORS:", form.errors)
    if form.validate_on_submit():
        mobile = form.mobile_number.data.strip()
        user = User.query.filter_by(mobile_number=mobile, deleted_at=None).first()

        if not user or not user.check_password(form.password.data):
            log_action(mobile, "login_failed", "Invalid credentials")
            flash("Invalid mobile number or password.", "danger")
            return render_template("auth/login.html", form=form)

        if not user.is_active_account:
            flash("Your account is deactivated. Please contact support.", "danger")
            return render_template("auth/login.html", form=form)

        login_user(user, remember=form.remember_me.data)
        _register_device_session(user)
        log_action(user.mobile_number, "login", "Successful login")
        flash(f"Welcome back, {user.full_name.split()[0]}!", "success")

        next_page = request.args.get("next")
        return redirect(next_page or url_for("main.home"))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    log_action(current_user.mobile_number, "logout", "User logged out")
    logout_user()
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.home"))


@auth_bp.route("/logout-all-devices")
@login_required
def logout_all_devices():
    DeviceSession.query.filter_by(user_id=current_user.id).update({"revoked": True})
    db.session.commit()
    log_action(current_user.mobile_number, "logout_all_devices", "All sessions revoked")
    logout_user()
    session.clear()
    flash("You have been logged out from all devices.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
def forgot_password():
    form = ForgotPasswordRequestForm()
    if form.validate_on_submit():
        mobile = form.mobile_number.data.strip()
        user = User.query.filter_by(mobile_number=mobile, deleted_at=None).first()
        if not user:
            flash("No account found with this mobile number.", "danger")
            return render_template("auth/forgot_password.html", form=form)

        issue_otp(mobile, purpose="password_reset")
        session["reset_mobile"] = mobile
        flash("An OTP has been sent to your mobile number.", "info")
        return redirect(url_for("auth.forgot_password_verify"))

    return render_template("auth/forgot_password.html", form=form)


@auth_bp.route("/forgot-password/verify", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
def forgot_password_verify():
    mobile = session.get("reset_mobile")
    if not mobile:
        return redirect(url_for("auth.forgot_password"))

    form = ForgotPasswordVerifyForm()
    if form.validate_on_submit():
        ok, error = verify_otp(mobile, form.otp_code.data.strip(), purpose="password_reset")
        if not ok:
            flash(error, "danger")
            return render_template("auth/forgot_password_verify.html", form=form, mobile=mobile)

        user = User.query.filter_by(mobile_number=mobile).first()
        token = issue_password_reset_token(user)
        session.pop("reset_mobile", None)
        return redirect(url_for("auth.reset_password", token=token))

    return render_template("auth/forgot_password_verify.html", form=form, mobile=mobile)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user_id = consume_password_reset_token(token)
        if not user_id:
            flash("This reset link is invalid or has expired. Please try again.", "danger")
            return redirect(url_for("auth.forgot_password"))

        user = User.query.get(user_id)
        user.set_password(form.new_password.data)
        db.session.commit()

        notify_user(user.id, "Password Changed", "Your password was changed successfully.", category="account")
        send_password_changed_email(user)
        log_action(user.mobile_number, "password_reset", "Password reset via OTP flow")

        flash("Your password has been reset. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", form=form, token=token)


def _register_device_session(user):
    token = secrets.token_hex(32)
    session["device_token"] = token
    entry = DeviceSession(
        user_id=user.id,
        session_token=token,
        user_agent=request.headers.get("User-Agent", "")[:255],
        ip_address=request.remote_addr,
    )
    db.session.add(entry)
    db.session.commit()
