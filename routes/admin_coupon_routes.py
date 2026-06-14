from flask import (

    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session

)

import cloudinary.uploader

import cloudinary_config

from datetime import datetime

from database import db

from database import Product

from database import GlobalNotification

from coupons_database import Coupon

from utils.admin_guard import (

    admin_required

)

from utils.notification_utils import (
    create_global_notification
)


# =========================================
# BLUEPRINT
# =========================================

admin_coupon_bp = Blueprint(

    "admin_coupon",

    __name__

)


# =========================================
# COUPON DASHBOARD
# =========================================

@admin_coupon_bp.route(
    "/admin/coupons"
)
@admin_required
def admin_coupons():

    coupons = (

        Coupon.query

        .order_by(
            Coupon.created_at.desc()
        )

        .all()

    )

    for coupon in coupons:
        
        if coupon.popularity_text:
            
            coupon.display_popularity = (

                coupon.popularity_text

            )
        
        else:
            
            if coupon.times_used == 0:
                
                coupon.display_popularity = (

                    "🌙 Waiting for its first sweet moment"

                )
            
            elif coupon.times_used == 1:
                
                coupon.display_popularity = (

                    "✨ 1 dessert lover claimed this deal"

                )
            
            elif coupon.times_used < 10:
                
                coupon.display_popularity = (

                    f"🍰 {coupon.times_used} sweet moments created"

                )
            
            elif coupon.times_used < 50:
                
                coupon.display_popularity = (

                    f"🔥 {coupon.times_used} dessert lovers claimed this deal"

                )
            
            elif coupon.times_used < 100:
                
                coupon.display_popularity = (
                    
                    f"💛 {coupon.times_used} happy dessert lovers saved more"

                )
            
            else:
                
                coupon.display_popularity = (
                    
                    f"👑 {coupon.times_used}+ dessert lovers couldn't resist this deal"

                )
                

    products = Product.query.order_by(
        Product.product_name.asc()
    ).all()

    categories = sorted(

        list(

            set(

                product.product_category

                for product in products

                if product.product_category

            )

        )

    )

    return render_template(

        "admin/admin_coupons.html",

        coupons=coupons,

        products=products,

        categories=categories,

        admin_username=session.get(
            "admin_username"
        ),

        admin_role=session.get(
            "admin_role"
        )

    )


# =========================================
# CREATE COUPON
# =========================================

