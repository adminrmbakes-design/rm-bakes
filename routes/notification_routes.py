from flask import (

    Blueprint,
    render_template,
    redirect,
    url_for,
    jsonify

)

from flask_login import (

    login_required,
    current_user

)

from database import (

    db,
    UserNotification,
    GlobalNotification

)

from datetime import datetime

from orders_database import (
    Order,
    ProductReview
)

# =========================================
# BLUEPRINT
# =========================================

notification_bp = Blueprint(

    "notification",
    __name__

)



# =========================================
# NOTIFICATIONS PAGE
# =========================================

@notification_bp.route("/notifications")
def notifications_page():

    # =====================================
    # DEFAULT VALUES
    # =====================================

    user_notifications = []
    unread_notifications_count = 0

    # =====================================
    # AUTHENTICATED USER LOGIC
    # =====================================

    if current_user.is_authenticated:

        pending_orders = (
            Order.query.filter_by(
                user_id=current_user.user_id,
                review_reminder_sent=False,
                order_status="delivered"
            ).all()
        )

        for order in pending_orders:

            if (
                order.review_remind_at
                and
                datetime.utcnow() >= order.review_remind_at
            ):

                existing_notification = (
                    UserNotification.query.filter_by(
                        user_id=current_user.user_id,
                        order_id=order.order_id,
                        notification_category="review_reminder"
                    ).first()
                )

                if not existing_notification:

                    reminder = UserNotification(
                        user_id=current_user.user_id,
                        title="💌 How was your sweet experience?",
                        message=(
                            "Your desserts were delivered. "
                            "We'd love to hear your thoughts 🌸"
                        ),
                        notification_type="review",
                        order_id=order.order_id,
                        notification_category="review_reminder"
                    )

                    db.session.add(reminder)

                order.review_reminder_sent = True

        db.session.commit()

        user_notifications = (
            UserNotification.query.filter_by(
                user_id=current_user.user_id,
                is_cleared=False
            )
            .order_by(
                UserNotification.created_at.desc()
            )
            .all()
        )

        for notification in user_notifications:

            notification.has_review = False

            if notification.order_id:

                review = (
                    ProductReview.query.filter_by(
                        order_id=notification.order_id,
                        customer_id=current_user.user_id
                    ).first()
                )

                notification.has_review = (
                    review is not None
                )

        unread_notifications = (
            UserNotification.query.filter_by(
                user_id=current_user.user_id,
                is_read=False,
                is_cleared=False
            ).all()
        )

        for notification in unread_notifications:
            notification.is_read = True

        db.session.commit()

        unread_notifications_count = (
            UserNotification.query.filter_by(
                user_id=current_user.user_id,
                is_read=False,
                is_cleared=False
            ).count()
        )

    # =====================================
    # GLOBAL NOTIFICATIONS
    # =====================================

    global_notifications = (
        GlobalNotification.query
        .filter(
            GlobalNotification.is_active == True,
            (
                (GlobalNotification.expires_at == None)
                |
                (GlobalNotification.expires_at > datetime.utcnow())
            )
        )
        .order_by(
            GlobalNotification.is_featured.desc(),
            GlobalNotification.priority.desc(),
            GlobalNotification.created_at.desc()
        )
        .all()
    )

    for notification in global_notifications:
        
        notification.product_name = None
        
        if notification.product_id:
            
            product = Product.query.get(
                notification.product_id
            )
            
            if product:
                
                notification.product_name = (
                    product.product_name
                )

    return render_template(
        "notifications.html",
        user_notifications=user_notifications,
        global_notifications=global_notifications,
        unread_notifications_count=unread_notifications_count
    )
# =========================================
# CLEAR USER NOTIFICATIONS
# =========================================

@notification_bp.route(

    "/clear-user-notifications",

    methods=["POST"]

)
@login_required
def clear_user_notifications():

    notifications = (

        UserNotification.query.filter_by(

            user_id=current_user.user_id,

            is_cleared=False

        ).all()

    )



    for notification in notifications:

        notification.is_cleared = True



    db.session.commit()



    return jsonify({

        "success": True,

        "message":
        "Notifications cleared successfully 😭"

    })



# =========================================
# UNREAD NOTIFICATION COUNT
# =========================================

@notification_bp.route("/notifications-count")
@login_required
def notifications_count():

    unread_count = (

        UserNotification.query.filter_by(

            user_id=current_user.user_id,

            is_read=False,

            is_cleared=False

        ).count()

    )



    return jsonify({

        "success": True,

        "unread_count":
        unread_count

    })



# =========================================
# MARK ALL NOTIFICATIONS AS READ
# =========================================

@notification_bp.route(

    "/mark-all-notifications-read",

    methods=["POST"]

)
@login_required
def mark_all_notifications_read():

    unread_notifications = (

        UserNotification.query.filter_by(

            user_id=current_user.user_id,

            is_read=False,

            is_cleared=False

        ).all()

    )



    for notification in unread_notifications:

        notification.is_read = True



    db.session.commit()



    return jsonify({

        "success": True,

        "message":
        "Notifications marked as read ✨"

    })
