from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from models import db
from models.product import Product, Category
from models.user import wishlist as wishlist_table

products_bp = Blueprint("products", __name__, template_folder="../templates/products")


@products_bp.route("/")
def listing():
    query = Product.query.filter_by(is_hidden=False, status="active", deleted_at=None)

    category_slug = request.args.get("category")
    if category_slug:
        category = Category.query.filter_by(slug=category_slug).first()
        if category:
            query = query.filter_by(category_id=category.id)

    search = request.args.get("q", "").strip()
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    city = request.args.get("city", "").strip()
    if city:
        query = query.filter(Product.delivery_city.ilike(f"%{city}%"))

    sort = request.args.get("sort", "newest")
    if sort == "price_low":
        query = query.order_by(Product.price.asc())
    elif sort == "price_high":
        query = query.order_by(Product.price.desc())
    else:
        query = query.order_by(Product.created_at.desc())

    page = request.args.get("page", 1, type=int)
    pagination = query.paginate(page=page, per_page=12, error_out=False)
    categories = Category.query.filter_by(is_active=True).order_by(Category.sort_order).all()

    return render_template(
        "products/listing.html",
        products=pagination.items,
        pagination=pagination,
        categories=categories,
        search=search,
        category_slug=category_slug,
        sort=sort,
    )


@products_bp.route("/<slug>")
def detail(slug):
    product = Product.query.filter_by(slug=slug, deleted_at=None).first_or_404()
    related = (
        Product.query.filter_by(category_id=product.category_id, is_hidden=False, status="active", deleted_at=None)
        .filter(Product.id != product.id)
        .limit(4)
        .all()
    )
    in_wishlist = False
    if current_user.is_authenticated:
        in_wishlist = current_user.wishlist_items.filter_by(id=product.id).first() is not None
    return render_template("products/detail.html", product=product, related=related, in_wishlist=in_wishlist)


@products_bp.route("/<slug>/wishlist-toggle", methods=["POST"])
@login_required
def toggle_wishlist(slug):
    product = Product.query.filter_by(slug=slug, deleted_at=None).first_or_404()
    existing = current_user.wishlist_items.filter_by(id=product.id).first()
    if existing:
        current_user.wishlist_items.remove(product)
        added = False
    else:
        current_user.wishlist_items.append(product)
        added = True
    db.session.commit()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"in_wishlist": added})
    flash("Wishlist updated." if added else "Removed from wishlist.", "info")
    return redirect(url_for("products.detail", slug=slug))
