from datetime import datetime

from database import db

from utils.custom_order_validation_utils import (

    is_profile_complete,

    get_missing_profile_fields

)



# =========================================
# BUILD PROFILE SNAPSHOT
# =========================================

def build_profile_snapshot(

    user

):



    return {

        "full_name": user.full_name,

        "phone_number": user.phone_number,

        "delivery_address": user.delivery_address,

        "landmark": user.landmark,

        "city": user.city,

        "pincode": user.pincode,

        "google_maps_link": user.google_maps_link

    }



# =========================================
# APPLY PROFILE SNAPSHOT
# =========================================

def apply_profile_snapshot_to_custom_order(

    custom_order,

    user

):



    snapshot = build_profile_snapshot(

        user

    )



    custom_order.full_name = (

        snapshot["full_name"]

    )



    custom_order.phone_number = (

        snapshot["phone_number"]

    )



    custom_order.delivery_address = (

        snapshot["delivery_address"]

    )



    custom_order.landmark = (

        snapshot["landmark"]

    )



    custom_order.city = (

        snapshot["city"]

    )



    custom_order.pincode = (

        snapshot["pincode"]

    )



    custom_order.google_maps_link = (

        snapshot["google_maps_link"]

    )



    custom_order.profile_snapshot_updated_at = (

        datetime.utcnow()

    )



    return custom_order



# =========================================
# VALIDATE PROFILE BEFORE SUBMISSION
# =========================================

def validate_profile_before_custom_order(

    user

):



    if not is_profile_complete(

        user

    ):



        return {

            "success": False,

            "missing_fields":

                get_missing_profile_fields(

                    user

                )

        }



    return {

        "success": True,

        "missing_fields": []

    }



# =========================================
# REFRESH PROFILE SNAPSHOT
# =========================================

def refresh_custom_order_profile_snapshot(

    custom_order,

    user

):



    apply_profile_snapshot_to_custom_order(

        custom_order,

        user

    )



    db.session.commit()



    return True



# =========================================
# DELIVERY SNAPSHOT STATUS
# =========================================

def get_delivery_snapshot_status(

    custom_order

):



    required_fields = [

        custom_order.full_name,

        custom_order.phone_number,

        custom_order.delivery_address,

        custom_order.city,

        custom_order.pincode

    ]



    if all(required_fields):



        return {

            "complete": True,

            "message":

                "Delivery details complete"

        }



    return {

        "complete": False,

        "message":

            "Missing delivery details"

    }



# =========================================
# PROFILE SNAPSHOT AGE
# =========================================

def get_profile_snapshot_age(

    custom_order

):



    if not custom_order.profile_snapshot_updated_at:

        return None



    now = datetime.utcnow()



    difference = (

        now

        -

        custom_order.profile_snapshot_updated_at

    )



    return difference.days