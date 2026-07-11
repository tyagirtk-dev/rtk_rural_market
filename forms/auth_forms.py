from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Regexp, Optional

MOBILE_REGEX = Regexp(r"^[6-9]\d{9}$", message="Enter a valid 10-digit Indian mobile number.")


class RegistrationForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=120)])
    mobile_number = StringField("Mobile Number", validators=[DataRequired(), MOBILE_REGEX])
    email = StringField("Email Address", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create Account")


class OTPVerifyForm(FlaskForm):
    otp_code = StringField("OTP", validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField("Verify")


class LoginForm(FlaskForm):
    mobile_number = StringField("Mobile Number", validators=[DataRequired(), MOBILE_REGEX])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me", default=False)
    submit = SubmitField("Login")


class ForgotPasswordRequestForm(FlaskForm):
    mobile_number = StringField("Mobile Number", validators=[DataRequired(), MOBILE_REGEX])
    submit = SubmitField("Send OTP")


class ForgotPasswordVerifyForm(FlaskForm):
    otp_code = StringField("OTP", validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField("Verify")


class ResetPasswordForm(FlaskForm):
    new_password = PasswordField("New Password", validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[DataRequired(), EqualTo("new_password", message="Passwords must match.")],
    )
    submit = SubmitField("Reset Password")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[DataRequired(), EqualTo("new_password", message="Passwords must match.")],
    )
    submit = SubmitField("Change Password")
