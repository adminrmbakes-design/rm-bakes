from flask import (

    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session

)

from datetime import datetime

from database import db

from coupons_database import Coupon

from utils.admin_guard import (

    admin_required

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

    return render_template(

        "admin/admin_coupons.html",

        coupons=coupons,

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

    discount_type = request.form.get(
        "discount_type"
    )

    discount_value = request.form.get(
        "discount_value"
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

    coupon = Coupon(

        coupon_code=coupon_code,

        coupon_title=coupon_title,

        discount_type=discount_type,

        discount_value=float(
            discount_value
        )

    )

    db.session.add(
        coupon
    )

    db.session.commit()

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
