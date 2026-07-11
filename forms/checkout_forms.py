from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, FileField
from wtforms.validators import DataRequired, Length, Optional

from forms.auth_forms import MOBILE_REGEX
from flask_wtf.file import FileAllowed


class CheckoutForm(FlaskForm):
    full_address = StringField("Address", validators=[DataRequired(), Length(max=300)])
    city = StringField("City", validators=[DataRequired(), Length(max=100)])
    pin_code = StringField("PIN Code", validators=[DataRequired(), Length(min=4, max=10)])
    contact_mobile = StringField("Contact Number", validators=[DataRequired(), MOBILE_REGEX])
    payment_method = SelectField("Payment Method", choices=[("upi", "UPI (QR Code)"), ("cod", "Cash on Delivery")])

    utr_number = StringField(
        "UTR Number",
        validators=[Optional(), Length(max=50)]
    )

    payment_screenshot = FileField(
        "Payment Screenshot",
        validators=[
            FileAllowed(
                ["jpg","jpeg","png","webp"],
                "Upload JPG, PNG or WEBP"
            )
        ]
    )
    order_notes = TextAreaField("Order Notes", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Place Order")


class ApplyCouponForm(FlaskForm):
    code = StringField("Coupon Code", validators=[DataRequired(), Length(max=30)])
    submit = SubmitField("Apply")


class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Length(max=120)])
    mobile = StringField("Mobile", validators=[Optional(), Length(max=15)])
    subject = StringField("Subject", validators=[Optional(), Length(max=150)])
    message = TextAreaField("Message", validators=[DataRequired(), Length(max=2000)])
    submit = SubmitField("Send Message")
