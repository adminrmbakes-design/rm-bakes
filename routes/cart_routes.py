from flask import Blueprint
from flask import redirect
from flask import url_for
from flask import flash
from flask import render_template
from flask import request
from flask import jsonify

from flask_login import login_required
from flask_login import current_user

from database import db
from database import Cart
from database import Product


cart_bp = Blueprint(
    "cart",
    __name__
)


# =========================
# VIEW CART
# =========================

@cart_bp.route("/cart")
@login_required
def cart():

    cart_items = Cart.query.filter_by(
        user_id=current_user.user_id
    ).all()

    total_price = 0

    for item in cart_items:

        product = Product.query.get(
            item.product_id
        )

        if product:

            total_price += (
                product.product_price *
                item.product_quantity
            )

    return render_template(
        "cart.html",
        cart_items=cart_items,
        total_price=total_price,
        Product=Product
    )


# =========================
# ADD TO CART
# =========================

@cart_bp.route("/add_to_cart/<int:product_id>", methods=["POST"])
@login_required
def add_to_cart(product_id):

    existing_cart_item = Cart.query.filter_by(
        user_id=current_user.user_id,
        product_id=product_id
    ).first()

    if existing_cart_item:

        existing_cart_item.product_quantity += 1

    else:

        new_cart_item = Cart(
            user_id=current_user.user_id,
            product_id=product_id,
            product_quantity=1
        )

        db.session.add(new_cart_item)

    db.session.commit()

    product = Product.query.get_or_404(
    product_id
)

    return jsonify({
    "success": True,
    "message":
        f"{product.product_name} added to cart 🛒"

})


# =========================
# INCREASE QUANTITY
# =========================

@cart_bp.route(
    "/increase_quantity/<int:item_id>",
    methods=["POST"]
)
@login_required
def increase_quantity(item_id):

    cart_item = Cart.query.get_or_404(
        item_id
    )

    cart_item.product_quantity += 1

    db.session.commit()

    return jsonify({
        "success": True,
        "quantity": cart_item.product_quantity,
        "message": "Quantity increased ✨"
    })


# =========================
# DECREASE QUANTITY
# =========================

@cart_bp.route(
    "/decrease_quantity/<int:item_id>",
    methods=["POST"]
)
@login_required
def decrease_quantity(item_id):

    cart_item = Cart.query.get_or_404(
        item_id
    )

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
            "message": "Item removed from cart 🗑️"
        })


# =========================
# REMOVE FROM CART
# =========================

@cart_bp.route(
    "/remove_item/<int:item_id>",
    methods=["POST"]
)
@login_required
def remove_item(item_id):

    cart_item = Cart.query.get_or_404(
        item_id
    )

    product = Product.query.get(
        cart_item.product_id
    )

    product_name = "Item"

    if product:

        product_name = (
            product.product_name
        )

    db.session.delete(cart_item)

    db.session.commit()

    return jsonify({

        "success": True,

        "message":
            f"{product_name} removed from cart 🗑️"

    })


# =========================
# UPDATE CART NOTE
# =========================

@cart_bp.route(
    "/update-cart-note/<int:cart_id>",
    methods=["POST"]
)
@login_required
def update_cart_note(cart_id):

    cart_item = Cart.query.get_or_404(
        cart_id
    )

    note = request.form.get(
        "note"
    )

    cart_item.note = note

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Note saved ✨"
    })


# =========================
# DELETE NOTE
# =========================

@cart_bp.route(
    "/delete-cart-note/<int:cart_id>",
    methods=["POST"]
)
@login_required
def delete_cart_note(cart_id):

    cart_item = Cart.query.get_or_404(
        cart_id
    )

    cart_item.note = ""

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Note removed 🗑️"
    })


# =========================
# UPDATE CART
# =========================

@cart_bp.route(
    "/update_cart/<int:cart_id>",
    methods=["POST"]
)
@login_required
def update_cart(cart_id):

    cart_item = Cart.query.get_or_404(
        cart_id
    )

    product_quantity = int(
        request.form.get(
            "product_quantity"
        )
    )

    if product_quantity < 1:

        product_quantity = 1

    cart_item.product_quantity = (
        product_quantity
    )

    db.session.commit()

    return jsonify({
        "success": True,
        "quantity": cart_item.product_quantity,
        "message": "Cart updated ✨"
    })