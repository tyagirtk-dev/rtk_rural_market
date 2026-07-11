import csv
import io
import os
import shutil
from datetime import datetime, date, timedelta

from flask import (
    Blueprint, render_template, redirect, url_for, flash, request,
    send_file, current_app, abort, Response
)
from flask_login import login_required, current_user
from sqlalchemy import func

from models import db
from models.user import User
from models.product import Product, Category, ProductImage
from models.order import Order, ORDER_STATUSES
from models.coupon import Coupon
from models.misc import City, DeliverySchedule, AuditLog, ContactMessage, SiteSetting
from forms.admin_forms import (
    ProductForm, CategoryForm, CouponForm, CityForm, DeliveryScheduleForm,
    OrderStatusForm, SMTPSettingsForm, WebsiteSettingsForm
)
from utils.decorators import admin_required
from utils.helpers import unique_slug, save_product_image, format_currency
from services.order_service import update_order_status
from services.audit_service import log_action

admin_bp = Blueprint("admin", __name__, template_folder="../templates/admin")


@admin_bp.before_request
@login_required
@admin_required
def _guard():
    """Every admin route requires an authenticated admin user."""
    pass


# ---------------------------------------------------------------- Dashboard
@admin_bp.route("/")
def dashboard():
    today = date.today()
    month_start = today.replace(day=1)

    stats = {
        "total_orders": Order.query.count(),
        "pending_orders": Order.query.filter_by(status="pending").count(),
        "orders_this_month": Order.query.filter(Order.created_at >= month_start).count(),
        "revenue_this_month": db.session.query(func.coalesce(func.sum(Order.grand_total), 0))
            .filter(Order.created_at >= month_start, Order.status != "cancelled").scalar(),
        "total_customers": User.query.filter_by(is_admin=False).count(),
        "total_products": Product.query.filter_by(deleted_at=None).count(),
        "low_stock": Product.query.filter(Product.available_quantity <= 5, Product.deleted_at.is_(None)).count(),
        "unresolved_messages": ContactMessage.query.filter_by(is_resolved=False).count(),
    }
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(8).all()
    return render_template("admin/dashboard.html", stats=stats, recent_orders=recent_orders)


# ------------------------------------------------------------------- Users
@admin_bp.route("/users")
def users():
    q = request.args.get("q", "").strip()
    query = User.query.filter_by(is_admin=False)
    if q:
        query = query.filter(
            (User.full_name.ilike(f"%{q}%")) |
            (User.mobile_number.ilike(f"%{q}%")) |
            (User.email.ilike(f"%{q}%"))
        )
    page = request.args.get("page", 1, type=int)
    pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template("admin/users.html", pagination=pagination, q=q)


@admin_bp.route("/users/<int:user_id>")
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    orders = user.orders.order_by(Order.created_at.desc()).all()
    return render_template("admin/user_detail.html", user=user, orders=orders)


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active_account = not user.is_active_account
    db.session.commit()
    log_action(current_user.mobile_number, "admin_toggle_user", f"User {user.mobile_number} active={user.is_active_account}")
    flash("User status updated.", "success")
    return redirect(url_for("admin.user_detail", user_id=user.id))


# --------------------------------------------------------------- Categories
@admin_bp.route("/categories")
def categories():
    items = Category.query.order_by(Category.sort_order).all()
    return render_template("admin/categories.html", categories=items)


@admin_bp.route("/categories/add", methods=["GET", "POST"])
def add_category():
    form = CategoryForm()
    if form.validate_on_submit():
        cat = Category(
            name=form.name.data.strip(),
            slug=unique_slug(Category, form.name.data),
            icon=form.icon.data or "bi-basket",
            sort_order=form.sort_order.data or 0,
            is_active=form.is_active.data,
        )
        db.session.add(cat)
        db.session.commit()
        flash("Category created.", "success")
        return redirect(url_for("admin.categories"))
    return render_template("admin/category_form.html", form=form, mode="add")


