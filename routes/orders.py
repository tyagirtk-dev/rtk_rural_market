from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user

from models.order import Order

orders_bp = Blueprint("orders", __name__, template_folder="../templates/orders")


@orders_bp.route("/")
@login_required
def history():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template("orders/history.html", orders=orders)


@orders_bp.route("/<order_number>")
@login_required
def detail(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    if order.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    return render_template("orders/detail.html", order=order)


@orders_bp.route("/<order_number>/confirmation")
@login_required
def confirmation(order_number):
    order = Order.query.filter_by(order_number=order_number, user_id=current_user.id).first_or_404()
    return render_template("orders/confirmation.html", order=order)
