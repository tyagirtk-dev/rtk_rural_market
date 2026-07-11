import random
import string
from datetime import datetime
from . import db

ORDER_STATUSES = ["pending", "confirmed", "packed", "out_for_delivery", "delivered", "cancelled"]


def generate_order_number():
    return "RTK" + "".join(random.choices(string.digits, k=8))


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False, default=generate_order_number)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    # snapshot of delivery details at time of order (address may change later)
    full_address = db.Column(db.String(300), nullable=False)
    city = db.Column(db.String(100), nullable=False, index=True)
    pin_code = db.Column(db.String(10), nullable=False)
    contact_mobile = db.Column(db.String(15), nullable=False)
    order_notes = db.Column(db.Text)

    payment_method = db.Column(db.String(20), default="upi")  # upi / cod
    payment_status = db.Column(db.String(20), default="pending")  # pending / paid / failed


    utr_number = db.Column(db.String(50))

    payment_screenshot = db.Column(
        db.String(255)
    )


    subtotal = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    discount_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    delivery_charge = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    grand_total = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    coupon_code = db.Column(db.String(30))
    status = db.Column(db.String(20), default="pending", index=True)  # see ORDER_STATUSES

    delivery_date = db.Column(db.Date, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship("OrderItem", backref="order", lazy="joined",
                             cascade="all, delete-orphan")
    status_history = db.relationship("OrderStatusHistory", backref="order", lazy="dynamic",
                                      cascade="all, delete-orphan",
                                      order_by="OrderStatusHistory.created_at")

    def __repr__(self):
        return f"<Order {self.order_number}>"


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)  # nullable: product may be deleted later

    # snapshot fields so historical orders stay accurate even if product changes
    product_name = db.Column(db.String(150), nullable=False)
    unit = db.Column(db.String(30))
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    product = db.relationship("Product")

    def line_total(self):
        return float(self.unit_price) * self.quantity


class OrderStatusHistory(db.Model):
    __tablename__ = "order_status_history"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False)
    note = db.Column(db.String(255))
    changed_by = db.Column(db.String(80))  # admin username/mobile, or 'system'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
