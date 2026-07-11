from flask import request
from models import db
from models.misc import AuditLog


def log_action(actor, action, details=""):
    try:
        ip = request.remote_addr if request else None
    except RuntimeError:
        ip = None
    entry = AuditLog(actor=actor or "system", action=action, details=details, ip_address=ip)
    db.session.add(entry)
    db.session.commit()
    return entry
