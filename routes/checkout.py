from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
import uuid
import os
from urllib.parse import quote
from flask_login import login_required, current_user

from models import db
from models.cart import Cart
from models.order import Order, OrderItem, OrderStatusHistory
from forms.checkout_forms import CheckoutForm
from services.notification_service import notify_user
from services.email_service import send_order_confirmation_email
from services.audit_service import log_action
from utils.helpers import compute_delivery_charge

checkout_bp = Blueprint("checkout", __name__, template_folder="../templates/checkout")


@checkout_bp.route("/", methods=["GET", "POST"])
@login_required
def checkout():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart or not cart.items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("products.listing"))

    for item in cart.items:
        if not item.product or not item.product.is_purchasable() or item.quantity > item.product.available_quantity:
            flash(f"'{item.product.name if item.product else 'An item'}' is no longer available in the requested quantity.", "danger")
            return redirect(url_for("cart.view_cart"))

    form = CheckoutForm()
    default_address = current_user.addresses.filter_by(is_default=True).first()
    if default_address and not form.is_submitted():
        form.full_address.data = default_address.full_address
        form.city.data = default_address.city
        form.pin_code.data = default_address.pin_code
        form.contact_mobile.data = current_user.mobile_number

    subtotal = cart.subtotal()
    discount = 0.0
    if cart.coupon:
        valid, _ = cart.coupon.is_valid(subtotal)
        discount = cart.coupon.calculate_discount(subtotal) if valid else 0.0
    delivery_charge = compute_delivery_charge(subtotal - discount)
    grand_total = max(subtotal - discount + delivery_charge, 0)


    if form.validate_on_submit():

        payment_screenshot = None
        utr_number = None

        if form.payment_method.data == "upi":

            utr_number = (form.utr_number.data or "").strip()

            if not utr_number:
                flash("Please enter UTR Number.", "danger")
                return render_template(
                    "checkout/checkout.html",
                    form=form,
                    cart=cart,
                    subtotal=subtotal,
                    discount=discount,
                    delivery_charge=delivery_charge,
                    grand_total=grand_total,
                    upi_url=upi_url,
                )

            if not form.payment_screenshot.data:
                flash("Please upload payment screenshot.", "danger")
                return render_template(
                    "checkout/checkout.html",
                    form=form,
                    cart=cart,
                    subtotal=subtotal,
                    discount=discount,
                    delivery_charge=delivery_charge,
                    grand_total=grand_total,
                    upi_url=upi_url,
                )

            f = form.payment_screenshot.data

            ext = os.path.splitext(
                secure_filename(f.filename)
            )[1]

            filename = str(uuid.uuid4()) + ext

            upload_path = os.path.join(
                current_app.config["UPLOAD_FOLDER"],
                "payments"
            )

            os.makedirs(upload_path, exist_ok=True)

            save_path = os.path.join(upload_path, filename)

            f.save(save_path)

            payment_screenshot = "uploads/payments/" + filename
        order = Order(
            user_id=current_user.id,
            full_address=form.full_address.data.strip(),
            city=form.city.data.strip(),
            pin_code=form.pin_code.data.strip(),
            contact_mobile=form.contact_mobile.data.strip(),
            order_notes=form.order_notes.data,
            payment_method=form.payment_method.data,
            utr_number=utr_number,
            payment_screenshot=payment_screenshot,
            subtotal=subtotal,
            discount_amount=discount,
            delivery_charge=delivery_charge,
            grand_total=grand_total,
            coupon_code=cart.coupon.code if cart.coupon else None,
            status="pending",
        )
        db.session.add(order)
        db.session.flush()  # get order.id before committing items

        for item in cart.items:
            db.session.add(OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                product_name=item.product.name,
                unit=item.product.unit,
                unit_price=item.product.price,
                quantity=item.quantity,
            ))
            item.product.available_quantity = max(0, item.product.available_quantity - item.quantity)
            if item.product.available_quantity == 0:
                item.product.stock_status = "out_of_stock"

        db.session.add(OrderStatusHistory(order_id=order.id, status="pending",
                                           note="Order placed by customer", changed_by=current_user.mobile_number))

        if cart.coupon:
            cart.coupon.times_used += 1

        # clear cart
        for item in list(cart.items):
            db.session.delete(item)
        cart.coupon_id = None

        db.session.commit()

        notify_user(current_user.id, "Order Placed", f"Your order {order.order_number} has been placed successfully.",
                     category="order", link=f"/orders/{order.order_number}")
        send_order_confirmation_email(current_user, order)
        log_action(current_user.mobile_number, "order_placed", f"Order {order.order_number}")

        return redirect(url_for("orders.confirmation", order_number=order.order_number))

    upi_url=(
        f"upi://pay?pa={current_app.config['UPI_ID']}"
        f"&pn={quote(current_app.config['UPI_NAME'])}"
        f"&am={grand_total:.2f}&cu=INR"
    )

    return render_template(
        "checkout/checkout.html", form=form, cart=cart, subtotal=subtotal,
        discount=discount, delivery_charge=delivery_charge,
        grand_total=grand_total, upi_url=upi_url,
    )
