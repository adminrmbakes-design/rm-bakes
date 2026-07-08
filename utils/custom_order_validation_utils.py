from flask import abort

from utils.custom_order_constants import (

    REQUIRED_PROFILE_FIELDS,

    CUSTOM_STATUS_PENDING,

    CUSTOM_STATUS_REVIEWING,

    CUSTOM_STATUS_QUOTED,

    CUSTOM_STATUS_QUOTATION_ACCEPTED,

    CUSTOM_STATUS_CONVERSION_PENDING,

    CUSTOM_STATUS_CANCEL_REQUESTED

)

from utils.custom_order_state_machine import (

    can_convert_to_main_order,

    can_request_cancellation

)



# =========================================
# OWNERSHIP VALIDATION
# =========================================

def validate_custom_order_ownership(

    custom_order,

    current_user

):



    if (

        custom_order.user_id

        !=

        current_user.user_id

    ):

        abort(403)



    return True



# =========================================
# PROFILE COMPLETENESS
# =========================================

def is_profile_complete(

    user

):



    for field in REQUIRED_PROFILE_FIELDS:



        value = getattr(

            user,

            field,

            None

        )



        if not value:

            return False



    return True



# =========================================
# MISSING PROFILE FIELDS
# =========================================

def get_missing_profile_fields(

    user

):



    missing_fields = []



    for field in REQUIRED_PROFILE_FIELDS:



        value = getattr(

            user,

            field,

            None

        )



        if not value:

            missing_fields.append(

                field

            )



    return missing_fields



# =========================================
# PROFILE REFRESH ALLOWED?
# =========================================

def can_refresh_profile_snapshot(

    custom_order

):



    allowed_statuses = [

        CUSTOM_STATUS_PENDING,

        CUSTOM_STATUS_REVIEWING

    ]



    return (

        custom_order.custom_status

        in

        allowed_statuses

    )



# =========================================
# ACCEPT QUOTE ALLOWED?
# =========================================

def can_accept_quote(

    custom_order

):



    return (

        custom_order.custom_status

        ==

        CUSTOM_STATUS_QUOTED

    )



# =========================================
# REJECT QUOTE ALLOWED?
# =========================================

def can_reject_quote(

    custom_order

):



    return (

        custom_order.custom_status

        ==

        CUSTOM_STATUS_QUOTED

    )



# =========================================
# CANCELLATION REQUEST ALLOWED?
# =========================================

def validate_cancellation_request(

    custom_order

):



    return can_request_cancellation(

        custom_order.custom_status

    )



# =========================================
# CONVERSION VALIDATION
# =========================================

def validate_conversion_to_main_order(

    custom_order

):



    # =====================================
    # STATUS CHECK
    # =====================================

    if not can_convert_to_main_order(

        custom_order.custom_status

    ):

        return False



    # =====================================
    # DUPLICATE CONVERSION CHECK
    # =====================================

    if custom_order.converted_to_main_order:

        return False



    return True



# =========================================
# DELIVERY DETAILS CHECK
# =========================================

def has_complete_delivery_snapshot(

    custom_order

):



    required_fields = [

        custom_order.full_name,

        custom_order.phone_number,

        custom_order.delivery_address,

        custom_order.city,

        custom_order.pincode

    ]



    return all(required_fields)



# =========================================
# DELIVERY READY?
# =========================================

def is_delivery_ready(

    custom_order

):



    if not has_complete_delivery_snapshot(

        custom_order

    ):

        return False



    if (

        custom_order.custom_status

        not in [

            CUSTOM_STATUS_QUOTATION_ACCEPTED,

            CUSTOM_STATUS_CONVERSION_PENDING

        ]

    ):

        return False



    return True



# =========================================
# ADMIN STATUS UPDATE VALIDATION
# =========================================

def validate_admin_status_update(

    current_status,

    new_status,

    transition_validator

):



    return transition_validator(

        current_status,

        new_status

    )



# =========================================
# FINAL STATE CHECK
# =========================================

def is_locked_custom_order(

    custom_order

):



    locked_states = [

        CUSTOM_STATUS_CANCEL_REQUESTED

    ]



    return (

        custom_order.custom_status

        in

        locked_states

    )