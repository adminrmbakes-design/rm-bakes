from flask import (

    Blueprint,

    request,

    redirect,

    url_for,

    flash,

    abort

)

from flask_login import (

    login_required,

    current_user

)

from datetime import datetime

from database import db

from custom_orders_database import CustomOrder

from utils.admin_guard import admin_required

from utils.custom_order_validation_utils import (

    validate_custom_order_ownership,

    validate_cancellation_request

)

from utils.custom_order_state_machine import (

    is_valid_custom_status_transition

)

from utils.custom_order_constants import (

    CUSTOM_STATUS_CANCEL_REQUESTED,

    CUSTOM_STATUS_CANCELLED,

    CUSTOM_STATUS_QUOTATION_ACCEPTED

)

from utils.notification_utils import (

    create_user_notification,

    create_admin_notification

)

from utils.custom_order_timeline_utils import (

    create_timeline_event

)



# =========================================
# BLUEPRINT
# =========================================

custom_order_cancellation_bp = Blueprint(

    "custom_order_cancellation",

    __name__

)



# =========================================
# REQUEST CANCELLATION
# =========================================

@custom_order_cancellation_bp.route(

    "/request-custom-order-cancellation/<int:custom_order_id>",

    methods=["POST"]

)

@login_required
def request_custom_order_cancellation(

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
    # VALIDATION
    # =====================================

    if not validate_cancellation_request(

        custom_order

    ):



        flash(

            (

                "Cancellation request is not "
                "allowed at this stage 😭"

            ),

            "danger"

        )



        return redirect(

            url_for(

                "custom_order.my_custom_orders"

            )

        )



    # =====================================
    # STATE MACHINE
    # =====================================

    if not is_valid_custom_status_transition(

        custom_order.custom_status,

        CUSTOM_STATUS_CANCEL_REQUESTED

    ):



        abort(403)



    cancel_reason = request.form.get(

        "cancel_reason"

    )



    # =====================================
    # UPDATE
    # =====================================

    custom_order.cancel_requested = True



    custom_order.cancel_reason = cancel_reason



    custom_order.cancel_requested_at = (

        datetime.utcnow()

    )



    custom_order.custom_status = (

        CUSTOM_STATUS_CANCEL_REQUESTED

    )



    try:



        db.session.commit()



        # =================================
        # TIMELINE
        # =================================

        create_timeline_event(

            custom_order_id=custom_order.custom_order_id,

            event_type="cancel_requested",

            title="Cancellation Requested ⚠️",

            description=(

                "Customer requested cancellation "
                "approval from RM Bakes."

            ),

            triggered_by="customer"

        )



        # =================================
        # USER NOTIFICATION
        # =================================

        create_user_notification(

            user_id=current_user.user_id,

            title="Cancellation Request Sent ⚠️",

            message=(

                "Your cancellation request was "
                "submitted to RM Bakes."

            ),

            notification_type="warning"

        )



        # =================================
        # ADMIN NOTIFICATION
        # =================================

        create_admin_notification(

            title="Cancellation Approval Required ⚠️",

            message=(

                f"{custom_order.request_code} "
                f"requested cancellation approval."

            ),

            notification_type="warning"

        )



        flash(

            (

                "Cancellation request submitted "
                "for admin approval 😭"

            ),

            "warning"

        )



    except Exception as error:



        db.session.rollback()



        print(

            "CUSTOM ORDER CANCEL REQUEST ERROR:",

            error

        )



        flash(

            "Couldn't request cancellation 😭",

            "danger"

        )



    return redirect(

        url_for(

            "custom_order.my_custom_orders"

        )

    )
    
    
    # =========================================
# APPROVE CANCELLATION
# =========================================

@custom_order_cancellation_bp.route(

    "/admin/approve-custom-cancellation/<int:custom_order_id>",

    methods=["POST"]

)

@admin_required
def approve_custom_cancellation(

    custom_order_id

):



    custom_order = CustomOrder.query.get_or_404(

        custom_order_id

    )



    # =====================================
    # STATE VALIDATION
    # =====================================

    if custom_order.custom_status != (

        CUSTOM_STATUS_CANCEL_REQUESTED

    ):



        abort(403)



    # =====================================
    # STATE MACHINE
    # =====================================

    if not is_valid_custom_status_transition(

        custom_order.custom_status,

        CUSTOM_STATUS_CANCELLED

    ):



        abort(403)



    # =====================================
    # UPDATE
    # =====================================

    custom_order.custom_status = (

        CUSTOM_STATUS_CANCELLED

    )



    custom_order.status = "cancelled"



    custom_order.cancel_reviewed_at = (

        datetime.utcnow()

    )



    custom_order.cancel_reviewed_by = (

        current_user.username

    )



    try:



        db.session.commit()



        # =================================
        # TIMELINE
        # =================================

        create_timeline_event(

            custom_order_id=custom_order.custom_order_id,

            event_type="cancel_approved",

            title="Dessert Request Cancelled 💔",

            description=(

                "RM Bakes approved the "
                "cancellation request."

            ),

            triggered_by="admin"

        )



        # =================================
        # USER NOTIFICATION
        # =================================

        create_user_notification(

            user_id=custom_order.user_id,

            title="Dessert Request Cancelled 💔",

            message=(

                "Your Dessert Studio request "
                "was cancelled successfully."

            ),

            notification_type="warning"

        )



        # =================================
        # ADMIN NOTIFICATION
        # =================================

        create_admin_notification(

            title="Cancellation Approved",

            message=(

                f"{custom_order.request_code} "
                f"was cancelled."

            ),

            notification_type="warning"

        )



        flash(

            "Cancellation approved 😭",

            "warning"

        )



    except Exception as error:



        db.session.rollback()



        print(

            "CANCEL APPROVAL ERROR:",

            error

        )



        flash(

            "Couldn't approve cancellation 😭",

            "danger"

        )



    return redirect(

        url_for(

            "custom_order.admin_custom_orders"

        )

    )



# =========================================
# REJECT CANCELLATION
# =========================================

@custom_order_cancellation_bp.route(

    "/admin/reject-custom-cancellation/<int:custom_order_id>",

    methods=["POST"]

)

@admin_required
def reject_custom_cancellation(

    custom_order_id

):



    custom_order = CustomOrder.query.get_or_404(

        custom_order_id

    )



    # =====================================
    # VALIDATION
    # =====================================

    if custom_order.custom_status != (

        CUSTOM_STATUS_CANCEL_REQUESTED

    ):



        abort(403)



    # =====================================
    # STATE MACHINE
    # =====================================

    if not is_valid_custom_status_transition(

        custom_order.custom_status,

        CUSTOM_STATUS_QUOTATION_ACCEPTED

    ):



        abort(403)



    rejection_reason = request.form.get(

        "rejection_reason"

    )



    # =====================================
    # RESTORE STATUS
    # =====================================

    custom_order.custom_status = (

        CUSTOM_STATUS_QUOTATION_ACCEPTED

    )



    custom_order.cancel_requested = False



    custom_order.cancel_reviewed_at = (

        datetime.utcnow()

    )



    custom_order.cancel_reviewed_by = (

        current_user.username

    )



    try:



        db.session.commit()



        # =================================
        # TIMELINE
        # =================================

        create_timeline_event(

            custom_order_id=custom_order.custom_order_id,

            event_type="cancel_rejected",

            title="Cancellation Rejected",

            description=(

                rejection_reason

                or

                "RM Bakes rejected the "
                "cancellation request."

            ),

            triggered_by="admin"

        )



        # =================================
        # USER NOTIFICATION
        # =================================

        create_user_notification(

            user_id=custom_order.user_id,

            title="Cancellation Rejected",

            message=(

                "Sorry, your dessert cannot "
                "be cancelled now. Please "
                "contact RM Bakes once again."

            ),

            notification_type="danger"

        )



        # =================================
        # ADMIN NOTIFICATION
        # =================================

        create_admin_notification(

            title="Cancellation Rejected",

            message=(

                f"{custom_order.request_code} "
                f"cancellation request rejected."

            ),

            notification_type="info"

        )



        flash(

            "Cancellation rejected.",

            "info"

        )



    except Exception as error:



        db.session.rollback()



        print(

            "CANCEL REJECTION ERROR:",

            error

        )



        flash(

            "Couldn't reject cancellation 😭",

            "danger"

        )



    return redirect(

        url_for(

            "custom_order.admin_custom_orders"

        )

    )