@admin_bp.route("/categories/<int:category_id>/edit", methods=["GET", "POST"])
def edit_category(category_id):
    cat = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=cat)
    if form.validate_on_submit():
        cat.name = form.name.data.strip()
        cat.slug = unique_slug(Category, form.name.data, existing_id=cat.id)
        cat.icon = form.icon.data or "bi-basket"
        cat.sort_order = form.sort_order.data or 0
        cat.is_active = form.is_active.data
        db.session.commit()
        flash("Category updated.", "success")
        return redirect(url_for("admin.categories"))
    return render_template("admin/category_form.html", form=form, mode="edit")


@admin_bp.route("/categories/<int:category_id>/delete", methods=["POST"])
def delete_category(category_id):
    cat = Category.query.get_or_404(category_id)
    if cat.products.count() > 0:
        flash("Cannot delete a category that still has products. Move or delete its products first.", "danger")
    else:
        db.session.delete(cat)
        db.session.commit()
        flash("Category deleted.", "info")
    return redirect(url_for("admin.categories"))


# ----------------------------------------------------------------- Products
@admin_bp.route("/products")
def products():
    q = request.args.get("q", "").strip()
    query = Product.query.filter_by(deleted_at=None)
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))
    page = request.args.get("page", 1, type=int)
    pagination = query.order_by(Product.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template("admin/products.html", pagination=pagination, q=q)


def _populate_category_choices(form):
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]


@admin_bp.route("/products/add", methods=["GET", "POST"])
def add_product():
    form = ProductForm()
    _populate_category_choices(form)
    if form.validate_on_submit():
        product = Product(
            category_id=form.category_id.data,
            name=form.name.data.strip(),
            slug=unique_slug(Product, form.name.data),
            description=form.description.data,
            price=form.price.data,
            unit=form.unit.data,
            available_quantity=form.available_quantity.data,
            delivery_city=form.delivery_city.data,
            is_featured=form.is_featured.data,
            is_hidden=form.is_hidden.data,
            status=form.status.data,
            stock_status="in_stock" if form.available_quantity.data > 0 else "out_of_stock",
        )
        db.session.add(product)
        db.session.flush()

        for i, file_storage in enumerate(request.files.getlist("images")):
            if file_storage and file_storage.filename:
                try:
                    path = save_product_image(file_storage)
                    if path:
                        db.session.add(ProductImage(product_id=product.id, file_path=path, sort_order=i))
                except ValueError as exc:
                    flash(str(exc), "warning")

        db.session.commit()
        log_action(current_user.mobile_number, "admin_add_product", product.name)
        flash("Product created.", "success")
        return redirect(url_for("admin.products"))

    return render_template("admin/product_form.html", form=form, mode="add")


@admin_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    _populate_category_choices(form)
    if form.validate_on_submit():
        product.category_id = form.category_id.data
        product.name = form.name.data.strip()
        product.slug = unique_slug(Product, form.name.data, existing_id=product.id)
        product.description = form.description.data
        product.price = form.price.data
        product.unit = form.unit.data
        product.available_quantity = form.available_quantity.data
        product.delivery_city = form.delivery_city.data
        product.is_featured = form.is_featured.data
        product.is_hidden = form.is_hidden.data
        product.status = form.status.data
        product.stock_status = "in_stock" if form.available_quantity.data > 0 else "out_of_stock"

        for i, file_storage in enumerate(request.files.getlist("images")):
            if file_storage and file_storage.filename:
                try:
                    path = save_product_image(file_storage)
                    if path:
                        db.session.add(ProductImage(
                            product_id=product.id, file_path=path,
                            sort_order=len(product.images) + i
                        ))
                except ValueError as exc:
                    flash(str(exc), "warning")

        db.session.commit()
        log_action(current_user.mobile_number, "admin_edit_product", product.name)
        flash("Product updated.", "success")
        return redirect(url_for("admin.products"))

    return render_template("admin/product_form.html", form=form, mode="edit", product=product)


