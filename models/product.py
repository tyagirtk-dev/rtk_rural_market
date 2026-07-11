from datetime import datetime
from . import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    slug = db.Column(db.String(90), unique=True, nullable=False, index=True)
    icon = db.Column(db.String(50), default="bi-basket")  # bootstrap-icons class
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0)

    products = db.relationship("Product", backref="category", lazy="dynamic")

    def __repr__(self):
        return f"<Category {self.name}>"


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False, index=True)

    name = db.Column(db.String(150), nullable=False, index=True)
    slug = db.Column(db.String(170), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)

    price = db.Column(db.Numeric(10, 2), nullable=False)
    unit = db.Column(db.String(30), nullable=False, default="kg")  # kg, litre, piece, dozen, gram
    available_quantity = db.Column(db.Integer, default=0, nullable=False)
    stock_status = db.Column(db.String(20), default="in_stock")  # in_stock / low_stock / out_of_stock

    delivery_city = db.Column(db.String(100), index=True)

    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    is_hidden = db.Column(db.Boolean, default=False, nullable=False)
    status = db.Column(db.String(20), default="active")  # active / inactive

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)  # soft delete

    images = db.relationship("ProductImage", backref="product", lazy="joined",
                              cascade="all, delete-orphan", order_by="ProductImage.sort_order")

    def primary_image(self):
        return self.images[0].file_path if self.images else None

    def is_purchasable(self):
        return (self.status == "active" and not self.is_hidden and not self.deleted_at
                and self.available_quantity > 0)

    def __repr__(self):
        return f"<Product {self.name}>"


class ProductImage(db.Model):
    __tablename__ = "product_images"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
    file_path = db.Column(db.String(255), nullable=False)  # relative to static/
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
