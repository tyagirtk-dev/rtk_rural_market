from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, TextAreaField, DecimalField, IntegerField, SelectField,
    BooleanField, SubmitField, DateField, MultipleFileField
)
from wtforms.validators import DataRequired, Length, Optional, NumberRange


class CategoryForm(FlaskForm):
    name = StringField("Category Name", validators=[DataRequired(), Length(max=80)])
    icon = StringField("Bootstrap Icon Class", validators=[Optional(), Length(max=50)])
    sort_order = IntegerField("Sort Order", default=0, validators=[Optional()])
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save Category")


class ProductForm(FlaskForm):
    category_id = SelectField("Category", coerce=int, validators=[DataRequired()])
    name = StringField("Product Name", validators=[DataRequired(), Length(max=150)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=3000)])
    price = DecimalField("Price (₹)", validators=[DataRequired(), NumberRange(min=0)])
    unit = SelectField(
        "Unit",
        choices=[("kg", "Kilogram"), ("litre", "Litre"), ("gram", "Gram"),
                 ("piece", "Piece"), ("dozen", "Dozen"), ("packet", "Packet")],
    )
    available_quantity = IntegerField("Available Quantity", validators=[DataRequired(), NumberRange(min=0)])
    delivery_city = StringField("Delivery City", validators=[Optional(), Length(max=100)])
    is_featured = BooleanField("Feature this product")
    is_hidden = BooleanField("Hide from storefront")
    status = SelectField("Status", choices=[("active", "Active"), ("inactive", "Inactive")])
    images = MultipleFileField(
        "Product Images",
        validators=[Optional(), FileAllowed(["png", "jpg", "jpeg", "webp"], "Images only.")],
    )
    submit = SubmitField("Save Product")


class CouponForm(FlaskForm):
    code = StringField("Coupon Code", validators=[DataRequired(), Length(max=30)])
    discount_type = SelectField("Discount Type", choices=[("percentage", "Percentage"), ("fixed", "Fixed Amount")])
    discount_value = DecimalField("Discount Value", validators=[DataRequired(), NumberRange(min=0)])
    min_order_value = DecimalField("Minimum Order Value", default=0, validators=[Optional(), NumberRange(min=0)])
    max_discount_amount = DecimalField("Max Discount (for % coupons)", validators=[Optional(), NumberRange(min=0)])
    usage_limit = IntegerField("Usage Limit", validators=[Optional(), NumberRange(min=1)])
    expiry_date = DateField("Expiry Date", validators=[Optional()])
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save Coupon")


class CityForm(FlaskForm):
    name = StringField("City Name", validators=[DataRequired(), Length(max=100)])
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save City")


class DeliveryScheduleForm(FlaskForm):
    city = StringField("City", validators=[DataRequired(), Length(max=100)])
    delivery_date = DateField("Delivery Date", validators=[DataRequired()])
    notes = StringField("Notes", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Save Schedule")


class OrderStatusForm(FlaskForm):
    status = SelectField(
        "Status",
        choices=[
            ("pending", "Pending"), ("confirmed", "Confirmed"), ("packed", "Packed"),
            ("out_for_delivery", "Out for Delivery"), ("delivered", "Delivered"),
            ("cancelled", "Cancelled"),
        ],
    )
    note = StringField("Note", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Update Status")


class SMTPSettingsForm(FlaskForm):
    smtp_host = StringField("SMTP Host", validators=[Optional(), Length(max=150)])
    smtp_port = IntegerField("SMTP Port", validators=[Optional()])
    smtp_username = StringField("SMTP Username", validators=[Optional(), Length(max=150)])
    smtp_password = StringField("SMTP Password", validators=[Optional(), Length(max=150)])
    smtp_from_name = StringField("From Name", validators=[Optional(), Length(max=100)])
    smtp_from_email = StringField("From Email", validators=[Optional(), Length(max=150)])
    submit = SubmitField("Save SMTP Settings")


class WebsiteSettingsForm(FlaskForm):
    site_name = StringField("Website Name", validators=[Optional(), Length(max=150)])
    contact_phone = StringField("Contact Phone", validators=[Optional(), Length(max=20)])
    contact_email = StringField("Contact Email", validators=[Optional(), Length(max=150)])
    whatsapp_number = StringField("WhatsApp Number", validators=[Optional(), Length(max=20)])
    address = TextAreaField("Business Address", validators=[Optional(), Length(max=500)])
    google_maps_embed = TextAreaField("Google Maps Embed URL", validators=[Optional(), Length(max=1000)])
    submit = SubmitField("Save Website Settings")
