"""
SMTP email service.

Requires real SMTP_* values in .env to actually deliver mail (see .env.example).
Without them, sends are logged and skipped rather than raising, so the rest of
the app keeps working in a fresh checkout.
"""
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import current_app, render_template

logger = logging.getLogger("rtk.email")


def _send_raw(to_email, subject, html_body, text_body=None):
    cfg = current_app.config
    if not cfg.get("SMTP_HOST") or not cfg.get("SMTP_USERNAME"):
        logger.warning("SMTP not configured; skipping email to %s (subject: %s)", to_email, subject)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{cfg['SMTP_FROM_NAME']} <{cfg['SMTP_FROM_EMAIL']}>"
    msg["To"] = to_email

    if text_body:
        msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(cfg["SMTP_HOST"], cfg["SMTP_PORT"], timeout=15) as server:
            if cfg.get("SMTP_USE_TLS", True):
                server.starttls()
            server.login(cfg["SMTP_USERNAME"], cfg["SMTP_PASSWORD"])
            server.sendmail(cfg["SMTP_FROM_EMAIL"], [to_email], msg.as_string())
        return True
    except Exception:
        logger.exception("Failed to send email to %s", to_email)
        return False


def send_welcome_email(user):
    if not user.email:
        return False
    html = render_template("emails/welcome.html", user=user)
    return _send_raw(user.email, "Welcome to RTK Rural Market", html)


def send_order_confirmation_email(user, order):
    if not user.email:
        return False
    html = render_template("emails/order_confirmation.html", user=user, order=order)
    return _send_raw(user.email, f"Order Confirmed - {order.order_number}", html)


def send_order_status_update_email(user, order):
    if not user.email:
        return False
    html = render_template("emails/order_status_update.html", user=user, order=order)
    status_label = order.status.replace("_", " ").title()
    return _send_raw(user.email, f"Order {order.order_number} - {status_label}", html)


def send_password_changed_email(user):
    if not user.email:
        return False
    html = render_template("emails/password_changed.html", user=user)
    return _send_raw(user.email, "Your password was changed", html)


def send_contact_form_email(contact_message):
    cfg = current_app.config
    receiver = cfg.get("CONTACT_FORM_RECEIVER")
    if not receiver:
        return False
    html = render_template("emails/contact_notification.html", msg=contact_message)
    return _send_raw(receiver, f"New Contact Message: {contact_message.subject or 'General'}", html)


def send_admin_notification_email(subject, body_text):
    cfg = current_app.config
    receiver = cfg.get("CONTACT_FORM_RECEIVER")
    if not receiver:
        return False
    html = f"<pre style='font-family:inherit;white-space:pre-wrap;'>{body_text}</pre>"
    return _send_raw(receiver, subject, html)
