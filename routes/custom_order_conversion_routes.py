from flask import (

    Blueprint,

    redirect,

    url_for,

    flash,

    abort

)

from flask_login import current_user

from datetime import datetime

from database import db

from custom_orders_database import CustomOrder


from utils.admin_guard import admin_required

from utils.custom_order_conversion_utils import (

    create_main_order_from_custom_order

)

from utils.custom_order_state_machine import (

    is_valid_custom_status_transition

)

from utils.custom_order_constants import (

    CUSTOM_STATUS_QUOTATION_ACCEPTED,

    CUSTOM_STATUS_CONVERTED

)



# =========================================
# BLUEPRINT
# =========================================

custom_order_conversion_bp = Blueprint(

    "custom_order_conversion",

    __name__

)



# =========================================
# CONVERT TO PRODUCTION ORDER
# =========================================

@custom_order_conversion_bp.route(

    "/admin/convert-custom-order/<int:custom_order_id>",

    methods=["POST"]

)

@admin_required
def convert_custom_order(

    custom_order_id

):



    custom_order = CustomOrder.query.get_or_404(

        custom_order_id

    )



    # =====================================
    # STATUS VALIDATION
    # =====================================

    if custom_order.custom_status != (

        CUSTOM_STATUS_QUOTATION_ACCEPTED

    ):



        abort(403)



    # =====================================
    # DUPLICATE PROTECTION
    # =====================================

    if custom_order.converted_main_order_id:



        flash(

            "Dessert request already converted.",

            "warning"

        )



        return redirect(

            url_for(

                "custom_order.admin_custom_orders"

            )

        )



    # =====================================
    # STATE MACHINE VALIDATION
    # =====================================

    if not is_valid_custom_status_transition(

        custom_order.custom_status,

        CUSTOM_STATUS_CONVERTED
        
    ):



        abort(403)



    try:



        # =================================
        # CONVERT TO MAIN ORDER
        # =================================

        conversion_result = (

            create_main_order_from_custom_order(

                custom_order

            )

        )



        if not conversion_result["success"]:



            flash(

                conversion_result["message"],

                "danger"

            )



            return redirect(

                url_for(

                    "custom_order.admin_custom_orders"

                )

            )
            
            flash(

            "Dessert request converted successfully 😭🔥",

            "success"

        )



    except Exception as error:



        db.session.rollback()



        print(

            "CUSTOM ORDER CONVERSION ERROR:",

            error

        )



        flash(

            "Couldn't convert dessert request 😭",

            "danger"

        )



    return redirect(

        url_for(

            "custom_order.admin_custom_orders"

        )

    )
        
    