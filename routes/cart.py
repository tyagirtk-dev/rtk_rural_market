from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from models import db
from models.product import Product
from models.cart import Cart, CartItem
from models.coupon import Coupon
from forms.checkout_forms import ApplyCouponForm
from utils.helpers import compute_delivery_charge

cart_bp = Blueprint("cart", __name__, template_folder="../templates/cart")


def _get_or_create_cart():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()
    return cart


@cart_bp.route("/")
@login_required
def view_cart():
    cart = _get_or_create_cart()
    subtotal = cart.subtotal()
    discount = 0.0
    if cart.coupon:
        valid, _ = cart.coupon.is_valid(subtotal)
        discount = cart.coupon.calculate_discount(subtotal) if valid else 0.0
    delivery_charge = compute_delivery_charge(subtotal - discount) if cart.items else 0.0
    grand_total = max(subtotal - discount + delivery_charge, 0)
    coupon_form = ApplyCouponForm()
    return render_template(
        "cart/view.html", cart=cart, subtotal=subtotal, discount=discount,
        delivery_charge=delivery_charge, grand_total=grand_total, coupon_form=coupon_form,
    )


@cart_bp.route("/add/<int:product_id>", methods=["POST"])
@login_required
def add_to_cart(product_id):
    product = Product.query.filter_by(id=product_id, deleted_at=None).first_or_404()
    if not product.is_purchasable():
        flash("This product is currently unavailable.", "warning")
        return redirect(request.referrer or url_for("products.listing"))

    quantity = max(1, request.form.get("quantity", 1, type=int))
    cart = _get_or_create_cart()
    item = CartItem.query.filter_by(cart_id=cart.id, product_id=product.id).first()
    if item:
        item.quantity = min(item.quantity + quantity, product.available_quantity)
    else:
        item = CartItem(cart_id=cart.id, product_id=product.id,
                         quantity=min(quantity, product.available_quantity))
        db.session.add(item)
    db.session.commit()
    flash(f"{product.name} added to cart.", "success")
    return redirect(request.referrer or url_for("cart.view_cart"))


@cart_bp.route("/update/<int:item_id>", methods=["POST"])
@login_required
def update_item(item_id):
    cart = _get_or_create_cart()
    item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first_or_404()
    quantity = request.form.get("quantity", 1, type=int)
    if quantity <= 0:
        db.session.delete(item)
    else:
        item.quantity = min(quantity, item.product.available_quantity or quantity)
    db.session.commit()
    return redirect(url_for("cart.view_cart"))


@cart_bp.route("/remove/<int:item_id>", methods=["POST"])
@login_required
def remove_item(item_id):
    cart = _get_or_create_cart()
    item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash("Item removed from cart.", "info")
    return redirect(url_for("cart.view_cart"))


@cart_bp.route("/apply-coupon", methods=["POST"])
@login_required
def apply_coupon():
    cart = _get_or_create_cart()
    form = ApplyCouponForm()
    if form.validate_on_submit():
        coupon = Coupon.query.filter_by(code=form.code.data.strip().upper()).first()
        if not coupon:
            flash("Invalid coupon code.", "danger")
        else:
            valid, error = coupon.is_valid(cart.subtotal())
            if not valid:
                flash(error, "danger")
            else:
                cart.coupon_id = coupon.id
                db.session.commit()
                flash(f"Coupon {coupon.code} applied!", "success")
    return redirect(url_for("cart.view_cart"))


@cart_bp.route("/remove-coupon", methods=["POST"])
@login_required
def remove_coupon():
    cart = _get_or_create_cart()
    cart.coupon_id = None
    db.session.commit()
    flash("Coupon removed.", "info")
    return redirect(url_for("cart.view_cart"))
