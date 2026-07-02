# ============================================================
# checkout_routes.py  —  RM Bakes Payment Flow  (v14)
# ============================================================
#
# FLOW:
#   COD  → /create-payment  → creates order immediately
#                              returns { is_cod, redirect }
#
#   Online → /create-payment  → creates Razorpay order
#                               stores razorpay_order_id +
#                               expected_paise in session
#                               returns Razorpay config
#
#          → /verify-payment  → HMAC-SHA256 signature check
#                               cross-checks order_id & amount
#                               creates DB order ONLY if verified
#                               clears cart + session
#                               returns { success, redirect }
#
# /place-order is kept for legacy safety — routes to the
# same shared logic.
# ============================================================

from flask import Blueprint, render_template, redirect
from flask import url_for, jsonify, session, request

from flask_login import login_required, current_user

from database import db, Cart, Product, CouponUsage
from database import *

from orders_database import Order
from coupons_database import Coupon

from utils.notification_utils import create_admin_notification

from datetime import datetime

import json
import random
import hmac
import hashlib
import razorpay
import os
import logging

logger = logging.getLogger(__name__)


# ============================================================
# RAZORPAY CLIENT  (lazy — avoids crash if env not set)
# ============================================================

def _razorpay_client():
    key_id     = os.getenv("RAZORPAY_KEY_ID",     "")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET", "")
    if not key_id or not key_secret:
        raise RuntimeError(
            "Razorpay credentials are not configured. "
            "Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET."
        )
    return razorpay.Client(auth=(key_id, key_secret))


# ============================================================
# BLUEPRINT
# ============================================================

checkout_bp = Blueprint("checkout", __name__)


# ============================================================
# HELPER — DELIVERY FEE
# ============================================================

def calculate_delivery_fee(subtotal: float) -> float:
    if subtotal < 200:
        return 70.0
    elif subtotal < 400:
        return 50.0
    elif subtotal < 500:
        return 30.0
    return 0.0


# ============================================================
# HELPER — CALCULATE ORDER TOTALS  (single source of truth)
# ============================================================

def calculate_order_totals(user_id: int) -> dict | None:
    """
    Reads the cart from DB, applies the session coupon, and
    returns a fully-calculated totals dict.

    Returns None if the cart is empty.

    Keys returned:
        products       — list of product dicts for products_json
        subtotal       — float
        delivery_fee   — float
        discount_amount— float
        coupon_code    — str | None
        grand_total    — float  (never negative)
    """
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    if not cart_items:
        return None

    products     = []
    subtotal     = 0.0

    for item in cart_items:
        product = Product.query.get(item.product_id)
        if not product:
            continue

        item_total = product.product_price * item.product_quantity
        subtotal  += item_total

        products.append({
            "product_id":       product.product_id,
            "product_name":     product.product_name,
            "product_image":    product.product_image,
            "product_price":    product.product_price,
            "product_quantity": item.product_quantity,
            "product_unit":     product.product_unit,
            "note":             item.note,
            "total_price":      item_total,
        })

    delivery_fee    = calculate_delivery_fee(subtotal)
    discount_amount = float(session.get("discount_amount", 0))
    coupon_code     = session.get("coupon_code")

    grand_total = max(0.0, subtotal + delivery_fee - discount_amount)

    return {
        "products":        products,
        "subtotal":        round(subtotal,        2),
        "delivery_fee":    round(delivery_fee,    2),
        "discount_amount": round(discount_amount, 2),
        "coupon_code":     coupon_code,
        "grand_total":     round(grand_total,     2),
    }


# ============================================================
# HELPER — GENERATE ORDER NUMBER
# ============================================================

def _generate_order_number() -> str:
    ts  = datetime.now().strftime("%Y%m%d%H%M%S")
    rnd = random.randint(100, 999)
    return f"RM{ts}{rnd}"


# ============================================================
# HELPER — BUILD & COMMIT ORDER OBJECT
# ============================================================

