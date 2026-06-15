from flask import (

    Blueprint,
    render_template

)

from flask_login import (

    current_user

)

from database import (

    get_featured_products,
    get_active_carousels,
    UserNotification

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
    # RENDER HOME PAGE
    # =====================================

    return render_template(

        "index.html",

        featured_products=featured_products,

        active_carousels=active_carousels,

        unread_notifications_count=
            unread_notifications_count

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
