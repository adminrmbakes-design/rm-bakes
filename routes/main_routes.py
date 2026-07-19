from flask import (

    Blueprint,
    render_template

)

from flask_login import (

    current_user

)

from utils.timezone_utils import to_ist

from database import (

    get_featured_products,
    get_active_carousels,
    UserNotification,
    Product

)



# =========================================
# BLUEPRINT
# =========================================

main_bp = Blueprint(

    "main",
    __name__

)



# =========================================
# HOME PAGE
# =========================================

@main_bp.route("/")
def home():

    # =====================================
    # FEATURED PRODUCTS AND CAROUSEL
    # =====================================

    featured_products = get_featured_products()

    active_carousels = get_active_carousels()

    launching_products = (

        Product.query

        .filter_by(
            product_is_launching=True
        )

        .all()

    )



    # =====================================
    # UNREAD NOTIFICATIONS COUNT
    # =====================================

    unread_notifications_count = 0



    if current_user.is_authenticated:

        unread_notifications_count = (

            UserNotification.query.filter_by(

                user_id=current_user.user_id,

                is_read=False,

                is_cleared=False

            ).count()

        )



    # =====================================
    # MY STANDALONE REVIEW (Leave a Review box)
    # =====================================

    my_general_review = None

    if current_user.is_authenticated:

        from orders_database import ProductReview

        my_general_review = ProductReview.query.filter_by(

            customer_id=current_user.user_id,

            product_name="Overall Experience",

            order_id=None

        ).first()



    # =====================================
    # RENDER HOME PAGE
    # =====================================

    return render_template(

        "index.html",

        featured_products=featured_products,

        active_carousels=active_carousels,

        launching_products=launching_products,

        unread_notifications_count=
            unread_notifications_count,

        my_general_review=my_general_review

    )



# =====================================
# ABOUT PAGE
# =====================================

@main_bp.route("/about")
def about():

    unread_notifications_count = 0



    if current_user.is_authenticated:

        unread_notifications_count = (

            UserNotification.query.filter_by(

                user_id=current_user.user_id,

                is_read=False,

                is_cleared=False

            ).count()

        )



    return render_template(

        "about.html",

        unread_notifications_count=
            unread_notifications_count

    )


# =====================================
# CONTACT PAGE
# =====================================

@main_bp.route("/contact")
def contact():

    unread_notifications_count = 0

    if current_user.is_authenticated:

        unread_notifications_count = (

            UserNotification.query.filter_by(

                user_id=current_user.user_id,

                is_read=False,

                is_cleared=False

            ).count()

        )

    return render_template(

        "contact.html",

        unread_notifications_count=
            unread_notifications_count

    )


# =====================================
# API: HOMEPAGE REVIEWS (for testimonials carousel)
# =====================================

@main_bp.route("/homepage-reviews-data")
def homepage_reviews_api():

    from orders_database import ProductReview  # FIX: correct module
    from flask import jsonify

    # FIX: Only show "Overall Experience" reviews on homepage (not product-specific)
    reviews = (
        ProductReview.query
        .filter(
            ProductReview.product_name.in_(["Overall Experience", "Overall"]),
            ProductReview.is_visible == True
        )
        .order_by(ProductReview.created_at.desc())
        .limit(30)
        .all()
    )

    return jsonify([
        {
            "review_id":     r.review_id,
            "customer_name": r.customer_name,
            "rating":        r.rating,
            "review_text":   r.review_text if r.review_text else None,
            "date":          to_ist(r.created_at).strftime("%d %b"),
            "is_own": bool(
                current_user.is_authenticated
                and r.customer_id == current_user.user_id
            ),
            "has_reply": bool(r.admin_reply),
        }
        for r in reviews
    ])
