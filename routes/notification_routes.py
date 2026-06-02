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
@login_required
def notifications_page():

    # =====================================
    # USER NOTIFICATIONS
    # =====================================

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



    # =====================================
    # MARK USER NOTIFICATIONS AS READ
    # =====================================

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



    # =====================================
    # GLOBAL NOTIFICATIONS
    # =====================================

    global_notifications = (

        GlobalNotification.query.filter_by(

            is_active=True

        )

        .order_by(

            GlobalNotification.created_at.desc()

        )

        .all()

    )



    # =====================================
    # UNREAD COUNT
    # =====================================

    unread_notifications_count = (

        UserNotification.query.filter_by(

            user_id=current_user.user_id,

            is_read=False,

            is_cleared=False

        ).count()

    )



    # =====================================
    # RENDER PAGE
    # =====================================

    return render_template(

        "notifications.html",

        user_notifications=user_notifications,

        global_notifications=global_notifications,

        unread_notifications_count=
            unread_notifications_count

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