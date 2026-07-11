from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    mobile_number = db.Column(db.String(15), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active_account = db.Column(db.Boolean, default=True, nullable=False)
    mobile_verified = db.Column(db.Boolean, default=False, nullable=False)

    dark_mode = db.Column(db.Boolean, default=False, nullable=False)
    marketing_opt_in = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)  # soft delete

    addresses = db.relationship("Address", backref="user", lazy="dynamic",
                                 cascade="all, delete-orphan")
    orders = db.relationship("Order", backref="customer", lazy="dynamic")
    notifications = db.relationship("Notification", backref="user", lazy="dynamic",
                                     cascade="all, delete-orphan")
    wishlist_items = db.relationship("Product", secondary="wishlist", lazy="dynamic")

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    # Flask-Login uses get_id() -> str; keep default (uses .id) but guard soft delete.
    @property
    def is_active(self):
        return self.is_active_account and self.deleted_at is None

    def __repr__(self):
        return f"<User {self.mobile_number}>"


wishlist = db.Table(
    "wishlist",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("product_id", db.Integer, db.ForeignKey("products.id"), primary_key=True),
    db.Column("added_at", db.DateTime, default=datetime.utcnow),
)


class Address(db.Model):
    __tablename__ = "addresses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    label = db.Column(db.String(50), default="Home")  # Home / Work / Other
    full_address = db.Column(db.String(300), nullable=False)
    city = db.Column(db.String(100), nullable=False, index=True)
    pin_code = db.Column(db.String(10), nullable=False)
    landmark = db.Column(db.String(150))
    is_default = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DeviceSession(db.Model):
    """Tracks active login sessions so 'logout from all devices' can work."""
    __tablename__ = "device_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    session_token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_agent = db.Column(db.String(255))
    ip_address = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen_at = db.Column(db.DateTime, default=datetime.utcnow)
    revoked = db.Column(db.Boolean, default=False, nullable=False)
