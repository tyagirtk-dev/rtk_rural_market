from datetime import datetime
from . import db


class Coupon(db.Model):
    __tablename__ = "coupons"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    discount_type = db.Column(db.String(20), nullable=False, default="percentage")  # percentage / fixed
    discount_value = db.Column(db.Numeric(10, 2), nullable=False)
    min_order_value = db.Column(db.Numeric(10, 2), default=0)
    max_discount_amount = db.Column(db.Numeric(10, 2), nullable=True)  # cap for percentage coupons

    usage_limit = db.Column(db.Integer, nullable=True)  # total redemptions allowed, None = unlimited
    times_used = db.Column(db.Integer, default=0, nullable=False)

    expiry_date = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_valid(self, order_value=0):
        if not self.is_active:
            return False, "This coupon is no longer active."
        if self.expiry_date and self.expiry_date < datetime.utcnow().date():
            return False, "This coupon has expired."
        if self.usage_limit is not None and self.times_used >= self.usage_limit:
            return False, "This coupon has reached its usage limit."
        if order_value < float(self.min_order_value or 0):
            return False, f"Minimum order value for this coupon is ₹{self.min_order_value:.0f}."
        return True, ""

    def calculate_discount(self, order_value):
        if self.discount_type == "fixed":
            discount = float(self.discount_value)
        else:
            discount = order_value * float(self.discount_value) / 100.0
            if self.max_discount_amount:
                discount = min(discount, float(self.max_discount_amount))
        return round(min(discount, order_value), 2)
