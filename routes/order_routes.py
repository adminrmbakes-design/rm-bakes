from flask import Blueprint
from flask import render_template
from flask import redirect
from flask import url_for
from flask import jsonify

from flask_login import login_required
from flask_login import current_user

from sqlalchemy.orm import sessionmaker

from database import db
from database import Cart

from orders_database import Order

from datetime import datetime

from utils.notification_utils import (

    create_admin_notification

)

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

    # =====================================
    # ORDERS DATABASE SESSION
    # =====================================

    orders_engine = db.engines["orders"]

    OrdersSession = sessionmaker(
        bind=orders_engine
    )

    orders_session = OrdersSession()



    try:

        # =================================
        # DEBUG
        # =================================

        print("\n========== DEBUG ==========")

        print("CURRENT USER ID:")
        print(current_user.user_id)



        all_orders = orders_session.query(
            Order
        ).all()



        print("\nALL ORDERS IN DATABASE:")
        print(all_orders)



        print("\nALL USER IDS:")

        for existing_order in all_orders:

            print(existing_order.user_id)



        print("===========================\n")



        # =================================
        # GET USER ORDERS
        # =================================

        orders = orders_session.query(
            Order
        ).filter_by(

            user_id=current_user.user_id

        ).order_by(

            Order.ordered_at.desc()

        ).all()



        # =================================
        # CONVERT PRODUCTS JSON
        # =================================

        for order in orders:

            order.products = json.loads(
                order.products_json
            )



        return render_template(

            "orders.html",

            orders=orders

        )



    finally:

        orders_session.close()



# =========================================
# ORDER DETAILS
# =========================================

@order_bp.route(
    "/order/<int:order_id>"
)
@login_required
def order_details(order_id):

    # =====================================
    # ORDERS DATABASE SESSION
    # =====================================

    orders_engine = db.engines["orders"]

    OrdersSession = sessionmaker(
        bind=orders_engine
    )

    orders_session = OrdersSession()



    try:

        order = orders_session.query(
            Order
        ).filter_by(

            order_id=order_id,

            user_id=current_user.user_id

        ).first()



        if not order:

            return redirect(
                url_for("order.my_orders")
            )



        # =================================
        # CONVERT PRODUCTS JSON
        # =================================

        order.products = json.loads(
            order.products_json
        )



        return render_template(

            "order_details.html",

            order=order

        )



    finally:

        orders_session.close()



# =========================================
# CANCEL ORDER
# =========================================

@order_bp.route(
    "/cancel-order/<int:order_id>",
    methods=["POST"]
)
@login_required
def cancel_order(order_id):

    # =====================================
    # ORDERS DATABASE SESSION
    # =====================================

    orders_engine = db.engines["orders"]

    OrdersSession = sessionmaker(
        bind=orders_engine
    )

    orders_session = OrdersSession()



    try:

        order = orders_session.query(
            Order
        ).filter_by(

            order_id=order_id,

            user_id=current_user.user_id

        ).first()



        # =================================
        # ORDER NOT FOUND
        # =================================

        if not order:

            return jsonify({

                "success": False,

                "message":
                "Order not found 😭"

            })



        # =================================
        # CANCEL RULE
        # =================================

        allowed_status = [

            "queued",

            "approved"

        ]



        if order.order_status not in allowed_status:

            return jsonify({

                "success": False,

                "message":
                "This order cannot be cancelled 😭"

            })



        # =================================
        # CANCEL ORDER
        # =================================

        order.order_status = "cancelled"



        order.cancelled_at = (
            datetime.utcnow()
        )



        orders_session.commit()



        # =================================
        # CREATE ADMIN NOTIFICATION
        # =================================

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

            "message":
            "Order cancelled successfully 😭"

        })



    except Exception as error:

        orders_session.rollback()



        return jsonify({

            "success": False,

            "message":
            str(error)

        })



    finally:

        orders_session.close()



# =========================================
# ORDER AGAIN
# =========================================

@order_bp.route(
    "/order-again/<int:order_id>",
    methods=["POST"]
)
@login_required
def order_again(order_id):

    # =====================================
    # ORDERS DATABASE SESSION
    # =====================================

    orders_engine = db.engines["orders"]

    OrdersSession = sessionmaker(
        bind=orders_engine
    )

    orders_session = OrdersSession()



    try:

        order = orders_session.query(
            Order
        ).filter_by(

            order_id=order_id,

            user_id=current_user.user_id

        ).first()



        if not order:

            return jsonify({

                "success": False,

                "message":
                "Order not found 😭"

            })



        # =================================
        # CONVERT PRODUCTS JSON
        # =================================

        products = json.loads(
            order.products_json
        )



        # =================================
        # ADD TO CART
        # =================================

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

                    product_quantity=
                        item["product_quantity"],

                    note=item["note"]

                )



                db.session.add(cart_item)



        db.session.commit()



        return jsonify({

            "success": True,

            "message":
            "Items added to cart again 🍰",

            "redirect":
            url_for("cart.cart")

        })



    except Exception as error:

        db.session.rollback()



        return jsonify({

            "success": False,

            "message":
            str(error)

        })



    finally:

        orders_session.close()