def _create_order_record(
    totals:          dict,
    payment_method:  str,
    payment_status:  str,
    payment_verified:bool,
    payment_gateway: str = "None",
    payment_mode:    str | None = None,
    razorpay_order_id:   str | None = None,
    razorpay_payment_id: str | None = None,
    transaction_reference: str | None = None,
    payment_failure_reason: str | None = None,
) -> Order:
    """
    Creates, adds, and commits an Order.
    Also handles coupon usage increment.
    Raises on DB failure (caller should rollback).
    """
    order_number = _generate_order_number()

    new_order = Order(
        # ── user snapshot ──
        user_id          = current_user.user_id,
        username         = current_user.username,
        email            = current_user.email,
        full_name        = current_user.full_name,
        phone_number     = current_user.phone_number,
        delivery_address = current_user.delivery_address,
        landmark         = current_user.landmark,
        city             = current_user.city,
        pincode          = current_user.pincode,
        google_maps_link = current_user.google_maps_link,

        # ── order identity ──
        order_number  = order_number,
        order_status  = "queued",
        order_source  = "menu_order",
        products_json = json.dumps(totals["products"]),

        # ── financials ──
        subtotal        = totals["subtotal"],
        delivery_fee    = totals["delivery_fee"],
        discount_amount = totals["discount_amount"],
        coupon_code     = totals["coupon_code"],
        grand_total     = totals["grand_total"],
        total_amount    = totals["grand_total"],

        # ── payment ──
        payment_method    = payment_method,
        payment_status    = payment_status,
        payment_verified  = payment_verified,
        payment_gateway   = payment_gateway,
        payment_mode      = payment_mode,
        razorpay_order_id = razorpay_order_id,
        razorpay_payment_id       = razorpay_payment_id,
        transaction_reference     = transaction_reference,
        payment_failure_reason    = payment_failure_reason,
        payment_completed_at      = datetime.utcnow() if payment_verified else None,
    )

    db.session.add(new_order)
    db.session.flush()   # get new_order.order_id before coupon update

    # ── coupon usage ──
    coupon_code = totals["coupon_code"]
    if coupon_code:
        coupon = Coupon.query.filter_by(
            coupon_code=coupon_code
        ).first()
        if coupon:
            coupon.times_used += 1
            usage = CouponUsage(
                user_id=current_user.user_id,
                coupon_code=coupon_code
            )
            db.session.add(usage)

    db.session.commit()
    return new_order


# ============================================================
# HELPER — CLEAR CART + SESSION AFTER ORDER
# ============================================================

def _post_order_cleanup(user_id: int):
    Cart.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    for key in ("coupon_code", "discount_amount", "discount_target",
                "razorpay_order_id", "pending_paise"):
        session.pop(key, None)


# ============================================================
# CHECKOUT PAGE
# ============================================================

@checkout_bp.route("/checkout")
@login_required
def checkout_page():
    cart_items = Cart.query.filter_by(
        user_id=current_user.user_id
    ).all()

    if not cart_items:
        return redirect(url_for("cart.cart"))

    # re-use the shared totals calculator for the page render
    totals = calculate_order_totals(current_user.user_id) or {
        "products": [], "subtotal": 0, "delivery_fee": 0,
        "discount_amount": 0, "coupon_code": None, "grand_total": 0,
    }

    # build checkout_items list for template display
    checkout_items = []
    for item in cart_items:
        product = Product.query.get(item.product_id)
        if not product:
            continue
        checkout_items.append({
            "product_id":       product.product_id,
            "product_name":     product.product_name,
            "product_image":    product.product_image,
            "product_price":    product.product_price,
            "product_quantity": item.product_quantity,
            "product_unit":     product.product_unit,
            "note":             item.note,
            "total_price":      product.product_price * item.product_quantity,
        })

    return render_template(
        "checkout.html",
        checkout_items  = checkout_items,
        subtotal        = totals["subtotal"],
        delivery_fee    = totals["delivery_fee"],
        discount_amount = totals["discount_amount"],
        applied_coupon  = session.get("coupon_code"),
        discount_target = session.get("discount_target"),
        grand_total     = totals["grand_total"],
    )


# ============================================================
# APPLY COUPON
# ============================================================

