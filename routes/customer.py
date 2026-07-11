from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from models.order import Order
from flask_login import login_required, current_user, logout_user

from models import db
from models.user import Address
from forms.customer_forms import ProfileForm, AddressForm, DeleteAccountForm
from forms.auth_forms import ChangePasswordForm
from services.email_service import send_password_changed_email
from services.notification_service import notify_user
from services.audit_service import log_action

customer_bp = Blueprint("customer", __name__, template_folder="../templates/customer")


@customer_bp.route("/dashboard")
@login_required
def dashboard():
    recent_orders = current_user.orders.order_by(Order.created_at.desc()).limit(5).all()
    return render_template("customer/dashboard.html", recent_orders=recent_orders)


@customer_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data.strip()
        current_user.email = form.email.data.strip().lower() if form.email.data else None
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("customer.profile"))
    return render_template("customer/profile.html", form=form)


@customer_bp.route("/addresses")
@login_required
def addresses():
    items = current_user.addresses.order_by(Address.is_default.desc()).all()
    return render_template("customer/addresses.html", addresses=items)


@customer_bp.route("/addresses/add", methods=["GET", "POST"])
@login_required
def add_address():
    form = AddressForm()
    if form.validate_on_submit():
        if form.is_default.data:
            current_user.addresses.update({"is_default": False})
        addr = Address(
            user_id=current_user.id,
            label=form.label.data.strip(),
            full_address=form.full_address.data.strip(),
            city=form.city.data.strip(),
            pin_code=form.pin_code.data.strip(),
            landmark=form.landmark.data,
            is_default=form.is_default.data,
        )
        db.session.add(addr)
        db.session.commit()
        flash("Address saved.", "success")
        return redirect(url_for("customer.addresses"))
    return render_template("customer/address_form.html", form=form, mode="add")


@customer_bp.route("/addresses/<int:address_id>/edit", methods=["GET", "POST"])
@login_required
def edit_address(address_id):
    addr = current_user.addresses.filter_by(id=address_id).first_or_404()
    form = AddressForm(obj=addr)
    if form.validate_on_submit():
        if form.is_default.data:
            current_user.addresses.update({"is_default": False})
        addr.label = form.label.data.strip()
        addr.full_address = form.full_address.data.strip()
        addr.city = form.city.data.strip()
        addr.pin_code = form.pin_code.data.strip()
        addr.landmark = form.landmark.data
        addr.is_default = form.is_default.data
        db.session.commit()
        flash("Address updated.", "success")
        return redirect(url_for("customer.addresses"))
    return render_template("customer/address_form.html", form=form, mode="edit")


@customer_bp.route("/addresses/<int:address_id>/delete", methods=["POST"])
@login_required
def delete_address(address_id):
    addr = current_user.addresses.filter_by(id=address_id).first_or_404()
    db.session.delete(addr)
    db.session.commit()
    flash("Address removed.", "info")
    return redirect(url_for("customer.addresses"))


@customer_bp.route("/wishlist")
@login_required
def wishlist():
    items = current_user.wishlist_items.all()
    return render_template("customer/wishlist.html", items=items)


@customer_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Current password is incorrect.", "danger")
            return render_template("customer/change_password.html", form=form)
        current_user.set_password(form.new_password.data)
        db.session.commit()
        notify_user(current_user.id, "Password Changed", "Your password was changed successfully.", category="account")
        send_password_changed_email(current_user)
        log_action(current_user.mobile_number, "password_change", "Password changed from account settings")
        flash("Password changed successfully.", "success")
        return redirect(url_for("customer.dashboard"))
    return render_template("customer/change_password.html", form=form)


@customer_bp.route("/privacy-settings", methods=["GET", "POST"])
@login_required
def privacy_settings():
    if request.method == "POST":
        current_user.marketing_opt_in = "marketing_opt_in" in request.form
        db.session.commit()
        flash("Privacy settings updated.", "success")
        return redirect(url_for("customer.privacy_settings"))
    return render_template("customer/privacy_settings.html")


@customer_bp.route("/delete-account", methods=["GET", "POST"])
@login_required
def delete_account():
    form = DeleteAccountForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.password.data):
            flash("Incorrect password.", "danger")
            return render_template("customer/delete_account.html", form=form)
        current_user.deleted_at = datetime.utcnow()
        current_user.is_active_account = False
        db.session.commit()
        log_action(current_user.mobile_number, "account_deleted", "Soft deleted by self-service request")
        logout_user()
        flash("Your account has been deleted.", "info")
        return redirect(url_for("main.home"))
    return render_template("customer/delete_account.html", form=form)