@admin_bp.route("/products/<int:product_id>/delete", methods=["POST"])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    product.deleted_at = datetime.utcnow()
    product.status = "inactive"
    product.is_hidden = True
    db.session.commit()
    log_action(current_user.mobile_number, "admin_delete_product", product.name)
    flash("Product deleted.", "info")
    return redirect(url_for("admin.products"))


@admin_bp.route("/products/<int:product_id>/toggle-hidden", methods=["POST"])
def toggle_product_hidden(product_id):
    product = Product.query.get_or_404(product_id)
    product.is_hidden = not product.is_hidden
    db.session.commit()
    return redirect(url_for("admin.products"))


@admin_bp.route("/products/<int:product_id>/toggle-featured", methods=["POST"])
def toggle_product_featured(product_id):
    product = Product.query.get_or_404(product_id)
    product.is_featured = not product.is_featured
    db.session.commit()
    return redirect(url_for("admin.products"))


@admin_bp.route("/products/images/<int:image_id>/delete", methods=["POST"])
def delete_product_image(image_id):
    image = ProductImage.query.get_or_404(image_id)
    product_id = image.product_id
    db.session.delete(image)
    db.session.commit()
    return redirect(url_for("admin.edit_product", product_id=product_id))


# ------------------------------------------------------------- Inventory
@admin_bp.route("/inventory")
def inventory():
    products_list = Product.query.filter_by(deleted_at=None).order_by(Product.available_quantity.asc()).all()
    return render_template("admin/inventory.html", products=products_list)


# ---------------------------------------------------------------- Orders
@admin_bp.route("/orders")
def orders():
    status = request.args.get("status", "")
    city = request.args.get("city", "")
    q = request.args.get("q", "").strip()

    query = Order.query
    if status:
        query = query.filter_by(status=status)
    if city:
        query = query.filter(Order.city.ilike(f"%{city}%"))
    if q:
        query = query.filter(
            (Order.order_number.ilike(f"%{q}%")) | (Order.contact_mobile.ilike(f"%{q}%"))
        )

    page = request.args.get("page", 1, type=int)
    pagination = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template("admin/orders.html", pagination=pagination, status=status, city=city, q=q,
                            statuses=ORDER_STATUSES)


@admin_bp.route("/orders/<order_number>")
def order_detail(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    form = OrderStatusForm(status=order.status)
    return render_template("admin/order_detail.html", order=order, form=form)


@admin_bp.route("/orders/<order_number>/update-status", methods=["POST"])
def order_update_status(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    form = OrderStatusForm()
    if form.validate_on_submit():
        update_order_status(order, form.status.data, changed_by=current_user.mobile_number, note=form.note.data)
        flash("Order status updated.", "success")
    return redirect(url_for("admin.order_detail", order_number=order_number))


@admin_bp.route("/orders/export-csv")
def export_orders_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Order Number", "Customer", "Mobile", "City", "Status", "Payment",
                      "Subtotal", "Discount", "Delivery", "Grand Total", "Placed On"])
    for order in Order.query.order_by(Order.created_at.desc()).all():
        writer.writerow([
            order.order_number, order.customer.full_name, order.contact_mobile, order.city,
            order.status, order.payment_method, order.subtotal, order.discount_amount,
            order.delivery_charge, order.grand_total, order.created_at.strftime("%Y-%m-%d %H:%M"),
        ])
    output.seek(0)
    return Response(
        output.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=orders_export.csv"},
    )