@checkout_bp.route("/apply-coupon", methods=["POST"])
@login_required
def apply_coupon():
    try:
        if session.get("coupon_code"):
            return jsonify({
                "success": False,
                "message": "✨ A Sweet Deal is already applied to your order!"
            })

        coupon_code = (
            request.json.get("coupon_code", "").strip().upper()
        )

        coupon = Coupon.query.filter_by(coupon_code=coupon_code).first()

        if not coupon:
            return jsonify({"success": False, "message": "🌙 That Sweet Deal couldn't be found!"})
        if not coupon.is_active:
            return jsonify({"success": False, "message": "🌙 Sweet Deal is tucked away for now!"})
        if coupon.usage_limit and coupon.times_used >= coupon.usage_limit:
            return jsonify({"success": False, "message": "🌸 This Sweet Deal has found all its happy homes."})
        if coupon.expiry_date and coupon.expiry_date < datetime.utcnow():
            return jsonify({"success": False, "message": "⏳ This Sweet Deal has already melted away."})

        existing = CouponUsage.query.filter_by(
            user_id=current_user.user_id,
            coupon_code=coupon.coupon_code
        ).first()
        if existing:
            return jsonify({"success": False, "message": "👀 You've already enjoyed this Sweet Deal once."})

        # ── calculate eligible amount ──
        cart_items = Cart.query.filter_by(user_id=current_user.user_id).all()
        subtotal = eligible_amount = 0.0

        for item in cart_items:
            product = Product.query.get(item.product_id)
            if not product:
                continue
            line = product.product_price * item.product_quantity
            subtotal += line
            if coupon.scope == "cart":
                eligible_amount += line
            elif coupon.scope == "product" and product.product_name == coupon.target_product:
                eligible_amount += line
            elif coupon.scope == "category" and product.product_category == coupon.target_category:
                eligible_amount += line

        if eligible_amount <= 0:
            return jsonify({"success": False, "message": "✨ This Sweet Deal isn't applicable to your cart 🍰"})

        if subtotal < coupon.minimum_order_amount:
            return jsonify({
                "success": False,
                "message": f"🌟 Add a little more sweetness to unlock this offer! (min ₹{coupon.minimum_order_amount})"
            })

        # ── discount calculation ──
        if coupon.discount_type == "percentage":
            discount = (eligible_amount * coupon.discount_value) / 100
        else:
            discount = float(coupon.discount_value)

        if coupon.maximum_discount and discount > coupon.maximum_discount:
            discount = float(coupon.maximum_discount)

        discount = round(discount, 2)

        # ── scope label ──
        if coupon.scope == "product":
            session["discount_target"] = f"On {coupon.target_product} 🍰"
        elif coupon.scope == "category":
            session["discount_target"] = f"On {coupon.target_category} Collection ✨"
        else:
            session["discount_target"] = "On Your Entire Cart 🎉"

        session["coupon_code"]     = coupon.coupon_code
        session["discount_amount"] = discount

        return jsonify({
            "success":         True,
            "coupon_code":     coupon.coupon_code,
            "discount_amount": discount,
            "message":         "🍰 Sweet Deal applied! 🎉"
        })

    except Exception as exc:
        logger.exception("apply_coupon error")
        return jsonify({"success": False, "message": "Could not apply coupon — please try again."})


# ============================================================
# REMOVE COUPON
# ============================================================

@checkout_bp.route("/remove-coupon", methods=["POST"])
@login_required
def remove_coupon():
    session.pop("coupon_code",     None)
    session.pop("discount_amount", None)
    session.pop("discount_target", None)
    return jsonify({"success": True, "message": "✨ Coupon removed!"})


# ============================================================
# CREATE PAYMENT  (single entry-point for both COD & Online)
# ============================================================

@checkout_bp.route("/create-payment", methods=["POST"])
@login_required
def create_payment():
    """
    COD   → creates order immediately, returns { success, is_cod, redirect }
    Online→ creates Razorpay order, returns Razorpay checkout config
    """
    try:
        # ── profile guard ──
        if not all([
            current_user.full_name,
            current_user.phone_number,
            current_user.delivery_address
        ]):
            return jsonify({
                "success": False,
                "message": "Please complete your delivery profile first 🧁"
            })

        # ── shared totals ──
        totals = calculate_order_totals(current_user.user_id)
        if not totals:
            return jsonify({
                "success": False,
                "message": "Your cart is empty 🚶"
            })

        payment_method = (
            current_user.preferred_payment_method or "Online"
        ).strip()

        # ==================================================
        # PATH A — Cash on Delivery
        # ==================================================
        if payment_method == "COD":
            order = _create_order_record(
                totals           = totals,
                payment_method   = "COD",
                payment_status   = "pending",
                payment_verified = False,
                payment_gateway  = "None",
                payment_mode     = "cod",
            )

            _post_order_cleanup(current_user.user_id)

            create_admin_notification(
                title   = "New COD Order",
                message = (
                    f"Order: {order.order_number}\n"
                    f"Customer: {current_user.full_name}\n"
                    f"Total: ₹{totals['grand_total']}\n"
                    "Status: QUEUED | Payment: PENDING (COD)"
                ),
                notification_type = "new_order"
            )

            logger.info("COD order created: %s", order.order_number)

            return jsonify({
                "success":  True,
                "is_cod":   True,
                "redirect": url_for("order.my_orders")
            })

        # ==================================================
        # PATH B — Online (Razorpay)
        # ==================================================
        paise = int(totals["grand_total"] * 100)
        if paise <= 0:
            return jsonify({
                "success": False,
                "message": "Order total must be greater than zero for online payment."
            })

        client = _razorpay_client()

        razorpay_order = client.order.create({
            "amount":          paise,
            "currency":        "INR",
            "payment_capture": 1,
        })

        # Store in session so verify-payment can cross-check
        session["razorpay_order_id"] = razorpay_order["id"]
        session["pending_paise"]     = paise

        return jsonify({
            "success":     True,
            "is_cod":      False,
            "key":         os.getenv("RAZORPAY_KEY_ID", ""),
            "amount":      paise,
            "currency":    "INR",
            "order_id":    razorpay_order["id"],
            "name":        "RM Bakes",
            "description": "Bakery Order",
            "prefill": {
                "name":    current_user.full_name,
                "email":   current_user.email,
                "contact": current_user.phone_number,
            },
        })

    except RuntimeError as exc:
        # Razorpay credentials missing
        logger.error("Razorpay config error: %s", exc)
        return jsonify({
            "success": False,
            "message": "Payment gateway is not configured. Please contact support."
        })

    except razorpay.errors.BadRequestError as exc:
        logger.exception("Razorpay BadRequestError")
        return jsonify({
            "success": False,
            "message": "Payment gateway rejected the request. Please try again."
        })

    except Exception as exc:
        logger.exception("create_payment error")
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": "Something went wrong while starting payment. Please try again."
        })


