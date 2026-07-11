from pathlib import Path

# -----------------------------------------------------
# CHECKOUT TEMPLATE
# -----------------------------------------------------

checkout = Path("templates/checkout/checkout.html")

text = checkout.read_text()

old = """
          <div id="upiBox" class="rtk-card p-3 text-center mb-3" style="max-width:260px; background:var(--rtk-green-100);">
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={{ upi_url|urlencode }}" class="img-fluid" alt="UPI QR">
            <p class="fw-bold mt-2 mb-1">₹{{ '%.2f'|format(grand_total) }}</p>
            <p class="small mb-0">Scan with Google Pay, PhonePe, Paytm or any UPI app.</p>
          </div>
"""

new = """
          <div id="upiBox" class="rtk-card p-3 text-center mb-3" style="background:var(--rtk-green-100);">

            <img
            src="https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={{ upi_url|urlencode }}"
            class="img-fluid mb-3"
            style="max-width:250px;">

            <h5>₹{{ '%.2f'|format(grand_total) }}</h5>

            <p class="small mb-3">
            Scan using Google Pay / PhonePe / Paytm
            </p>

            <div class="mb-3 text-start">
                {{ form.utr_number.label(class="form-label") }}
                {{ form.utr_number(class="form-control", placeholder="Enter UTR Number") }}
            </div>

            <div class="mb-2 text-start">
                {{ form.payment_screenshot.label(class="form-label") }}
                {{ form.payment_screenshot(class="form-control") }}
            </div>

          </div>
"""

if "payment_screenshot" not in text:
    text = text.replace(old, new)

checkout.write_text(text)

print("checkout.html patched")

# -----------------------------------------------------
# ADMIN PAYMENTS
# -----------------------------------------------------

admin = Path("templates/admin/payments.html")

text = admin.read_text()

if "UTR" not in text:

    text = text.replace(
        "<th>Amount</th>",
        "<th>Amount</th><th>UTR</th><th>Screenshot</th>"
    )

    text = text.replace(
        "<td>₹{{ '%.2f'|format(order.grand_total) }}</td>",
        """
<td>₹{{ '%.2f'|format(order.grand_total) }}</td>

<td>{{ order.utr_number or '-' }}</td>

<td>
{% if order.payment_screenshot %}
<a
target="_blank"
href="{{ url_for('static', filename=order.payment_screenshot) }}"
class="btn btn-sm btn-primary">
View
</a>
{% else %}
-
{% endif %}
</td>
"""
    )

admin.write_text(text)

print("admin payments patched")

# -----------------------------------------------------
# ORDER CONFIRMATION
# -----------------------------------------------------

confirm = Path("templates/orders/confirmation.html")

text = confirm.read_text()

old = """
          <p class="small mb-0 mt-2">Scan to pay via UPI</p>
"""

new = """
          <p class="small mb-2 mt-2">
          Payment submitted for verification.
          </p>

          <p class="small">
          <strong>UTR:</strong>
          {{ order.utr_number }}
          </p>

          {% if order.payment_screenshot %}
          <a
          target="_blank"
          href="{{ url_for('static', filename=order.payment_screenshot) }}"
          class="btn btn-sm btn-outline-success">

          View Uploaded Screenshot

          </a>
          {% endif %}
"""

if "View Uploaded Screenshot" not in text:
    text = text.replace(old, new)

confirm.write_text(text)

print("confirmation patched")

print()
print("="*60)
print("PART 3 COMPLETED")
print("="*60)
