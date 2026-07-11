from flask import Blueprint, render_template, redirect, url_for, flash

from models import db
from models.misc import ContactMessage, SiteSetting
from forms.checkout_forms import ContactForm
from services.email_service import send_contact_form_email

contact_bp = Blueprint("contact", __name__)


@contact_bp.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        msg = ContactMessage(
            name=form.name.data.strip(),
            email=form.email.data.strip(),
            mobile=form.mobile.data,
            subject=form.subject.data,
            message=form.message.data.strip(),
        )
        db.session.add(msg)
        db.session.commit()
        send_contact_form_email(msg)
        flash("Thanks for reaching out! We'll get back to you soon.", "success")
        return redirect(url_for("contact.contact"))

    site_settings = {
        "phone": SiteSetting.get("contact_phone", "+91 90000 00000"),
        "email": SiteSetting.get("contact_email", "hello@rtkruralmarket.com"),
        "whatsapp": SiteSetting.get("whatsapp_number", "919000000000"),
        "address": SiteSetting.get("address", "RTK Rural Market, Village Road, District, State - 000000"),
        "maps_embed": SiteSetting.get("google_maps_embed", ""),
    }
    return render_template("legal/contact.html", form=form, site=site_settings)
