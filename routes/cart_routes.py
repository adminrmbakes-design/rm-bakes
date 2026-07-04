"""
CART ROUTES — RM Bakes
Supports both logged-in (DB cart) and guest (session cart) users.
Guests can add/view/modify cart fully; login is only required at checkout.
"""

import uuid

from flask import Blueprint, redirect, url_for, flash, render_template
from flask import request, jsonify, session

from flask_login import current_user

from database import db, Cart, Product

from utils.feature_manager import is_feature_live

cart_bp = Blueprint("cart", __name__)


GUEST_CART_UNAVAILABLE_MESSAGE = "Guest Cart is currently unavailable. Please login to continue."


def guest_cart_blocked():
    """Standard response when a guest tries to use the cart while the
    guest_cart feature is COMING_SOON or DISABLED. Always redirects to
    login per spec, for both states."""
    flash(GUEST_CART_UNAVAILABLE_MESSAGE, "warning")
    return redirect(url_for("auth.login"))


# ─────────────────────────────────────────────
# GUEST CART SESSION HELPERS
# ─────────────────────────────────────────────

def get_guest_cart():
    """Return guest cart list from Flask session."""
    return session.get("guest_cart", [])


def save_guest_cart(cart):
    """Persist guest cart list back into Flask session."""
    session["guest_cart"] = cart
    session.modified = True


def merge_guest_cart(user_id):
    """
    Called right after login_user().
    Merges any session guest cart items into the user's DB cart,
    then clears the session guest cart.
    """
    guest_cart = get_guest_cart()
    if not guest_cart:
        return
    for item in guest_cart:
        pid = item.get("product_id")
        qty = item.get("quantity", 1)
        note = item.get("note", "")
        if not pid:
            continue
        existing = Cart.query.filter_by(user_id=user_id, product_id=pid).first()
        if existing:
            existing.product_quantity += qty
        else:
            db.session.add(Cart(
                user_id=user_id,
                product_id=pid,
                product_quantity=qty,
                note=note
            ))
    db.session.commit()
    session.pop("guest_cart", None)
    session.modified = True


# ─────────────────────────────────────────────
# VIEW CART  (works for guests too)
# ─────────────────────────────────────────────

@cart_bp.route("/cart")
def cart():
    if current_user.is_authenticated:
        # ── Logged-in: DB cart ──
        cart_items = Cart.query.filter_by(user_id=current_user.user_id).all()
        total_price = sum(
            (Product.query.get(i.product_id).product_price * i.product_quantity)
            for i in cart_items
            if Product.query.get(i.product_id)
        )
        return render_template(
            "cart.html",
            cart_items=cart_items,
            total_price=total_price,
            Product=Product,
            is_guest=False
        )
    else:
        # ── Guest: session cart ──
        if not is_feature_live("guest_cart"):
            return guest_cart_blocked()

        guest_cart = get_guest_cart()
        total_price = 0
        for item in guest_cart:
            product = Product.query.get(item["product_id"])
            if product:
                total_price += product.product_price * item["quantity"]
        return render_template(
            "cart.html",
            guest_cart=guest_cart,
            total_price=total_price,
            Product=Product,
            is_guest=True
        )


# ─────────────────────────────────────────────
# ADD TO CART  (works for guests too)
# ─────────────────────────────────────────────

