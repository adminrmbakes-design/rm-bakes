from database import (

    db,

    AdminNotification,

    UserNotification,

    GlobalNotification

)



# =========================================
# ADMIN NOTIFICATIONS
# =========================================

def create_admin_notification(

    title,

    message,

    notification_type="info"

):



    notification = AdminNotification(

        title=title,

        message=message,

        notification_type=notification_type

    )



    db.session.add(

        notification

    )



    db.session.commit()



    return notification



# =========================================
# USER NOTIFICATIONS
# =========================================

def create_user_notification(

    user_id,

    title,

    message,

    notification_type="info",

    order_id=None,

    custom_order_id=None,

    notification_category="order"

):



    notification = UserNotification(

        user_id=user_id,

        title=title,

        message=message,

        notification_type=notification_type,



        # =================================
        # ORDER LINKING
        # =================================

        order_id=order_id,

        custom_order_id=custom_order_id,

        notification_category=

            notification_category

    )



    db.session.add(

        notification

    )



    db.session.commit()



    return notification



# =========================================
# GLOBAL NOTIFICATIONS
# =========================================

def create_global_notification(

    title,

    message,

    banner_image,

    is_active=True

):



    notification = GlobalNotification(

        title=title,

        message=message,

        banner_image=banner_image,

        is_active=is_active

    )



    db.session.add(

        notification

    )



    db.session.commit()



    return notification