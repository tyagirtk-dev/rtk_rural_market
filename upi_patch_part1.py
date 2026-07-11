from pathlib import Path
import sqlite3

BASE = Path(".")
DB = BASE / "database" / "rtk_rural_market.db"

print("=" * 60)
print("RTK Rural Market - UPI Patch Part 1")
print("=" * 60)

# --------------------------------------------------
# DATABASE
# --------------------------------------------------

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("PRAGMA table_info(orders)")
cols = [x[1] for x in cur.fetchall()]

if "utr_number" not in cols:
    print("Adding utr_number...")
    cur.execute(
        "ALTER TABLE orders ADD COLUMN utr_number TEXT"
    )

if "payment_screenshot" not in cols:
    print("Adding payment_screenshot...")
    cur.execute(
        "ALTER TABLE orders ADD COLUMN payment_screenshot TEXT"
    )

conn.commit()
conn.close()

print("Database patched.")

# --------------------------------------------------
# PAYMENT UPLOAD DIRECTORY
# --------------------------------------------------

upload_dir = BASE / "static" / "uploads" / "payments"
upload_dir.mkdir(parents=True, exist_ok=True)

print("Upload folder ready.")

# --------------------------------------------------
# CHECKOUT FORM
# --------------------------------------------------

form_file = BASE / "forms" / "checkout_forms.py"

text = form_file.read_text()

if "FileField" not in text:

    text = text.replace(
        "from wtforms import StringField, TextAreaField, SelectField, SubmitField",
        "from wtforms import StringField, TextAreaField, SelectField, SubmitField"
        ", FileField",
    )

    text = text.replace(
        "from wtforms.validators import DataRequired, Length, Optional",
        "from wtforms.validators import DataRequired, Length, Optional",
    )

    text = text.replace(
        "from forms.auth_forms import MOBILE_REGEX",
        "from forms.auth_forms import MOBILE_REGEX\n"
        "from flask_wtf.file import FileAllowed",
    )

    old = """    payment_method = SelectField("Payment Method", choices=[("upi", "UPI (QR Code)"), ("cod", "Cash on Delivery")])
"""

    new = old + """
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
"""

    text = text.replace(old, new)

    form_file.write_text(text)

    print("Checkout form patched.")

else:
    print("Checkout form already patched.")

# --------------------------------------------------
# ORDER MODEL
# --------------------------------------------------

model = BASE / "models" / "order.py"

txt = model.read_text()

if "utr_number" not in txt:

    target = """    payment_status = db.Column(db.String(20), default="pending")  # pending / paid / failed
"""

    replacement = target + """

    utr_number = db.Column(db.String(50))

    payment_screenshot = db.Column(
        db.String(255)
    )

"""

    txt = txt.replace(target, replacement)

    model.write_text(txt)

    print("Order model patched.")

else:
    print("Order model already patched.")

print()
print("PART 1 COMPLETED SUCCESSFULLY")
