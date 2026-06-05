from flask import Blueprint, render_template, redirect, url_for, jsonify
from flask_login import login_required, current_user

from database import db, Cart
from orders_database import Order, ProductReview

from datetime import datetime

from utils.notification_utils import create_admin_notification

import json


# =========================================
# BLUEPRINT
# =========================================

order_bp = Blueprint(
    "order",
    __name__
)


# =========================================
# MY ORDERS
# =========================================

@order_bp.route("/my-orders")
@login_required
def my_orders():

    try:

        print("\n========== DEBUG ==========")
        print("CURRENT USER ID:")
        print(current_user.user_id)

        all_orders = Order.query.all()

        print("\nALL ORDERS IN DATABASE:")
        print(all_orders)

        print("\nALL USER IDS:")

        for existing_order in all_orders:
            print(existing_order.user_id)

        print("===========================\n")

        orders = Order.query.filter_by(
            user_id=current_user.user_id
        ).order_by(
            Order.ordered_at.desc()
        ).all()

        for order in orders:
            order.products = json.loads(
                order.products_json
            )
            
            order.has_review = (
                
                ProductReview.query.filter_by(
                    
                    order_id=order.order_id,
                    customer_id=current_user.user_id
                ).first()

                is not None
            )

        return render_template(
            "orders.html",
            orders=orders
        )

    except Exception as error:

        print("MY ORDERS ERROR:", error)

        return render_template(
            "orders.html",
            orders=[]
        )


# =========================================
# ORDER DETAILS
# =========================================

@order_bp.route("/order/<int:order_id>")
@login_required
def order_details(order_id):

    try:

        order = Order.query.filter_by(
            order_id=order_id,
            user_id=current_user.user_id
        ).first()

        if not order:
            return redirect(
                url_for("order.my_orders")
            )

        order.products = json.loads(
            order.products_json
        )

        order.has_review = (
            ProductReview.query.filter_by(
                order_id=order.order_id,
                customer_id=current_user.user_id
            ).first()

            is not None

        )

        return render_template(
            "order_details.html",
            order=order
        )

    except Exception as error:

        print("ORDER DETAILS ERROR:", error)

        return redirect(
            url_for("order.my_orders")
        )


# =========================================
# CANCEL ORDER
# =========================================

@order_bp.route(
    "/cancel-order/<int:order_id>",
    methods=["POST"]
)
@login_required
def cancel_order(order_id):

    try:

        order = Order.query.filter_by(
            order_id=order_id,
            user_id=current_user.user_id
        ).first()

        if not order:

            return jsonify({
                "success": False,
                "message": "Order not found 😭"
            })

        allowed_status = [
            "queued",
            "approved"
        ]

        if order.order_status not in allowed_status:

            return jsonify({
                "success": False,
                "message": "This order cannot be cancelled 😭"
            })

        order.order_status = "cancelled"

        order.cancelled_at = datetime.utcnow()

        db.session.commit()

        create_admin_notification(
            title="Order Cancelled",
            message=f"""

Order:
{order.order_number}

Customer:
{order.full_name}

Status:
CANCELLED

""",
            notification_type="cancelled"
        )

        return jsonify({
            "success": True,
            "message": "Order cancelled successfully 😭"
        })

    except Exception as error:

        db.session.rollback()

        return jsonify({
            "success": False,
            "message": str(error)
        })


# =========================================
# ORDER AGAIN
# =========================================

@order_bp.route(
    "/order-again/<int:order_id>",
    methods=["POST"]
)
@login_required
def order_again(order_id):

    try:

        order = Order.query.filter_by(
            order_id=order_id,
            user_id=current_user.user_id
        ).first()

        if not order:

            return jsonify({
                "success": False,
                "message": "Order not found 😭"
            })

        products = json.loads(
            order.products_json
        )

        for item in products:

            existing_cart_item = Cart.query.filter_by(
                user_id=current_user.user_id,
                product_id=item["product_id"]
            ).first()

            if existing_cart_item:

                existing_cart_item.product_quantity += (
                    item["product_quantity"]
                )

            else:

                cart_item = Cart(
                    user_id=current_user.user_id,
                    product_id=item["product_id"],
                    product_quantity=item["product_quantity"],
                    note=item.get("note", "")
                )

                db.session.add(cart_item)

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Items added to cart again 🍰",
            "redirect": url_for("cart.cart")
        })

    except Exception as error:

        db.session.rollback()

        return jsonify({
            "success": False,
            "message": str(error)
        })
