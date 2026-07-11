from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length, Email, Optional

from forms.auth_forms import MOBILE_REGEX


class ProfileForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email Address", validators=[Optional(), Email(), Length(max=120)])
    submit = SubmitField("Save Changes")


class AddressForm(FlaskForm):
    label = StringField("Label (Home / Work / Other)", validators=[DataRequired(), Length(max=50)])
    full_address = StringField("Full Address", validators=[DataRequired(), Length(max=300)])
    city = StringField("City", validators=[DataRequired(), Length(max=100)])
    pin_code = StringField("PIN Code", validators=[DataRequired(), Length(min=4, max=10)])
    landmark = StringField("Landmark", validators=[Optional(), Length(max=150)])
    is_default = BooleanField("Set as default address")
    submit = SubmitField("Save Address")


class DeleteAccountForm(FlaskForm):
    password = PasswordField("Confirm your password", validators=[DataRequired()])
    submit = SubmitField("Permanently Delete My Account")
