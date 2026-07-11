from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models after db is defined so they can use it.
from .user import User, Address, DeviceSession  # noqa: E402,F401
from .otp import OTP, PasswordResetToken  # noqa: E402,F401
from .product import Category, Product, ProductImage  # noqa: E402,F401
from .cart import Cart, CartItem  # noqa: E402,F401
from .order import Order, OrderItem, OrderStatusHistory  # noqa: E402,F401
from .coupon import Coupon  # noqa: E402,F401
from .notification import Notification  # noqa: E402,F401
from .misc import ContactMessage, City, DeliverySchedule, AuditLog, SiteSetting  # noqa: E402,F401
