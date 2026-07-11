from flask import Blueprint, render_template

legal_bp = Blueprint("legal", __name__)


@legal_bp.route("/privacy-policy")
def privacy_policy():
    return render_template("legal/privacy_policy.html")


@legal_bp.route("/terms-and-conditions")
def terms():
    return render_template("legal/terms.html")


@legal_bp.route("/refund-policy")
def refund_policy():
    return render_template("legal/refund_policy.html")


@legal_bp.route("/shipping-policy")
def shipping_policy():
    return render_template("legal/shipping_policy.html")
