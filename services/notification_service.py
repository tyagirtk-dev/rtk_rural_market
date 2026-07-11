from models import db
from models.notification import Notification


def notify_user(user_id, title, message, category="general", link=None):
    note = Notification(
        user_id=user_id,
        title=title,
        message=message,
        category=category,
        link=link,
    )
    db.session.add(note)
    db.session.commit()
    return note


def unread_count(user_id):
    return Notification.query.filter_by(user_id=user_id, is_read=False).count()