@admin_coupon_bp.route(

    "/admin/coupons/create",

    methods=["POST"]

)
@admin_required
def create_coupon():

    coupon_code = request.form.get(
        "coupon_code"
    )

    coupon_title = request.form.get(
        "coupon_title"
    )

    coupon_description = request.form.get(
        "coupon_description"
    )

    discount_type = request.form.get(
        "discount_type"
    )

    discount_value = request.form.get(
        "discount_value"
    )

    minimum_order_amount = request.form.get(
        "minimum_order_amount"
    )

    usage_limit = request.form.get(
        "usage_limit"
    )

    maximum_discount = request.form.get(
        "maximum_discount"
    )

    expiry_date = request.form.get(
        "expiry_date"
    )

    scope = request.form.get(
        "scope"
    )

    target_product = request.form.get(
        "target_product"
    )

    target_category = request.form.get(
        "target_category"
    )

    popularity_text = request.form.get(
        "popularity_text"
    )

    coupon_banner = request.files.get(
        "coupon_banner"
    )

    existing_coupon = Coupon.query.filter_by(

        coupon_code=coupon_code

    ).first()

    if existing_coupon:

        flash(

            "Coupon code already exists 😭",

            "danger"

        )

        return redirect(

            url_for(
                "admin_coupon.admin_coupons"
            )

        )

    if not coupon_banner:
        
        flash(
            
            "Coupon banner is required 😭",

            "danger"

        )
        
        return redirect(

            url_for(
                
                "admin_coupon.admin_coupons"
            
            )

        )

    parsed_expiry_date = None

    if expiry_date:

        parsed_expiry_date = datetime.strptime(

            expiry_date,

            "%Y-%m-%dT%H:%M"

        )

    upload_result = cloudinary.uploader.upload(

        coupon_banner,

        folder="rm_bakes/coupons"

    )
    
    banner_url = (

        upload_result["secure_url"]

    )

    coupon = Coupon(

        coupon_code=coupon_code,

        coupon_title=coupon_title,

        coupon_description=coupon_description,

        coupon_banner=banner_url,

        discount_type=discount_type,

        discount_value=float(
            discount_value
        ),

        minimum_order_amount=float(
            minimum_order_amount or 0
        ),

        usage_limit=int(
            usage_limit
        ) if usage_limit else None,

        maximum_discount=float(
            maximum_discount
        ) if maximum_discount else None,

        expiry_date=parsed_expiry_date,

        scope=scope,

        target_product=target_product,

        target_category=target_category,

        popularity_text=popularity_text

    )

    # =====================================
    # AUTO NOTIFICATION MESSAGE
    # =====================================

    if coupon.discount_type == "percentage":

        notification_message = (

            f"🎉 Enjoy {int(coupon.discount_value)}% OFF "

            f"with coupon code "

            f"{coupon.coupon_code}."

        )

    else:

        notification_message = (

            f"💸 Save ₹{int(coupon.discount_value)} "

            f"with coupon code "

            f"{coupon.coupon_code}."

        )
        
    if coupon.minimum_order_amount:
        notification_message += (
            f"\n\nAdd minimum SWEET EXPERIENCES of ₹{coupon.minimum_order_amount}."
        )

    db.session.add(
        coupon
    )

    db.session.commit()

    # =====================================
    # CREATE GLOBAL NOTIFICATION
    # =====================================

    create_global_notification(

        title=f"🎟️ {coupon.coupon_title}",

        message=notification_message,

        banner_image=coupon.coupon_banner,

        notification_type="coupon",

        coupon_code=coupon.coupon_code,

        priority = 5,
        
        expires_at=coupon.expiry_date,

        is_featured=True,

        is_active=coupon.is_active

    )

    flash(

        "Sweet surprise created 🎉",

        "success"

    )

    return redirect(

        url_for(
            "admin_coupon.admin_coupons"
        )

    )


# =========================================
# UPDATE COUPON
# =========================================

