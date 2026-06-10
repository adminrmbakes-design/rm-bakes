from flask import Blueprint
from flask import render_template
from flask import redirect
from flask import url_for
from flask import jsonify
from flask import session
from flask import request

from flask_login import login_required
from flask_login import current_user

from database import db
from database import Cart
from database import Product

from orders_database import Order

from coupons_database import Coupon

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
# DELIVERY FEE HELPER
# =========================================

def calculate_delivery_fee(
    subtotal
):

    if subtotal < 200:

        return 70

    elif subtotal < 400:

        return 50

    elif subtotal < 500:

        return 30

    return 0


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

    delivery_fee = calculate_delivery_fee(subtotal) #Delivery fee function call

    discount_amount = session.get("discount_amount",0)
    
    
    grand_total = (

        subtotal +

        delivery_fee -

        discount_amount

    )

    
    if grand_total < 0:
        
        grand_total = 0
        

    return render_template(

        "checkout.html",

        checkout_items=checkout_items,

        subtotal=subtotal,

        delivery_fee=delivery_fee,

        discount_amount=discount_amount,

        applied_coupon=session.get(
            "coupon_code"),

        discount_target=session.get(
            "discount_target"),

        grand_total=grand_total

    )

# =========================================
# APPLY COUPON
# =========================================

@checkout_bp.route(
    "/apply-coupon",
    methods=["POST"]
)
@login_required
def apply_coupon():

    #If already applied coupon

    if session.get(
        "coupon_code"
    ):
        return jsonify({

            "success": False,

            "message":

            "✨ This Sweet Deal is already brightening your order!"

        })

    coupon_code = (

        request.json.get(
            "coupon_code",
            ""
        )

        .strip()

        .upper()

    )

    coupon = Coupon.query.filter_by(

        coupon_code=coupon_code

    ).first()

    if not coupon:

        return jsonify({

            "success": False,

            "message":
            "🌙 That Sweet Deal couldn't be found!"

        })

    if not coupon.is_active:

        return jsonify({

            "success": False,

            "message":
            "🌙 Sweet Deal tucked away for now!"

        })
        

    if (

        coupon.usage_limit

        and

        coupon.times_used >= coupon.usage_limit

    ):
        return jsonify({

            "success": False,

            "message":

            "🌸 This Sweet Deal has already found all its happy homes."

        })

    if (

        coupon.expiry_date

        and

        coupon.expiry_date <
        datetime.utcnow()

    ):

        return jsonify({

            "success": False,

            "message":
            "⏳ This Sweet Deal has already melted away."

        })

    # =========================
    # CART TOTAL
    # =========================

    cart_items = Cart.query.filter_by(

        user_id=current_user.user_id

    ).all()

    subtotal = 0

    eligible_amount = 0

    for item in cart_items:
        product = Product.query.get(
            item.product_id
        )
        
        if not product:
            continue
            
        line_total = (

            product.product_price *

            item.product_quantity

        )
        subtotal += line_total
        
        # =====================
        # ENTIRE CART
        # =====================
        
        if coupon.scope == "cart":
            
            eligible_amount += line_total
        

        # =====================
        # PRODUCT COUPON
        # =====================
        
        elif coupon.scope == "product":
            
            if (
                product.product_name ==
                coupon.target_product
            ):
                eligible_amount += line_total
                
        # =====================
        # CATEGORY COUPON
        # =====================
        
        elif coupon.scope == "category":
            
            if (
                product.product_category ==
                coupon.target_category

            ):
                eligible_amount += line_total

    if eligible_amount <= 0:
        
        return jsonify({
            "success": False,
            "message": "✨ This Sweet Deal isn't applicable to your cart 🍰"
        })

    # =========================
    # MINIMUM ORDER
    # =========================

    if (

        subtotal <

        coupon.minimum_order_amount

    ):

        return jsonify({

            "success": False,

            "message":

            f"🌟 Just a little more of sweetness is needed to unlock this offer! \nMinimun of ₹{coupon.minimum_order_amount}"

        })

    # =========================
    # CALCULATE DISCOUNT
    # =========================

    discount_amount = 0

    if coupon.discount_type == "percentage":

        discount_amount = (

            eligible_amount *

            coupon.discount_value

        ) / 100

    else:

        discount_amount = (

            coupon.discount_value

        )

    if (

        coupon.maximum_discount

        and

        discount_amount >

        coupon.maximum_discount

    ):

        discount_amount = (

            coupon.maximum_discount

        )

    # =========================
    # SAVE SESSION
    # =========================

    session["coupon_code"] = (

        coupon.coupon_code

    )
    
    session["discount_amount"] = (

        round( 
            discount_amount,
            2
        )

    )

    if coupon.scope == "product":
        
        session["discount_target"] = (
            f"On {coupon.target_product} 🍰"
        )
    
    elif coupon.scope == "category":
        
        session["discount_target"] = (
            f"On {coupon.target_category} Collection ✨"
        )
    
    else:
        
        session["discount_target"] = (
            "On Your Entire Cart 🎉"
        )
    

    return jsonify({

        "success": True,

        "coupon_code":

        coupon.coupon_code,

        "discount_amount":

        round(
            discount_amount,
            2
        ),

        "message":

        "🍰 Your sweet surprise is waiting at checkout! 🎉"

    })

# =========================================
# REMOVE COUPON
# =========================================

@checkout_bp.route(
    "/remove-coupon",
    methods=["POST"]
)
@login_required
def remove_coupon():

    session.pop(
        "coupon_code",
        None
    )

    session.pop(
        "discount_amount",
        None
    )

    session.pop(
        "discount_target",
        None
    )

    
    return jsonify({

        "success": True,

        "message":
        "✨ No worries, your treats are still waiting!"

    })

# =========================================
# PLACE ORDER
# =========================================

@checkout_bp.route(
    "/place-order",
    methods=["POST"]
)
@login_required
def place_order():

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
                "Fill your profile with sweetnes..🧁"

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
                "Your cart feels Lonely..🚶"

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

        delivery_fee = calculate_delivery_fee(
            subtotal
        )

        discount_amount = session.get(
            "discount_amount",
            0
        )
        
        coupon_code = session.get(
            "coupon_code"
        )

        grand_total = (

            subtotal +

            delivery_fee -
            
            discount_amount
        )

        if grand_total < 0:
            
            grand_total = 0

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

            discount_amount=discount_amount,

            coupon_code=coupon_code,

            grand_total=grand_total

        )

        db.session.add(new_order)

        db.session.commit()

        # =================================
        # UPDATE COUPON USAGE
        # =================================

        if coupon_code:
            
            coupon = Coupon.query.filter_by(

                coupon_code=coupon_code

            ).first()
            
            if coupon:
                
                coupon.times_used += 1
                
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

        # =================================
        # CLEAR COUPON SESSION
        # =================================

        session.pop(
            "coupon_code",
            None
        )

        session.pop(
            "discount_amount",
            None
        )

        session.pop(
            "discount_target",
            None
        )

        #==== Debug ====

        print("\nORDER SAVED")
        print(order_number)
        print()

        #===============

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
