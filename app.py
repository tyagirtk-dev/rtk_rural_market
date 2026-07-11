import os
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template, request
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import config_by_name
from models import db

login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=[])


def create_app(env=None):
    env = env or os.environ.get("FLASK_ENV", "production")
    app = Flask(__name__)
    app.config.from_object(config_by_name.get(env, config_by_name["production"]))

    _configure_logging(app)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to continue."
    login_manager.login_message_category = "info"

    csrf.init_app(app)
    limiter.init_app(app)

    from routes import register_blueprints
    register_blueprints(app)

    _register_error_handlers(app)
    _register_context_processors(app)
    _register_user_loader()

    with app.app_context():
        os.makedirs(os.path.dirname(app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")) or ".", exist_ok=True)
        db.create_all()
        _bootstrap_admin(app)
        _bootstrap_categories()

    return app


def _configure_logging(app):
    log_dir = os.path.join(app.root_path, "logs")
    os.makedirs(log_dir, exist_ok=True)
    handler = RotatingFileHandler(os.path.join(log_dir, "app.log"), maxBytes=1_000_000, backupCount=3)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    logging.getLogger("rtk.sms").addHandler(RotatingFileHandler(
        os.path.join(log_dir, "otp.log"), maxBytes=500_000, backupCount=2))


def _register_user_loader():
    from models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))


def _register_error_handlers(app):
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def too_large(e):
        return render_template("errors/413.html"), 413

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("Unhandled server error")
        return render_template("errors/500.html"), 500


def _register_context_processors(app):
    from datetime import datetime
    from models.product import Category
    from flask_login import current_user

    @app.context_processor
    def inject_globals():
        unread = 0
        if current_user.is_authenticated:
            from models.notification import Notification
            unread = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        nav_categories = Category.query.filter_by(is_active=True).order_by(Category.sort_order).limit(10).all()
        return {
            "nav_categories": nav_categories,
            "unread_notification_count": unread,
            "site_name": "RTK Rural Market",
            "now": datetime.utcnow,
        }


def _bootstrap_admin(app):
    from models.user import User

    mobile = app.config["ADMIN_MOBILE"]
    existing = User.query.filter_by(mobile_number=mobile).first()
    if existing:
        return
    admin = User(
        full_name="Admin",
        mobile_number=mobile,
        email=app.config["ADMIN_EMAIL"],
        is_admin=True,
        mobile_verified=True,
        is_active_account=True,
    )
    admin.set_password(app.config["ADMIN_PASSWORD"])
    db.session.add(admin)
    db.session.commit()
    app.logger.info("Bootstrapped admin account for mobile %s", mobile)


def _bootstrap_categories():
    from models.product import Category
    from utils.helpers import unique_slug

    if Category.query.count() > 0:
        return

    defaults = [
        ("Milk", "bi-cup-straw"), ("Ghee", "bi-droplet"), ("Paneer", "bi-square"),
        ("Curd", "bi-circle"), ("Butter", "bi-square-fill"), ("Honey", "bi-flower1"),
        ("Vegetables", "bi-basket"), ("Jaggery", "bi-hexagon"), ("Pickles", "bi-jar"),
        ("Seasonal Products", "bi-calendar3"),
    ]
    for i, (name, icon) in enumerate(defaults):
        db.session.add(Category(name=name, slug=unique_slug(Category, name), icon=icon, sort_order=i))
    db.session.commit()


if __name__ == "__main__":
    app = create_app(os.environ.get("FLASK_ENV", "development"))
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=app.config.get("DEBUG", False))
