from flask import (

    Blueprint,

    redirect,

    url_for,

    flash

)

from flask_login import (

    login_required,

    current_user

)

from datetime import datetime

from database import db

from custom_orders_database import CustomOrder

from utils.custom_order_validation_utils import (

    validate_custom_order_ownership,

    can_refresh_profile_snapshot

)

from utils.custom_order_profile_utils import (

    refresh_custom_order_profile_snapshot

)

from utils.custom_order_timeline_utils import (

    create_timeline_event

)

from utils.notification_utils import (

    create_user_notification,

    create_admin_notification

)



# =========================================
# BLUEPRINT
# =========================================

custom_order_profile_bp = Blueprint(

    "custom_order_profile",

    __name__

)



# =========================================
# REFRESH PROFILE SNAPSHOT
# =========================================

@custom_order_profile_bp.route(

    "/refresh-custom-order-profile/<int:custom_order_id>",

    methods=["POST"]

)

@login_required
def refresh_custom_order_profile(

    custom_order_id

):



    custom_order = CustomOrder.query.get_or_404(

        custom_order_id

    )



    # =====================================
    # OWNERSHIP VALIDATION
    # =====================================

    validate_custom_order_ownership(

        custom_order,

        current_user

    )



    # =====================================
    # STATUS VALIDATION
    # =====================================

    if not can_refresh_profile_snapshot(

        custom_order

    ):



        flash(

            (

                "Profile details can only be "
                "refreshed while request is "
                "pending or under review 😭"

            ),

            "warning"

        )



        return redirect(

            url_for(

                "custom_order.my_custom_orders"

            )

        )



    try:



        # =================================
        # REFRESH SNAPSHOT
        # =================================

        refresh_custom_order_profile_snapshot(

            custom_order,

            current_user

        )



        # =================================
        # UPDATE TIMESTAMP
        # =================================

        custom_order.updated_at = (

            datetime.utcnow()

        )



        db.session.commit()



        # =================================
        # TIMELINE
        # =================================

        create_timeline_event(

            custom_order_id=custom_order.custom_order_id,

            event_type="profile_refresh",

            title="Delivery Details Refreshed 🔄",

            description=(

                "Customer refreshed delivery "
                "profile snapshot."

            ),

            triggered_by="customer"

        )



        # =================================
        # USER NOTIFICATION
        # =================================

        create_user_notification(

            user_id=current_user.user_id,

            title="Delivery Details Updated 🔄",

            message=(

                "Your Dessert Studio delivery "
                "snapshot was refreshed."

            ),

            notification_type="info"

        )



        # =================================
        # ADMIN NOTIFICATION
        # =================================

        create_admin_notification(

            title="Dessert Delivery Snapshot Updated",

            message=(

                f"{custom_order.request_code} "
                f"delivery details were refreshed."

            ),

            notification_type="info"

        )



        flash(

            "Delivery details refreshed 😭🔥",

            "success"

        )



    except Exception as error:



        db.session.rollback()



        print(

            "PROFILE SNAPSHOT REFRESH ERROR:",

            error

        )



        flash(

            "Couldn't refresh delivery details 😭",

            "danger"

        )



    return redirect(

        url_for(

            "custom_order.my_custom_orders"

        )

    )