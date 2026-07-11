from flask import Blueprint, render_template, send_from_directory, current_app

from models.product import Product, Category

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    categories = Category.query.filter_by(is_active=True).order_by(Category.sort_order).all()
    featured = (
        Product.query.filter_by(is_featured=True, is_hidden=False, status="active", deleted_at=None)
        .limit(8)
        .all()
    )
    latest = (
        Product.query.filter_by(is_hidden=False, status="active", deleted_at=None)
        .order_by(Product.created_at.desc())
        .limit(8)
        .all()
    )
    return render_template("home.html", categories=categories, featured=featured, latest=latest)


@main_bp.route("/manifest.json")
def manifest():
    return send_from_directory(current_app.static_folder, "manifest.json", mimetype="application/manifest+json")


@main_bp.route("/service-worker.js")
def service_worker():
    return send_from_directory(current_app.static_folder, "js/service-worker.js", mimetype="application/javascript")
