from flask import Blueprint, render_template, redirect, url_for, jsonify
from flask_login import login_required, current_user

from models import db
from models.notification import Notification

notifications_bp = Blueprint("notifications", __name__, template_folder="../templates/customer")


@notifications_bp.route("/")
@login_required
def center():
    items = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return render_template("customer/notifications.html", notifications=items)


@notifications_bp.route("/unread-count")
@login_required
def unread_count():
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({"count": count})


@notifications_bp.route("/<int:notification_id>/read", methods=["POST"])
@login_required
def mark_read(notification_id):
    note = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first_or_404()
    note.is_read = True
    db.session.commit()
    return redirect(note.link or url_for("notifications.center"))