# ============================================================
# VERIFY PAYMENT  (backend HMAC-SHA256 verification)
# ============================================================

@checkout_bp.route("/verify-payment", methods=["POST"])
@login_required
def verify_payment():
    """
    1. Checks razorpay_order_id matches what WE created (anti-tamper)
    2. HMAC-SHA256 signature verification
    3. Recalculates totals fresh from DB
    4. Creates the order record with full payment details
    5. Clears cart + session
    """
    try:
        data                 = request.get_json(force=True) or {}
        rzp_payment_id       = data.get("razorpay_payment_id",  "")
        rzp_order_id         = data.get("razorpay_order_id",    "")
        rzp_signature        = data.get("razorpay_signature",   "")

        # ── step 1: anti-tamper — order ID must match session ──
        expected_order_id = session.get("razorpay_order_id", "")
        if not expected_order_id or rzp_order_id != expected_order_id:
            logger.warning(
                "verify_payment: order_id mismatch. "
                "Got %s, expected %s (user %s)",
                rzp_order_id, expected_order_id, current_user.user_id
            )
            return jsonify({
                "success": False,
                "message": "Payment session mismatch. Please refresh and try again."
            })

        # ── step 2: HMAC-SHA256 signature verification ──
        key_secret = os.getenv("RAZORPAY_KEY_SECRET", "").encode()
        body       = f"{rzp_order_id}|{rzp_payment_id}".encode()
        expected_sig = hmac.new(key_secret, body, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected_sig, rzp_signature):
            logger.warning(
                "verify_payment: signature mismatch for order %s (user %s)",
                rzp_order_id, current_user.user_id
            )
            return jsonify({
                "success": False,
                "message": "Payment signature verification failed. Please contact support."
            })

        # ── step 3: recalculate totals fresh from DB ──
        totals = calculate_order_totals(current_user.user_id)
        if not totals:
            return jsonify({
                "success": False,
                "message": "Cart was empty when we tried to confirm your order. Please contact support."
            })

        # ── step 4: optional amount sanity-check ──
        expected_paise = session.get("pending_paise", 0)
        actual_paise   = int(totals["grand_total"] * 100)
        if expected_paise and abs(actual_paise - expected_paise) > 1:
            logger.error(
                "verify_payment: amount mismatch! expected=%d actual=%d (user %s)",
                expected_paise, actual_paise, current_user.user_id
            )
            return jsonify({
                "success": False,
                "message": "Order amount mismatch detected. Please contact support."
            })

        # ── step 5: create verified order ──
        order = _create_order_record(
            totals               = totals,
            payment_method       = "Online",
            payment_status       = "paid",
            payment_verified     = True,
            payment_gateway      = "Razorpay",
            payment_mode         = None,       # Razorpay doesn't return mode here
            razorpay_order_id    = rzp_order_id,
            razorpay_payment_id  = rzp_payment_id,
            transaction_reference= rzp_payment_id,
        )

        # ── step 6: clear cart + session ──
        _post_order_cleanup(current_user.user_id)

        create_admin_notification(
            title   = "New Online Order — Payment Verified ✅",
            message = (
                f"Order: {order.order_number}\n"
                f"Customer: {current_user.full_name}\n"
                f"Total: ₹{totals['grand_total']}\n"
                f"Razorpay Payment ID: {rzp_payment_id}\n"
                "Status: QUEUED | Payment: PAID (Verified)"
            ),
            notification_type = "new_order"
        )

        logger.info(
            "Online order verified & created: %s (payment %s)",
            order.order_number, rzp_payment_id
        )

        return jsonify({
            "success":  True,
            "redirect": url_for("order.my_orders")
        })

    except Exception as exc:
        logger.exception("verify_payment error")
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": "Verification failed due to a server error. "
                       "If money was deducted, please contact support with your payment ID."
        })


# ============================================================
# PLACE ORDER  (legacy alias — routes to create_payment)
# ============================================================

@checkout_bp.route("/place-order", methods=["POST"])
@login_required
def place_order():
    """
    Kept for backwards-compatibility.
    All logic now lives in create_payment().
    """
    return create_payment()