# ------------------------------------------------------------- Delivery
@admin_bp.route("/delivery-planning")
def delivery_planning():
    city_filter = request.args.get("city", "")
    active_orders = Order.query.filter(Order.status.in_(["confirmed", "packed"]))
    if city_filter:
        active_orders = active_orders.filter(Order.city.ilike(f"%{city_filter}%"))
    active_orders = active_orders.order_by(Order.city, Order.created_at).all()

    grouped = {}
    for order in active_orders:
        grouped.setdefault(order.city, []).append(order)

    summary = {
        city: {
            "order_count": len(orders_in_city),
            "total_value": sum(float(o.grand_total) for o in orders_in_city),
        }
        for city, orders_in_city in grouped.items()
    }

    schedules = DeliverySchedule.query.order_by(DeliverySchedule.delivery_date.desc()).limit(20).all()
    return render_template("admin/delivery_planning.html", grouped=grouped, summary=summary, schedules=schedules,
                            city_filter=city_filter)


@admin_bp.route("/delivery-planning/print/<city>")
def delivery_print(city):
    orders_in_city = Order.query.filter(
        Order.city.ilike(city), Order.status.in_(["confirmed", "packed", "out_for_delivery"])
    ).order_by(Order.created_at).all()
    return render_template("admin/delivery_print.html", city=city, orders=orders_in_city)


@admin_bp.route("/delivery-schedule/add", methods=["GET", "POST"])
def add_delivery_schedule():
    form = DeliveryScheduleForm()
    if form.validate_on_submit():
        db.session.add(DeliverySchedule(
            city=form.city.data.strip(), delivery_date=form.delivery_date.data, notes=form.notes.data
        ))
        db.session.commit()
        flash("Delivery date scheduled.", "success")
        return redirect(url_for("admin.delivery_planning"))
    return render_template("admin/delivery_schedule_form.html", form=form)


# ------------------------------------------------------------------ Cities
@admin_bp.route("/cities")
def cities():
    items = City.query.order_by(City.name).all()
    return render_template("admin/cities.html", cities=items)


@admin_bp.route("/cities/add", methods=["GET", "POST"])
def add_city():
    form = CityForm()
    if form.validate_on_submit():
        db.session.add(City(name=form.name.data.strip(), is_active=form.is_active.data))
        db.session.commit()
        flash("City added.", "success")
        return redirect(url_for("admin.cities"))
    return render_template("admin/city_form.html", form=form, mode="add")


@admin_bp.route("/cities/<int:city_id>/edit", methods=["GET", "POST"])
def edit_city(city_id):
    city = City.query.get_or_404(city_id)
    form = CityForm(obj=city)
    if form.validate_on_submit():
        city.name = form.name.data.strip()
        city.is_active = form.is_active.data
        db.session.commit()
        flash("City updated.", "success")
        return redirect(url_for("admin.cities"))
    return render_template("admin/city_form.html", form=form, mode="edit")


@admin_bp.route("/cities/<int:city_id>/delete", methods=["POST"])
def delete_city(city_id):
    city = City.query.get_or_404(city_id)
    db.session.delete(city)
    db.session.commit()
    flash("City removed.", "info")
    return redirect(url_for("admin.cities"))


# ----------------------------------------------------------------- Coupons
@admin_bp.route("/coupons")
def coupons():
    items = Coupon.query.order_by(Coupon.created_at.desc()).all()
    return render_template("admin/coupons.html", coupons=items)


@admin_bp.route("/coupons/add", methods=["GET", "POST"])
def add_coupon():
    form = CouponForm()
    if form.validate_on_submit():
        db.session.add(Coupon(
            code=form.code.data.strip().upper(),
            discount_type=form.discount_type.data,
            discount_value=form.discount_value.data,
            min_order_value=form.min_order_value.data or 0,
            max_discount_amount=form.max_discount_amount.data,
            usage_limit=form.usage_limit.data,
            expiry_date=form.expiry_date.data,
            is_active=form.is_active.data,
        ))
        db.session.commit()
        flash("Coupon created.", "success")
        return redirect(url_for("admin.coupons"))
    return render_template("admin/coupon_form.html", form=form, mode="add")


