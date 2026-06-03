from flask import Blueprint
from flask import render_template
from flask import redirect
from flask import url_for
from flask import jsonify

from flask_login import login_required
from flask_login import current_user


from database import db
from database import Cart
from database import Product

from orders_database import Order

from datetime import datetime

from utils.notification_utils import (

    create_admin_notification

)

import json
import random



# =========================================
# BLUEPRINT
# =========================================

checkout_bp = Blueprint(
    "checkout",
    __name__
)



# =========================================
# CHECKOUT PAGE
# =========================================

@checkout_bp.route("/checkout")
@login_required
def checkout_page():

    cart_items = Cart.query.filter_by(
        user_id=current_user.user_id
    ).all()



    if not cart_items:

        return redirect(
            url_for("cart.cart")
        )



    checkout_items = []

    subtotal = 0



    for item in cart_items:

        product = Product.query.get(
            item.product_id
        )



        if not product:
            continue



        total_price = (

            product.product_price *

            item.product_quantity

        )



        subtotal += total_price



        checkout_items.append({

            "product_id":
                product.product_id,

            "product_name":
                product.product_name,

            "product_image":
                product.product_image,

            "product_price":
                product.product_price,

            "product_quantity":
                item.product_quantity,

            "product_unit":
                product.product_unit,

            "note":
                item.note,

            "total_price":
                total_price

        })



    delivery_fee = 40



    grand_total = (

        subtotal +

        delivery_fee

    )



    return render_template(

        "checkout.html",

        checkout_items=checkout_items,

        subtotal=subtotal,

        delivery_fee=delivery_fee,

        grand_total=grand_total

    )



# =========================================
# PLACE ORDER
# =========================================

@checkout_bp.route(
    "/place-order",
    methods=["POST"]
)
@login_required
def place_order():

    orders_session = None

    try:

        # =================================
        # PROFILE VALIDATION
        # =================================

        required_fields = [

            current_user.full_name,

            current_user.phone_number,

            current_user.delivery_address

        ]



        if not all(required_fields):

            return jsonify({

                "success": False,

                "message":
                "Complete your profile details first 😭"

            })




        # =================================
        # GET CART
        # =================================

        cart_items = Cart.query.filter_by(
            user_id=current_user.user_id
        ).all()



        if not cart_items:

            return jsonify({

                "success": False,

                "message":
                "Your cart is empty 😭"

            })



        # =================================
        # GENERATE ORDER NUMBER
        # =================================

        timestamp = datetime.now().strftime(
            "%Y%m%d%H%M%S"
        )



        random_number = random.randint(
            100,
            999
        )



        order_number = (
            f"RM{timestamp}{random_number}"
        )



        # =================================
        # BUILD PRODUCTS JSON
        # =================================

        products = []

        subtotal = 0



        for item in cart_items:

            product = Product.query.get(
                item.product_id
            )



            if not product:
                continue



            item_total = (

                product.product_price *

                item.product_quantity

            )



            subtotal += item_total



            products.append({

                "product_id":
                    product.product_id,

                "product_name":
                    product.product_name,

                "product_image":
                    product.product_image,

                "product_price":
                    product.product_price,

                "product_quantity":
                    item.product_quantity,

                "product_unit":
                    product.product_unit,

                "note":
                    item.note,

                "total_price":
                    item_total

            })



        # =================================
        # TOTALS
        # =================================

        delivery_fee = 40



        grand_total = (

            subtotal +

            delivery_fee

        )



        # =================================
        # CREATE ORDER
        # =================================

        new_order = Order(

            user_id=current_user.user_id,

            username=current_user.username,

            email=current_user.email,

            full_name=current_user.full_name,

            phone_number=current_user.phone_number,

            delivery_address=
                current_user.delivery_address,

            landmark=
                current_user.landmark,

            city=
                current_user.city,

            pincode=
                current_user.pincode,

            google_maps_link=
                current_user.google_maps_link,

            payment_method=
                current_user.preferred_payment_method,

            order_number=order_number,

            order_status="queued",

            products_json=json.dumps(
                products
            ),

            subtotal=subtotal,

            delivery_fee=delivery_fee,

            grand_total=grand_total

        )



        db.session.add(new_order)

        db.session.commit()



        # =================================
        # CREATE ADMIN NOTIFICATION
        # =================================

        create_admin_notification(

            title="New Order Received",

            message=f"""

Order:
{order_number}

Customer:
{current_user.full_name}

Total:
₹{grand_total}

Status:
QUEUED

""",

            notification_type="new_order"

        )



        # =================================
        # CLEAR CART
        # =================================

        for item in cart_items:

            db.session.delete(item)



        db.session.commit()



        print("\nORDER SAVED")
        print(order_number)
        print()



        return jsonify({

            "success": True,

            "redirect":
            url_for("order.my_orders")

        })



    except Exception as error:



        db.session.rollback()



        print("\nORDER ERROR:")
        print(error)
        print()



        return jsonify({

            "success": False,

            "message":
            str(error)

        })



    finally:
        
