def register_blueprints(app):
    from .main import main_bp
    from .auth import auth_bp
    from .customer import customer_bp
    from .products import products_bp
    from .cart import cart_bp
    from .checkout import checkout_bp
    from .orders import orders_bp
    from .notifications import notifications_bp
    from .contact import contact_bp
    from .legal import legal_bp
    from .admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(customer_bp, url_prefix="/account")
    app.register_blueprint(products_bp, url_prefix="/products")
    app.register_blueprint(cart_bp, url_prefix="/cart")
    app.register_blueprint(checkout_bp, url_prefix="/checkout")
    app.register_blueprint(orders_bp, url_prefix="/orders")
    app.register_blueprint(notifications_bp, url_prefix="/notifications")
    app.register_blueprint(contact_bp)
    app.register_blueprint(legal_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
