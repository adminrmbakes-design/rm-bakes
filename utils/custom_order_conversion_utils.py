import json

from datetime import datetime

from database import db

from orders_database import Order

from utils.custom_order_constants import (

    ORDER_SOURCE_CUSTOM,

    CUSTOM_STATUS_CONVERTED,

    TIMELINE_EVENT_CONVERTED,

    TRIGGER_SYSTEM,

    PRODUCTION_STATUS_QUEUED

)

from utils.custom_order_validation_utils import (

    validate_conversion_to_main_order,

    has_complete_delivery_snapshot

)

from utils.custom_order_timeline_utils import (

    create_timeline_event

)

from utils.notification_utils import (

    create_admin_notification,

    create_user_notification

)



# =========================================
# BUILD PRODUCTS JSON
# =========================================

def build_custom_order_products_json(

    custom_order

):



    product_payload = [

        {

            "type": "custom_dessert",

            "request_code":

                custom_order.request_code,



            "dessert_category":

                custom_order.dessert_category,



            "flavor":

                custom_order.flavor,



            "quantity":

                custom_order.quantity,



            "occasion":

                custom_order.occasion,



            "quoted_price":

                custom_order.admin_price,



            "custom_message":

                custom_order.custom_message,



            "special_notes":

                custom_order.special_notes,



            "inspiration_image":

                custom_order.inspiration_image

        }

    ]



    return json.dumps(

        product_payload

    )



# =========================================
# CREATE MAIN ORDER
# =========================================

def create_main_order_from_custom_order(

    custom_order

):



    # =====================================
    # VALIDATION
    # =====================================

    if not validate_conversion_to_main_order(

        custom_order

    ):



        return {

            "success": False,

            "message":

                "Conversion validation failed."

        }



    # =====================================
    # DELIVERY VALIDATION
    # =====================================

    if not has_complete_delivery_snapshot(

        custom_order

    ):



        return {

            "success": False,

            "message":

                "Incomplete delivery details."

        }



    try:



        # =================================
        # CREATE MAIN ORDER
        # =================================

        main_order = Order(

            # =============================
            # USER
            # =============================

            user_id=custom_order.user_id,

            username=custom_order.username,

            email=custom_order.email,



            # =============================
            # CUSTOMER SNAPSHOT
            # =============================

            full_name=custom_order.full_name,

            phone_number=custom_order.phone_number,



            # =============================
            # DELIVERY SNAPSHOT
            # =============================

            delivery_address=

                custom_order.delivery_address,



            landmark=custom_order.landmark,

            city=custom_order.city,

            pincode=custom_order.pincode,



            google_maps_link=

                custom_order.google_maps_link,



            # =============================
            # PRODUCTS JSON
            # =============================

            products_json=(

                build_custom_order_products_json(

                    custom_order

                )

            ),



            # =============================
            # TOTALS
            # =============================

            subtotal=custom_order.admin_price,

            delivery_fee=0,

            grand_total=custom_order.admin_price,

            total_amount=custom_order.admin_price,



            # =============================
            # PAYMENT
            # =============================

            payment_method="Pending",

            payment_status="pending",



            # =============================
            # ORDER STATUS
            # =============================

            order_status=

                PRODUCTION_STATUS_QUEUED,



            # =============================
            # ORDER SOURCE
            # =============================

            order_source=

                ORDER_SOURCE_CUSTOM,



            converted_from_dessert_studio=True,



            # =============================
            # CUSTOM ORDER LINKAGE
            # =============================

            custom_order_id=(

                custom_order.custom_order_id

            ),



            custom_request_code=(

                custom_order.request_code

            ),



            # =============================
            # CUSTOM DESSERT DETAILS
            # =============================

            custom_dessert_category=(

                custom_order.dessert_category

            ),



            custom_flavor=(

                custom_order.flavor

            ),



            custom_quantity=(

                custom_order.quantity

            ),



            custom_description=(

                custom_order.description

            ),



            custom_message=(

                custom_order.custom_message

            ),



            custom_special_notes=(

                custom_order.special_notes

            ),



            custom_inspiration_image=(

                custom_order.inspiration_image

            ),



            # =============================
            # ORDER NUMBER
            # =============================

            order_number=(

                f"RM-DS-{custom_order.custom_order_id}"

            ),



            # =============================
            # TIMESTAMPS
            # =============================

            created_at=datetime.utcnow(),

            ordered_at=datetime.utcnow(),

            production_started_at=datetime.utcnow()

        )



        db.session.add(

            main_order

        )



        db.session.flush()



        # =================================
        # LINK CUSTOM ORDER
        # =================================

        custom_order.converted_to_main_order = True



        custom_order.converted_main_order_id = (

            main_order.order_id

        )



        custom_order.custom_status = (

            CUSTOM_STATUS_CONVERTED

        )



        custom_order.converted_at = (

            datetime.utcnow()

        )



        # =================================
        # TIMELINE
        # =================================

        create_timeline_event(

            custom_order_id=

                custom_order.custom_order_id,



            event_type=

                TIMELINE_EVENT_CONVERTED,



            title=

                "Converted To Production 🔥",



            description=(

                "Your dessert officially entered "
                "RM Bakes production workflow."

            ),



            triggered_by=TRIGGER_SYSTEM

        )



        # =================================
        # USER NOTIFICATION
        # =================================

        create_user_notification(

    user_id=custom_order.user_id,

    title="Dessert Entered Production 🔥",

    message=(

        "Your handcrafted dessert is now "
        "queued for production."

    ),

    notification_type="success",



    order_id=

        main_order.order_id,



    custom_order_id=

        custom_order.custom_order_id,



    notification_category=

        "custom_order"

)





        # =================================
        # ADMIN NOTIFICATION
        # =================================

        create_admin_notification(

            title="Dessert Converted To Production",

            message=(

                f"{custom_order.request_code} "
                f"entered production workflow."

            ),

            notification_type="info"

        )



        # =================================
        # FINAL COMMIT
        # =================================

        db.session.commit()



        return {

            "success": True,

            "main_order_id":

                main_order.order_id

        }



    except Exception as error:



        db.session.rollback()



        print(

            "CUSTOM ORDER CONVERSION ERROR:",

            error

        )



        return {

            "success": False,

            "message":

                str(error)

        }