@cart_bp.route("/add_to_cart/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)

    if current_user.is_authenticated:
        # ── Logged-in: DB cart ──
        existing = Cart.query.filter_by(
            user_id=current_user.user_id,
            product_id=product_id
        ).first()
        if existing:
            existing.product_quantity += 1
        else:
            db.session.add(Cart(
                user_id=current_user.user_id,
                product_id=product_id,
                product_quantity=1
            ))
        db.session.commit()
    else:
        # ── Guest: session cart ──
        if not is_feature_live("guest_cart"):
            return guest_cart_blocked()

        guest_cart = get_guest_cart()
        existing = next((i for i in guest_cart if i["product_id"] == product_id), None)
        if existing:
            existing["quantity"] += 1
        else:
            guest_cart.append({
                "product_id": product_id,
                "quantity": 1,
                "note": "",
                "gid": uuid.uuid4().hex[:10]   # unique guest item id
            })
        save_guest_cart(guest_cart)

    return jsonify({
        "success": True,
        "message": f"{product.product_name} added to cart 🛒"
    })


# ─────────────────────────────────────────────
# INCREASE QUANTITY
# ─────────────────────────────────────────────

@cart_bp.route("/increase_quantity/<int:item_id>", methods=["POST"])
def increase_quantity(item_id):
    if current_user.is_authenticated:
        cart_item = Cart.query.get_or_404(item_id)
        cart_item.product_quantity += 1
        db.session.commit()
        return jsonify({
            "success": True,
            "quantity": cart_item.product_quantity,
            "message": "Quantity increased ✨"
        })
    return jsonify({"success": False, "message": "Login required"})


# ─────────────────────────────────────────────
# GUEST: INCREASE QUANTITY  (by product_id in session)
# ─────────────────────────────────────────────

@cart_bp.route("/guest_increase/<int:product_id>", methods=["POST"])
def guest_increase(product_id):
    if not is_feature_live("guest_cart"):
        return guest_cart_blocked()

    guest_cart = get_guest_cart()
    item = next((i for i in guest_cart if i["product_id"] == product_id), None)
    if item:
        item["quantity"] += 1
        save_guest_cart(guest_cart)
        return jsonify({"success": True, "quantity": item["quantity"], "message": "Updated ✨"})
    return jsonify({"success": False, "message": "Item not found"})


# ─────────────────────────────────────────────
# DECREASE QUANTITY
# ─────────────────────────────────────────────

@cart_bp.route("/decrease_quantity/<int:item_id>", methods=["POST"])
def decrease_quantity(item_id):
    if current_user.is_authenticated:
        cart_item = Cart.query.get_or_404(item_id)
        if cart_item.product_quantity > 1:
            cart_item.product_quantity -= 1
            db.session.commit()
            return jsonify({
                "success": True,
                "removed": False,
                "quantity": cart_item.product_quantity,
                "message": "Quantity decreased"
            })
        else:
            db.session.delete(cart_item)
            db.session.commit()
            return jsonify({
                "success": True,
                "removed": True,
                "quantity": 0,
                "message": "Item removed 🗑️"
            })
    return jsonify({"success": False, "message": "Login required"})


# ─────────────────────────────────────────────
# GUEST: DECREASE QUANTITY
# ─────────────────────────────────────────────

@cart_bp.route("/guest_decrease/<int:product_id>", methods=["POST"])
def guest_decrease(product_id):
    if not is_feature_live("guest_cart"):
        return guest_cart_blocked()

    guest_cart = get_guest_cart()
    item = next((i for i in guest_cart if i["product_id"] == product_id), None)
    if item:
        if item["quantity"] > 1:
            item["quantity"] -= 1
            save_guest_cart(guest_cart)
            return jsonify({"success": True, "removed": False, "quantity": item["quantity"], "message": "Updated"})
        else:
            guest_cart.remove(item)
            save_guest_cart(guest_cart)
            return jsonify({"success": True, "removed": True, "quantity": 0, "message": "Item removed 🗑️"})
    return jsonify({"success": False, "message": "Item not found"})


# ─────────────────────────────────────────────
# REMOVE FROM CART
# ─────────────────────────────────────────────

@cart_bp.route("/remove_item/<int:item_id>", methods=["POST"])
def remove_item(item_id):
    if current_user.is_authenticated:
        cart_item = Cart.query.get_or_404(item_id)
        product = Product.query.get(cart_item.product_id)
        name = product.product_name if product else "Item"
        db.session.delete(cart_item)
        db.session.commit()
        return jsonify({"success": True, "message": f"{name} removed 🗑️"})
    return jsonify({"success": False, "message": "Login required"})


# ─────────────────────────────────────────────
# GUEST: REMOVE ITEM
# ─────────────────────────────────────────────

@cart_bp.route("/guest_remove/<int:product_id>", methods=["POST"])
def guest_remove(product_id):
    if not is_feature_live("guest_cart"):
        return guest_cart_blocked()

    guest_cart = get_guest_cart()
    item = next((i for i in guest_cart if i["product_id"] == product_id), None)
    if item:
        guest_cart.remove(item)
        save_guest_cart(guest_cart)
        product = Product.query.get(product_id)
        name = product.product_name if product else "Item"
        return jsonify({"success": True, "message": f"{name} removed 🗑️"})
    return jsonify({"success": False, "message": "Item not found"})


# ─────────────────────────────────────────────
# UPDATE CART NOTE  (logged-in only)
# ─────────────────────────────────────────────

@cart_bp.route("/update-cart-note/<int:cart_id>", methods=["POST"])
def update_cart_note(cart_id):
    if not current_user.is_authenticated:
        return jsonify({"success": False, "message": "Login required"})
    cart_item = Cart.query.get_or_404(cart_id)
    cart_item.note = request.form.get("note", "")
    db.session.commit()
    return jsonify({"success": True, "message": "Note saved ✨"})


# ─────────────────────────────────────────────
# DELETE NOTE  (logged-in only)
# ─────────────────────────────────────────────

@cart_bp.route("/delete-cart-note/<int:cart_id>", methods=["POST"])
def delete_cart_note(cart_id):
    if not current_user.is_authenticated:
        return jsonify({"success": False, "message": "Login required"})
    cart_item = Cart.query.get_or_404(cart_id)
    cart_item.note = ""
    db.session.commit()
    return jsonify({"success": True, "message": "Note removed 🗑️"})


# ─────────────────────────────────────────────
# UPDATE CART QTY (form-based, logged-in)
# ─────────────────────────────────────────────

@cart_bp.route("/update_cart/<int:cart_id>", methods=["POST"])
def update_cart(cart_id):
    if not current_user.is_authenticated:
        return jsonify({"success": False})
    cart_item = Cart.query.get_or_404(cart_id)
    qty = max(1, int(request.form.get("product_quantity", 1)))
    cart_item.product_quantity = qty
    db.session.commit()
    return jsonify({"success": True, "quantity": qty, "message": "Cart updated ✨"})


# ─────────────────────────────────────────────
# API: AVAILABLE COUPONS (for checkout coupon picker)
# ─────────────────────────────────────────────

@cart_bp.route("/api/available-coupons")
def available_coupons_api():
    """
    Returns active, non-expired, non-maxed coupons that the
    current user has NOT already used. Works for guests too
    (guests see all active coupons without usage filter).
    """
    from coupons_database import Coupon, CouponUsage
    from datetime import datetime
    from flask import jsonify

    now  = datetime.utcnow()
    rows = Coupon.query.filter_by(is_active=True).all()

    result = []
    for c in rows:
        # Skip expired
        if c.expiry_date and c.expiry_date < now:
            continue
        # Skip usage-limit-reached
        if c.usage_limit and c.times_used >= c.usage_limit:
            continue
        # Skip if logged-in user already used it
        if current_user.is_authenticated:
            used = CouponUsage.query.filter_by(
                user_id=current_user.user_id,
                coupon_id=c.coupon_id
            ).count()
            if used > 0:
                continue

        if c.discount_type == "percentage":
            discount_str = f"{int(c.discount_value)}% off"
        else:
            discount_str = f"₹{int(c.discount_value)} off"

        result.append({
            "code":          c.coupon_code,
            "title":         c.coupon_title,
            "description":   c.coupon_description or "",
            "discount":      discount_str,
            "discount_type": c.discount_type,
            "discount_value":c.discount_value,
            "min_order":     c.minimum_order_amount or 0,
            "banner":        c.coupon_banner or "",
            "popularity":    c.popularity_text or "",
            "scope":         c.scope or "cart",
            "target":        c.target_product or c.target_category or ""
        })

    return jsonify(result)


# ─────────────────────────────────────────────
# CLEAR ENTIRE CART  (FIX #3)
# Works for both logged-in (DB cart) and guest (session cart) users.
# ─────────────────────────────────────────────

@cart_bp.route("/clear-cart", methods=["POST"])
def clear_cart():
    from flask import jsonify

    if current_user.is_authenticated:
        items = Cart.query.filter_by(user_id=current_user.user_id).all()
        count = len(items)
        for item in items:
            db.session.delete(item)
        db.session.commit()
    else:
        if not is_feature_live("guest_cart"):
            return guest_cart_blocked()

        guest_cart = get_guest_cart()
        count = len(guest_cart)
        save_guest_cart([])

    if count == 0:
        return jsonify({"success": False, "message": "Cart is already empty"})

    return jsonify({
        "success": True,
        "message": f"Cart cleared — {count} item{'s' if count != 1 else ''} removed 🗑️"
    })
