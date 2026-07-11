from datetime import datetime
from . import db


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    mobile = db.Column(db.String(15))
    subject = db.Column(db.String(150))
    message = db.Column(db.Text, nullable=False)
    is_resolved = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class City(db.Model):
    __tablename__ = "cities"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)


class DeliverySchedule(db.Model):
    __tablename__ = "delivery_schedules"

    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100), nullable=False, index=True)
    delivery_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.String(255))
    is_locked = db.Column(db.Boolean, default=False)  # locked = no more orders added to this run
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    actor = db.Column(db.String(120))  # mobile number or 'system'
    action = db.Column(db.String(120), nullable=False)  # e.g. 'login', 'order_status_change'
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


class SiteSetting(db.Model):
    """Simple key/value store for admin-editable website settings."""
    __tablename__ = "site_settings"

    key = db.Column(db.String(80), primary_key=True)
    value = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get(key, default=None):
        row = SiteSetting.query.get(key)
        return row.value if row else default

    @staticmethod
    def set(key, value):
        row = SiteSetting.query.get(key)
        if row:
            row.value = value
        else:
            row = SiteSetting(key=key, value=value)
            db.session.add(row)