@admin_bp.route("/coupons/<int:coupon_id>/edit", methods=["GET", "POST"])
def edit_coupon(coupon_id):
    coupon = Coupon.query.get_or_404(coupon_id)
    form = CouponForm(obj=coupon)
    if form.validate_on_submit():
        coupon.code = form.code.data.strip().upper()
        coupon.discount_type = form.discount_type.data
        coupon.discount_value = form.discount_value.data
        coupon.min_order_value = form.min_order_value.data or 0
        coupon.max_discount_amount = form.max_discount_amount.data
        coupon.usage_limit = form.usage_limit.data
        coupon.expiry_date = form.expiry_date.data
        coupon.is_active = form.is_active.data
        db.session.commit()
        flash("Coupon updated.", "success")
        return redirect(url_for("admin.coupons"))
    return render_template("admin/coupon_form.html", form=form, mode="edit")


@admin_bp.route("/coupons/<int:coupon_id>/delete", methods=["POST"])
def delete_coupon(coupon_id):
    coupon = Coupon.query.get_or_404(coupon_id)
    db.session.delete(coupon)
    db.session.commit()
    flash("Coupon deleted.", "info")
    return redirect(url_for("admin.coupons"))


# ---------------------------------------------------------------- Payments
@admin_bp.route("/payments")
def payments():
    page = request.args.get("page", 1, type=int)
    pagination = Order.query.order_by(Order.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template("admin/payments.html", pagination=pagination)


# --------------------------------------------------------------- Messages
@admin_bp.route("/messages")
def messages():
    items = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template("admin/messages.html", messages=items)


@admin_bp.route("/messages/<int:message_id>/resolve", methods=["POST"])
def resolve_message(message_id):
    msg = ContactMessage.query.get_or_404(message_id)
    msg.is_resolved = True
    db.session.commit()
    return redirect(url_for("admin.messages"))


# ---------------------------------------------------------------- Reports
@admin_bp.route("/reports")
def reports():
    days_back = 30
    start_date = date.today() - timedelta(days=days_back)

    daily_rows = (
        db.session.query(func.date(Order.created_at), func.count(Order.id), func.coalesce(func.sum(Order.grand_total), 0))
        .filter(Order.created_at >= start_date, Order.status != "cancelled")
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
        .all()
    )
    from models.order import OrderItem
    top_products = (
        db.session.query(OrderItem.product_name, func.sum(OrderItem.quantity).label("qty"))
        .group_by(OrderItem.product_name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(10)
        .all()
    )
    status_counts = (
        db.session.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
    )
    return render_template(
        "admin/reports.html", daily_rows=daily_rows, top_products=top_products,
        status_counts=status_counts, days_back=days_back,
    )


# --------------------------------------------------------------- Settings
@admin_bp.route("/settings/smtp", methods=["GET", "POST"])
def smtp_settings():
    form = SMTPSettingsForm(
        smtp_host=SiteSetting.get("smtp_host", current_app.config.get("SMTP_HOST", "")),
        smtp_port=int(SiteSetting.get("smtp_port", current_app.config.get("SMTP_PORT", 587)) or 587),
        smtp_username=SiteSetting.get("smtp_username", current_app.config.get("SMTP_USERNAME", "")),
        smtp_from_name=SiteSetting.get("smtp_from_name", current_app.config.get("SMTP_FROM_NAME", "")),
        smtp_from_email=SiteSetting.get("smtp_from_email", current_app.config.get("SMTP_FROM_EMAIL", "")),
    )
    if form.validate_on_submit():
        SiteSetting.set("smtp_host", form.smtp_host.data)
        SiteSetting.set("smtp_port", str(form.smtp_port.data or 587))
        SiteSetting.set("smtp_username", form.smtp_username.data)
        if form.smtp_password.data:
            SiteSetting.set("smtp_password", form.smtp_password.data)
        SiteSetting.set("smtp_from_name", form.smtp_from_name.data)
        SiteSetting.set("smtp_from_email", form.smtp_from_email.data)
        db.session.commit()
        flash("SMTP settings saved. Note: these override .env values only after a restart picks up SiteSetting overrides in a future enhancement; for now .env is authoritative at runtime.", "info")
        return redirect(url_for("admin.smtp_settings"))
    return render_template("admin/smtp_settings.html", form=form)


@admin_bp.route("/settings/website", methods=["GET", "POST"])
def website_settings():
    form = WebsiteSettingsForm(
        site_name=SiteSetting.get("site_name", "RTK Rural Market"),
        contact_phone=SiteSetting.get("contact_phone", ""),
        contact_email=SiteSetting.get("contact_email", ""),
        whatsapp_number=SiteSetting.get("whatsapp_number", ""),
        address=SiteSetting.get("address", ""),
        google_maps_embed=SiteSetting.get("google_maps_embed", ""),
    )
    if form.validate_on_submit():
        for field in ["site_name", "contact_phone", "contact_email", "whatsapp_number", "address", "google_maps_embed"]:
            SiteSetting.set(field, getattr(form, field).data)
        db.session.commit()
        flash("Website settings saved.", "success")
        return redirect(url_for("admin.website_settings"))
    return render_template("admin/website_settings.html", form=form)


# ---------------------------------------------------------------- Backup
@admin_bp.route("/backup")
def backup():
    backups_dir = os.path.join(current_app.root_path, "backups")
    os.makedirs(backups_dir, exist_ok=True)
    files = sorted(os.listdir(backups_dir), reverse=True)
    return render_template("admin/backup.html", files=files)


@admin_bp.route("/backup/create", methods=["POST"])
def create_backup():
    db_uri = current_app.config["SQLALCHEMY_DATABASE_URI"]
    if not db_uri.startswith("sqlite:///"):
        flash("Automatic backup is only implemented for SQLite. For PostgreSQL, use pg_dump on the server.", "warning")
        return redirect(url_for("admin.backup"))

    db_path = db_uri.replace("sqlite:///", "", 1)
    backups_dir = os.path.join(current_app.root_path, "backups")
    os.makedirs(backups_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(backups_dir, f"backup_{timestamp}.db")
    shutil.copy2(db_path, dest)
    log_action(current_user.mobile_number, "admin_backup_created", dest)
    flash("Backup created.", "success")
    return redirect(url_for("admin.backup"))


@admin_bp.route("/backup/download/<filename>")
def download_backup(filename):
    backups_dir = os.path.join(current_app.root_path, "backups")
    filepath = os.path.join(backups_dir, filename)
    if not os.path.isfile(filepath) or ".." in filename:
        abort(404)
    return send_file(filepath, as_attachment=True)


# ------------------------------------------------------------------- Logs
@admin_bp.route("/logs")
def logs():
    page = request.args.get("page", 1, type=int)
    pagination = AuditLog.query.order_by(AuditLog.created_at.desc()).paginate(page=page, per_page=50, error_out=False)
    return render_template("admin/logs.html", pagination=pagination)


from flask import flash,redirect,url_for

@admin_bp.post("/payments/<int:order_id>/approve")

def payment_approve(order_id):

    order=Order.query.get_or_404(order_id)

    order.payment_status="paid"

    db.session.commit()

    notify_user(

        order.user_id,

        "Payment Approved",

        f"Payment for {order.order_number} approved.",

        category="payment"

    )

    flash("Payment Approved.","success")

    return redirect(url_for("admin.payments"))


@admin_bp.post("/payments/<int:order_id>/reject")

def payment_reject(order_id):

    order=Order.query.get_or_404(order_id)

    order.payment_status="failed"

    db.session.commit()

    notify_user(

        order.user_id,

        "Payment Rejected",

        f"Payment for {order.order_number} rejected.",

        category="payment"

    )

    flash("Payment Rejected.","warning")

    return redirect(url_for("admin.payments"))

