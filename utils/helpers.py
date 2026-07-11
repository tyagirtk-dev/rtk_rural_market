import os
import re
import uuid
from flask import current_app
from werkzeug.utils import secure_filename


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def unique_slug(model, base_text, existing_id=None):
    """Generate a unique slug for a model, appending -2, -3, ... on collision."""
    base = slugify(base_text) or "item"
    slug = base
    counter = 2
    query = model.query.filter_by(slug=slug)
    if existing_id:
        query = query.filter(model.id != existing_id)
    while query.first() is not None:
        slug = f"{base}-{counter}"
        counter += 1
        query = model.query.filter_by(slug=slug)
        if existing_id:
            query = query.filter(model.id != existing_id)
    return slug


def allowed_image(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]


def save_product_image(file_storage):
    """Save an uploaded image under static/uploads/products and return its relative path."""
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_image(file_storage.filename):
        raise ValueError("Unsupported image format. Use PNG, JPG or WEBP.")

    ext = file_storage.filename.rsplit(".", 1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "products")
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, secure_filename(filename))
    file_storage.save(filepath)
    return f"uploads/products/{filename}"


def compute_delivery_charge(subtotal):
    cfg = current_app.config
    if subtotal >= cfg.get("FREE_DELIVERY_THRESHOLD", 500):
        return 0.0
    return float(cfg.get("DELIVERY_CHARGE", 40))


def format_currency(value):
    try:
        return f"₹{float(value):,.2f}"
    except (TypeError, ValueError):
        return "₹0.00"
