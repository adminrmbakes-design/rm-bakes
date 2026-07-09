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

from database import Carousel

from utils.admin_guard import (
    admin_required
)

# =========================================
# BLUEPRINT
# =========================================

admin_carousel_bp = Blueprint(

    "admin_carousel",

    __name__

)

# =========================================
# CAROUSEL DASHBOARD
# =========================================

@admin_carousel_bp.route(
    "/admin/carousels"
)
@admin_required
def admin_carousels():

    carousels = (

        Carousel.query

        .order_by(
            Carousel.carousel_priority.desc(),
            Carousel.carousel_created_at.desc()
        )

        .all()

    )

    return render_template(

        "admin/admin_carousels.html",

        carousels=carousels,

        admin_username=session.get(
            "admin_username"
        ),

        admin_role=session.get(
            "admin_role"
        )

    )

# =========================================
# CREATE CAROUSEL
# =========================================

@admin_carousel_bp.route(

    "/admin/carousels/create",

    methods=["POST"]

)
@admin_required
def create_carousel():

    carousel_title = request.form.get(
        "carousel_title"
    )

    carousel_description = request.form.get(
        "carousel_description"
    )

    carousel_category = request.form.get(
        "carousel_category"
    )

    carousel_visibility = request.form.get(
        "carousel_visibility"
    )

    carousel_action_text = request.form.get(
        "carousel_action_text"
    )

    carousel_action_link = request.form.get(
        "carousel_action_link"
    )

    carousel_priority = int(

        request.form.get(
            "carousel_priority",
            0
        )

    )

    starts_at = request.form.get(
        "carousel_starts_at"
    )

    expires_at = request.form.get(
        "carousel_expires_at"
    )

    carousel_banner = request.files.get(
        "carousel_banner"
    )

    if not carousel_banner:

        flash(

            "Carousel banner is required 😭",

            "danger"

        )

        return redirect(

            url_for(
                "admin_carousel.admin_carousels"
            )

        )

    parsed_starts_at = None

    parsed_expires_at = None

    if starts_at:

        parsed_starts_at = datetime.strptime(

            starts_at,

            "%Y-%m-%dT%H:%M"

        )

    if expires_at:

        parsed_expires_at = datetime.strptime(

            expires_at,

            "%Y-%m-%dT%H:%M"

        )

    upload_result = cloudinary.uploader.upload(

        carousel_banner,

        folder="rm_bakes/carousels"

    )

    banner_url = (

        upload_result["secure_url"]

    )

    carousel = Carousel(

        carousel_title=carousel_title,

        carousel_description=
            carousel_description,

        carousel_banner_image=
            banner_url,

        carousel_category=
            carousel_category,

        carousel_visibility=
            carousel_visibility,

        carousel_action_text=
            carousel_action_text,

        carousel_action_link=
            carousel_action_link,

        carousel_priority=
            carousel_priority,

        carousel_starts_at=
            parsed_starts_at,

        carousel_expires_at=
            parsed_expires_at

    )

    db.session.add(
        carousel
    )

    db.session.commit()

    flash(

        "Carousel created 🎠",

        "success"

    )

    return redirect(

        url_for(
            "admin_carousel.admin_carousels"
        )

    )

# =========================================
# UPDATE CAROUSEL
# =========================================

@admin_carousel_bp.route(

    "/admin/carousels/update/<int:carousel_id>",

    methods=["POST"]

)
@admin_required
def update_carousel(carousel_id):

    carousel = Carousel.query.get_or_404(
        carousel_id
    )

    new_banner = request.files.get(
        "carousel_banner"
    )

    starts_at = request.form.get(
        "carousel_starts_at"
    )

    expires_at = request.form.get(
        "carousel_expires_at"
    )

    parsed_starts_at = None

    parsed_expires_at = None

    if starts_at:

        parsed_starts_at = datetime.strptime(

            starts_at,

            "%Y-%m-%dT%H:%M"

        )

    if expires_at:

        parsed_expires_at = datetime.strptime(

            expires_at,

            "%Y-%m-%dT%H:%M"

        )

    carousel.carousel_title = request.form.get(
        "carousel_title"
    )

    carousel.carousel_description = request.form.get(
        "carousel_description"
    )

    carousel.carousel_category = request.form.get(
        "carousel_category"
    )

    carousel.carousel_visibility = request.form.get(
        "carousel_visibility"
    )

    carousel.carousel_action_text = request.form.get(
        "carousel_action_text"
    )

    carousel.carousel_action_link = request.form.get(
        "carousel_action_link"
    )

    carousel.carousel_priority = int(

        request.form.get(
            "carousel_priority",
            0
        )

    )

    carousel.carousel_starts_at = (
        parsed_starts_at
    )

    carousel.carousel_expires_at = (
        parsed_expires_at
    )

    if (

        new_banner

        and

        new_banner.filename

    ):

        upload_result = cloudinary.uploader.upload(

            new_banner,

            folder="rm_bakes/carousels"

        )

        carousel.carousel_banner_image = (

            upload_result["secure_url"]

        )

    db.session.commit()

    flash(

        "Carousel updated 🎠",

        "success"

    )

    return redirect(

        url_for(
            "admin_carousel.admin_carousels"
        )

    )

# =========================================
# TOGGLE CAROUSEL
# =========================================

@admin_carousel_bp.route(

    "/admin/carousels/toggle/<int:carousel_id>",

    methods=["POST"]

)
@admin_required
def toggle_carousel(carousel_id):

    carousel = Carousel.query.get_or_404(
        carousel_id
    )

    carousel.carousel_is_active = (

        not carousel.carousel_is_active

    )

    db.session.commit()

    if carousel.carousel_is_active:

        flash(

            "Carousel activated 🎉",

            "success"

        )

    else:

        flash(

            "Carousel deactivated 😴",

            "success"

        )

    return redirect(

        url_for(
            "admin_carousel.admin_carousels"
        )

    )

# =========================================
# DELETE CAROUSEL
# =========================================

@admin_carousel_bp.route(

    "/admin/carousels/delete/<int:carousel_id>",

    methods=["POST"]

)
@admin_required
def delete_carousel(carousel_id):

    carousel = Carousel.query.get_or_404(
        carousel_id
    )

    db.session.delete(
        carousel
    )

    db.session.commit()

    flash(

        "Carousel deleted 🗑️",

        "success"

    )

    return redirect(

        url_for(
            "admin_carousel.admin_carousels"
        )

    )
