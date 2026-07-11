from pathlib import Path

# =====================================================
# CHECKOUT JS
# =====================================================

checkout = Path("templates/checkout/checkout.html")

text = checkout.read_text()

if "toggleUPI()" not in text:

    js = """

<script>

function toggleUPI(){

    let upi=document.getElementById("pm_upi");

    let box=document.getElementById("upiBox");

    if(upi.checked){

        box.style.display="block";

    }else{

        box.style.display="none";

    }

}

document.addEventListener("DOMContentLoaded",function(){

    toggleUPI();

    document.getElementById("pm_upi").addEventListener("change",toggleUPI);

    document.getElementById("pm_cod").addEventListener("change",toggleUPI);

});

</script>

"""

    text=text.replace("{% endblock %}",js+"\n{% endblock %}")

checkout.write_text(text)

print("checkout javascript added")

# =====================================================
# ADMIN PAYMENT PAGE
# =====================================================

admin=Path("templates/admin/payments.html")

text=admin.read_text()

if "Approve" not in text:

    text=text.replace(

'<td><a href="{{ url_for(\'admin.order_detail\', order_number=order.order_number) }}" class="small">View Order</a></td>',

'''

<td>

<a href="{{ url_for('admin.order_detail',order_number=order.order_number) }}"

class="btn btn-sm btn-secondary">

Order

</a>

{% if order.payment_status=="pending" %}

<form method="post"

action="{{ url_for('admin.payment_approve',order_id=order.id) }}"

style="display:inline">

<button class="btn btn-sm btn-success">

Approve

</button>

</form>

<form method="post"

action="{{ url_for('admin.payment_reject',order_id=order.id) }}"

style="display:inline">

<button class="btn btn-sm btn-danger">

Reject

</button>

</form>

{% endif %}

</td>

'''

)

admin.write_text(text)

print("admin template updated")

# =====================================================
# ROUTES
# =====================================================

route=Path("routes/admin.py")

text=route.read_text()

if "payment_approve" not in text:

    text+=r'''

from flask import flash,redirect,url_for

@admin_bp.post("/payments/<int:order_id>/approve")

def payment_approve(order_id):

    order=Order.query.get_or_404(order_id)

    order.payment_status="paid"

    db.session.commit()

    notify_user(

        order.user_id,

        "Payment Approved",

        f"Payment for {order.order_number} approved.",

        category="payment"

    )

    flash("Payment Approved.","success")

    return redirect(url_for("admin.payments"))


@admin_bp.post("/payments/<int:order_id>/reject")

def payment_reject(order_id):

    order=Order.query.get_or_404(order_id)

    order.payment_status="failed"

    db.session.commit()

    notify_user(

        order.user_id,

        "Payment Rejected",

        f"Payment for {order.order_number} rejected.",

        category="payment"

    )

    flash("Payment Rejected.","warning")

    return redirect(url_for("admin.payments"))

'''

route.write_text(text)

print("admin routes updated")

print()

print("="*60)
print("PATCH COMPLETED SUCCESSFULLY")
print("="*60)
print("Restart Flask Server")
