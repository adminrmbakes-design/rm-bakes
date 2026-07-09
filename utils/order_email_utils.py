import json

from utils.email_sender import send_email
from utils.timezone_utils import to_ist


# =========================================
# CONFIG
# =========================================
# All mail currently lands in one inbox (no custom domain verified on
# Resend yet — send_email() itself hardcodes the destination), so the
# receiver_email passed below is the *intended* recipient. The day a
# domain gets verified and send_email() is switched to deliver to the
# real address, every call site here already passes the right one —
# nothing else needs to change.

ADMIN_EMAIL = "admin.rmbakes@gmail.com"


# =========================================
# HELPERS
# =========================================

def _order_items_lines(order):
    """Turns order.products_json into friendly item lines with
    quantity, price, and any per-item note."""

    try:
        items = json.loads(order.products_json or "[]")
    except Exception:
        items = []

    lines = []

    for item in items:

        name     = item.get("product_name", "Item")
        qty      = item.get("product_quantity", 1)
        price    = item.get("product_price")
        note     = item.get("note")

        line = f"• {name} ×{qty}"

        if price is not None:
            line += f" — ₹{price:.0f} each"

        if note:
            line += f" (Note: {note})"

        lines.append(line)

    return lines or ["• (items unavailable)"]


def _payment_block(order):
    """Payment status line, with details when payment is actually done."""

    if order.payment_verified or (order.payment_status or "").lower() == "paid":

        lines = [f"💳 Payment: Paid via {order.payment_mode or order.payment_gateway or 'Online'}"]

        if order.payment_completed_at:
            lines.append(
                f"   Paid on: {to_ist(order.payment_completed_at).strftime('%d %b %Y, %I:%M %p')} IST"
            )

        if order.razorpay_payment_id:
            lines.append(f"   Transaction ID: {order.razorpay_payment_id}")

        lines.append(f"   Amount Paid: ₹{order.grand_total:.0f}")

        return "\n".join(lines)

    return f"💳 Payment: {order.payment_method or 'Cash on Delivery'} (Pay on delivery)"


def _customer_display_name(order):
    return order.full_name or order.username or "there"


# =========================================
# ORDER CONFIRMATION (on order creation)
# =========================================

def send_order_confirmation_email(order):

    try:

        item_lines = "\n".join(_order_items_lines(order))

        body = f"""🎉 Hi {_customer_display_name(order)}!

Thank you for choosing RM Bakes ❤️

We've received your order #{order.order_number} and it's now confirmed.

🍰 Items:
{item_lines}

Subtotal: ₹{order.subtotal:.0f}
Delivery Fee: ₹{order.delivery_fee:.0f}
{f"Discount ({order.coupon_code}): -₹{order.discount_amount:.0f}" if order.discount_amount else ""}
Grand Total: ₹{order.grand_total:.0f}

{_payment_block(order)}

We'll begin preparing your order shortly.

Thank you for baking sweet memories with us! ✨
"""

        send_email(
            receiver_email=order.email,
            subject=f"Order Confirmed — #{order.order_number} 🎉",
            body=body
        )

    except Exception as error:
        print(f"order confirmation email failed: {error}")


# =========================================
# ORDER STATUS UPDATE
# =========================================

STATUS_EMAIL_LINES = {

    "approved":
        "🎉 Great news — your order has been approved and is next in line for the kitchen!",

    "preparing":
        "👨‍🍳 Our chefs have started preparing your order.",

    "baking":
        "🍰 Your cake is now baking with love.",

    "packed":
        "📦 Your order has been packed carefully and is ready to head out.",

    "out_for_delivery":
        "🚚 Your order is out for delivery — it'll be with you soon!",

    "delivered":
        "✅ Your order was delivered. We hope you loved it!",

    "cancelled":
        "❌ Your order has been cancelled. If this wasn't expected, reach out to us anytime.",

}


def send_order_status_email(order, new_status):

    try:

        headline = STATUS_EMAIL_LINES.get(
            new_status,
            f"Your order status is now: {new_status.replace('_', ' ').title()}"
        )

        item_lines = "\n".join(_order_items_lines(order))

        body = f"""Hi {_customer_display_name(order)},

{headline}

🧾 Order #{order.order_number}

🍰 Items:
{item_lines}

Grand Total: ₹{order.grand_total:.0f}

{_payment_block(order)}

Thank you for baking sweet memories with us! ✨
"""

        send_email(
            receiver_email=order.email,
            subject=f"Order #{order.order_number} — {new_status.replace('_', ' ').title()}",
            body=body
        )

    except Exception as error:
        print(f"order status email failed: {error}")


# =========================================
# NEW PRODUCT LAUNCH (one announcement — see
# CONFIG note above on why this isn't per-user)
# =========================================

def send_new_product_email(product):

    try:

        body = f"""🍰 Fresh From The Oven!

{product.product_name} just landed on the RM Bakes menu.

{product.product_description or ''}

Price: ₹{product.product_price:.0f}

Come take a look before it sells out! 💛
"""

        send_email(
            receiver_email=ADMIN_EMAIL,
            subject=f"🍰 New Product Live: {product.product_name}",
            body=body
        )

    except Exception as error:
        print(f"new product email failed: {error}")


# =========================================
# NEW COUPON LAUNCH (one announcement)
# =========================================

def send_new_coupon_email(coupon):

    try:

        body = f"""🎟️ {coupon.coupon_title}

Use code: {coupon.coupon_code}

{coupon.coupon_description or ''}

{f"Valid until {to_ist(coupon.expiry_date).strftime('%d %b %Y')} IST" if coupon.expiry_date else ""}

Happy baking! 💛
"""

        send_email(
            receiver_email=ADMIN_EMAIL,
            subject=f"🎟️ New Coupon Live: {coupon.coupon_code}",
            body=body
        )

    except Exception as error:
        print(f"new coupon email failed: {error}")


# =========================================
# ADMIN ALERTS
# =========================================

def send_admin_new_order_email(order):

    try:

        item_lines = "\n".join(_order_items_lines(order))

        body = f"""📥 New order received!

Order #{order.order_number}
Customer: {_customer_display_name(order)} ({order.email})

🍰 Items:
{item_lines}

Grand Total: ₹{order.grand_total:.0f}
{_payment_block(order)}
"""

        send_email(
            receiver_email=ADMIN_EMAIL,
            subject=f"📥 New Order #{order.order_number}",
            body=body
        )

    except Exception as error:
        print(f"admin new-order email failed: {error}")


def send_admin_new_user_email(user):

    try:

        body = f"""👋 A new customer just joined RM Bakes!

Username: {user.username}
Email: {user.email}
"""

        send_email(
            receiver_email=ADMIN_EMAIL,
            subject="👋 New User Registered",
            body=body
        )

    except Exception as error:
        print(f"admin new-user email failed: {error}")


def send_admin_new_custom_order_email(custom_order):

    try:

        body = f"""🎂 A new Custom Order request just came in!

Request Code: {custom_order.request_code}
Customer: {custom_order.full_name or custom_order.username} ({custom_order.email})

Category: {custom_order.dessert_category}
Flavor: {custom_order.flavor}
Quantity: {custom_order.quantity}
Occasion: {custom_order.occasion or 'N/A'}

Head to the admin panel to review and quote it.
"""

        send_email(
            receiver_email=ADMIN_EMAIL,
            subject="🎂 New Custom Order Request",
            body=body
        )

    except Exception as error:
        print(f"admin new-custom-order email failed: {error}")