@admin_coupon_bp.route(

    "/admin/coupons/update/<int:coupon_id>",

    methods=["POST"]

)
@admin_required
def update_coupon(coupon_id):

    new_coupon_banner = request.files.get(
        "coupon_banner"
    )

    coupon = Coupon.query.get_or_404(

        coupon_id

    )

    #==== TEMP VARIABLE old_coupon_code ======

    old_coupon_code = coupon.coupon_code

    expiry_date = request.form.get(

        "expiry_date"

    )

    parsed_expiry_date = None

    if expiry_date:

        parsed_expiry_date = datetime.strptime(

            expiry_date,

            "%Y-%m-%dT%H:%M"

        )

    coupon.coupon_code = request.form.get(

        "coupon_code"

    )

    coupon.coupon_title = request.form.get(

        "coupon_title"

    )

    coupon.coupon_description = request.form.get(

        "coupon_description"

    )

    coupon.discount_type = request.form.get(

        "discount_type"

    )

    coupon.discount_value = float(

        request.form.get(
            "discount_value"
        ) or 0

    )

    coupon.minimum_order_amount = float(

        request.form.get(
            "minimum_order_amount"
        ) or 0

    )

    coupon.usage_limit = (

        int(
            request.form.get(
                "usage_limit"
            )
        )

        if request.form.get(
            "usage_limit"
        )

        else None

    )

    coupon.maximum_discount = (

        float(
            request.form.get(
                "maximum_discount"
            )
        )

        if request.form.get(
            "maximum_discount"
        )

        else None

    )

    coupon.scope = request.form.get(
        "scope"
    )
    
    # ==========================
    # PRODUCT COUPON
    # ==========================

    if coupon.scope == "product":
        
        coupon.target_product = (
            request.form.get(
                "target_product"
            )
        )
        
        coupon.target_category = None

    # ==========================
    # CATEGORY COUPON
    # ==========================

    elif coupon.scope == "category":
        
        coupon.target_category = (
            request.form.get(
                "target_category"
            )
        )
        
        coupon.target_product = None

    # ==========================
    # ENTIRE CART
    # ==========================

    else:
        
        coupon.target_product = None
        coupon.target_category = None
    # ---------------------------------

    coupon.popularity_text = request.form.get(

        "popularity_text"

    )

    coupon.expiry_date = (

        parsed_expiry_date

    )

    # =====================================
    # FIND LINKED NOTIFICATION
    # =====================================
    
    notification = GlobalNotification.query.filter_by(
        coupon_code=old_coupon_code
    ).first()

    print("=" * 50)
    print("LOOKING FOR:", old_coupon_code)
    print("FOUND:", notification)
    print("=" * 50)

    # =====================================
    # UPDATED NOTIFICATION MESSAGE
    # =====================================

    if coupon.discount_type == "percentage":
        
        notification_message = (
            f"🎉 Enjoy {int(coupon.discount_value)}% OFF "
            f"with coupon code {coupon.coupon_code}."
        )
    
    else:
        
        notification_message = (
            f"💸 Save ₹{int(coupon.discount_value)} "
            f"with coupon code {coupon.coupon_code}."
        )
        
    if coupon.minimum_order_amount:
        
        notification_message += (
            f"\n\nAdd minimum SWEET EXPERIENCES of ₹{int(coupon.minimum_order_amount)}."
        )

    if (

        new_coupon_banner

        and

        new_coupon_banner.filename

    ):
        upload_result = cloudinary.uploader.upload(

            new_coupon_banner,

            folder="rm_bakes/coupons"

        )
        
        coupon.coupon_banner = (

            upload_result["secure_url"]

        )

    if notification:

        notification.coupon_code = (
            coupon.coupon_code
        )
        
        notification.title = (
            f"🎟️ {coupon.coupon_title}"
        )
        
        notification.message = (
            notification_message
        )
        
        notification.banner_image = (
            coupon.coupon_banner
        )
        
        notification.expires_at = (
            coupon.expiry_date
        )
        
        notification.is_active = (
            coupon.is_active
        )

        print("=" * 50)
        print("NOTIFICATION FOUND")
        print("Old coupon:", old_coupon_code)
        print("New coupon:", coupon.coupon_code)
        print("Notification ID:", notification.notification_id)
        print("=" * 50)

    db.session.commit()

    print("COUPON UPDATE COMMITTED")

    flash(

        "Coupon updated successfully 🎉",

        "success"

    )

    return redirect(

        url_for(
            "admin_coupon.admin_coupons"
        )

    )



# =========================================
# TOGGLE COUPON
# =========================================

@admin_coupon_bp.route(

    "/admin/coupons/toggle/<int:coupon_id>",

    methods=["POST"]

)
@admin_required
def toggle_coupon(coupon_id):

    coupon = Coupon.query.get_or_404(

        coupon_id

    )

    coupon.is_active = (

        not coupon.is_active

    )

    db.session.commit()

    flash(

        "Coupon status updated ✨",

        "success"

    )

    return redirect(

        url_for(
            "admin_coupon.admin_coupons"
        )

    )


# =========================================
# DELETE COUPON
# =========================================

@admin_coupon_bp.route(

    "/admin/coupons/delete/<int:coupon_id>",

    methods=["POST"]

)
@admin_required
def delete_coupon(coupon_id):

    coupon = Coupon.query.get_or_404(

        coupon_id

    )

    db.session.delete(

        coupon

    )

    db.session.commit()

    flash(

        "Coupon deleted 🗑",

        "success"

    )

    return redirect(

        url_for(
            "admin_coupon.admin_coupons"
        )

    )
