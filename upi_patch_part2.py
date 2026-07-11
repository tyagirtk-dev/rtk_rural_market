from pathlib import Path

route = Path("routes/checkout.py")

text = route.read_text()

# -------------------------------------------------------
# Imports
# -------------------------------------------------------

if "secure_filename" not in text:

    text = text.replace(
        "from flask import Blueprint, render_template, redirect, url_for, flash, current_app",
        "from flask import Blueprint, render_template, redirect, url_for, flash, current_app\n"
        "from werkzeug.utils import secure_filename\n"
        "import uuid\n"
        "import os"
    )

# -------------------------------------------------------
# Upload + Validation
# -------------------------------------------------------

old = """    if form.validate_on_submit():
"""

new = """
    if form.validate_on_submit():

        payment_screenshot = None
        utr_number = None

        if form.payment_method.data == "upi":

            utr_number = (form.utr_number.data or "").strip()

            if not utr_number:
                flash("Please enter UTR Number.", "danger")
                return render_template(
                    "checkout/checkout.html",
                    form=form,
                    cart=cart,
                    subtotal=subtotal,
                    discount=discount,
                    delivery_charge=delivery_charge,
                    grand_total=grand_total,
                    upi_url=upi_url,
                )

            if not form.payment_screenshot.data:
                flash("Please upload payment screenshot.", "danger")
                return render_template(
                    "checkout/checkout.html",
                    form=form,
                    cart=cart,
                    subtotal=subtotal,
                    discount=discount,
                    delivery_charge=delivery_charge,
                    grand_total=grand_total,
                    upi_url=upi_url,
                )

            f = form.payment_screenshot.data

            ext = os.path.splitext(
                secure_filename(f.filename)
            )[1]

            filename = str(uuid.uuid4()) + ext

            upload_path = os.path.join(
                current_app.config["UPLOAD_FOLDER"],
                "payments"
            )

            os.makedirs(upload_path, exist_ok=True)

            save_path = os.path.join(upload_path, filename)

            f.save(save_path)

            payment_screenshot = "uploads/payments/" + filename
"""

text = text.replace(old, new)

# -------------------------------------------------------
# Save in Order
# -------------------------------------------------------

text = text.replace(

"""            payment_method=form.payment_method.data,""",

"""            payment_method=form.payment_method.data,
            utr_number=utr_number,
            payment_screenshot=payment_screenshot,"""

)

route.write_text(text)

print("="*60)
print("Checkout Route patched successfully.")
print("="*60)
