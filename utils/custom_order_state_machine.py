from utils.custom_order_constants import (

    CUSTOM_STATUS_PENDING,

    CUSTOM_STATUS_REVIEWING,

    CUSTOM_STATUS_QUOTED,

    CUSTOM_STATUS_QUOTATION_ACCEPTED,

    CUSTOM_STATUS_QUOTATION_REJECTED,

    CUSTOM_STATUS_CONVERTED,

    CUSTOM_STATUS_CANCEL_REQUESTED,

    CUSTOM_STATUS_CANCELLED

)



# =========================================
# VALID STATUS TRANSITIONS
# =========================================

VALID_CUSTOM_ORDER_TRANSITIONS = {



    # =====================================
    # INITIAL REQUEST
    # =====================================

    CUSTOM_STATUS_PENDING: [

        CUSTOM_STATUS_REVIEWING,

        CUSTOM_STATUS_CANCELLED

    ],



    # =====================================
    # ADMIN REVIEW
    # =====================================

    CUSTOM_STATUS_REVIEWING: [

        CUSTOM_STATUS_QUOTED,

        CUSTOM_STATUS_CANCELLED

    ],



    # =====================================
    # QUOTATION SENT
    # =====================================

    CUSTOM_STATUS_QUOTED: [

        CUSTOM_STATUS_QUOTATION_ACCEPTED,

        CUSTOM_STATUS_QUOTATION_REJECTED,

        CUSTOM_STATUS_CANCELLED

    ],



    # =====================================
    # CUSTOMER ACCEPTED QUOTATION
    # =====================================

    CUSTOM_STATUS_QUOTATION_ACCEPTED: [

        CUSTOM_STATUS_CONVERTED,

        CUSTOM_STATUS_CANCEL_REQUESTED

    ],



    # =====================================
    # CUSTOMER REJECTED QUOTATION
    # =====================================

    CUSTOM_STATUS_QUOTATION_REJECTED: [

        CUSTOM_STATUS_REVIEWING,

        CUSTOM_STATUS_CANCELLED

    ],



    # =====================================
    # CANCELLATION REQUESTED
    # =====================================

    CUSTOM_STATUS_CANCEL_REQUESTED: [

        CUSTOM_STATUS_CANCELLED,

        CUSTOM_STATUS_QUOTATION_ACCEPTED

    ],



    # =====================================
    # FINAL STATES
    # =====================================

    CUSTOM_STATUS_CONVERTED: [],

    CUSTOM_STATUS_CANCELLED: []

}



# =========================================
# VALIDATE TRANSITION
# =========================================

def is_valid_custom_status_transition(

    current_status,

    new_status

):



    allowed_transitions = (

        VALID_CUSTOM_ORDER_TRANSITIONS.get(

            current_status,

            []

        )

    )



    return new_status in allowed_transitions



# =========================================
# GET ALLOWED TRANSITIONS
# =========================================

def get_allowed_custom_status_transitions(

    current_status

):



    return VALID_CUSTOM_ORDER_TRANSITIONS.get(

        current_status,

        []

    )



# =========================================
# FINAL STATE CHECK
# =========================================

def is_final_custom_order_state(

    status

):



    final_states = [

        CUSTOM_STATUS_CONVERTED,

        CUSTOM_STATUS_CANCELLED

    ]



    return status in final_states



# =========================================
# CANCELLATION ALLOWED?
# =========================================

def can_request_cancellation(

    status

):



    allowed_statuses = [

        CUSTOM_STATUS_QUOTATION_ACCEPTED

    ]



    return status in allowed_statuses



# =========================================
# CONVERSION ALLOWED?
# =========================================

def can_convert_to_main_order(

    status

):



    allowed_statuses = [

        CUSTOM_STATUS_QUOTATION_ACCEPTED

    ]



    return status in allowed_statuses