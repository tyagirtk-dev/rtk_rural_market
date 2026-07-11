from models import db
from models.order import OrderStatusHistory
from services.notification_service import notify_user
from services.email_service import send_order_status_update_email
from services.audit_service import log_action


STATUS_MESSAGES = {
    "pending": "Your order has been received and is awaiting confirmation.",
    "confirmed": "Your order has been confirmed and will be prepared soon.",
    "packed": "Your order has been packed and is ready for delivery.",
    "out_for_delivery": "Your order is out for delivery.",
    "delivered": "Your order has been delivered. Enjoy!",
    "cancelled": "Your order has been cancelled.",
}


def update_order_status(order, new_status, changed_by="admin", note=None):
    order.status = new_status
    db.session.add(OrderStatusHistory(
        order_id=order.id, status=new_status, note=note, changed_by=changed_by
    ))
    db.session.commit()

    customer = order.customer
    friendly = STATUS_MESSAGES.get(new_status, f"Order status updated to {new_status}.")
    notify_user(
        customer.id,
        title=f"Order {order.order_number} - {new_status.replace('_', ' ').title()}",
        message=friendly,
        category="order",
        link=f"/orders/{order.order_number}",
    )
    send_order_status_update_email(customer, order)
    log_action(changed_by, "order_status_change", f"Order {order.order_number} -> {new_status}")
