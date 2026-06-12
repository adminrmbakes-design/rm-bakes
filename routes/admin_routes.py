from flask import (

    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash

)
import os

from werkzeug.utils import secure_filename

from database import GlobalNotification
from datetime import (

    datetime,
    timedelta

)

from werkzeug.security import (

    check_password_hash

)

from database import (

    db,
    User,
    AdminNotification
)

from database import (
    User,
    UserNotification
)

from utils.admin_guard import (

    admin_required

)

from utils.email_sender import (

    send_email

)

from utils.otp_generator import (

    generate_otp,
    generate_otp_expiry,
    is_otp_expired

)

from utils.notification_utils import (

    create_admin_notification,
    create_user_notification,
    create_global_notification

)

from orders_database import (

    Order,
    ProductReview,
    OrderFeedback

)

from custom_orders_database import (
    CustomOrder
)

from database import Product

import json
import cloudinary.uploader
import cloudinary_config


# =========================================
# BLUEPRINT
# =========================================

admin_bp = Blueprint(

    "admin",
    __name__

)



# =========================================
# TEST NOTIFICATION
# =========================================

@admin_bp.route("/test-notification")
def test_notification():

    create_admin_notification(

        title="Test Notification",

        message="RM Bakes notification system online 😭🔥",

        notification_type="success"

    )

    return "Notification Created"



# =========================================
# ADMIN LOGIN
# =========================================

@admin_bp.route(

    "/admin/login",

    methods=["GET", "POST"]

)
def admin_login():

    if request.method == "POST":

        username = request.form.get(
            "username"
        )

        password = request.form.get(
            "password"
        )

        admin_time = request.form.get(
            "admin_time"
        )



        valid_times = [

            "1",
            "5",
            "10",
            "15",
            "30",
            "45",
            "60"

        ]



        if admin_time not in valid_times:

            flash(

                "Invalid admin time selected",

                "danger"

            )

            return redirect(

                url_for(
                    "admin.admin_login"
                )

            )



        admin_user = User.query.filter_by(

            username=username,
            is_admin=True

        ).first()



        if not admin_user:

            create_admin_notification(

                title="Failed Admin Login",

                message=f"""

Unknown admin username attempt:

{username}

""",

                notification_type="security"

            )

            flash(

                "Admin account not found",

                "danger"

            )

            return redirect(

                url_for(
                    "admin.admin_login"
                )

            )



        password_correct = check_password_hash(

            admin_user.password,
            password

        )



        if not password_correct:

            create_admin_notification(

                title="Failed Admin Login",

                message=f"""

Failed login attempt for:

{username}

Reason:
Incorrect password

""",

                notification_type="security"

            )

            flash(

                "Incorrect password",

                "danger"

            )

            return redirect(

                url_for(
                    "admin.admin_login"
                )

            )



        session[
            "pending_admin_id"
        ] = admin_user.user_id



        session[
            "pending_admin_time"
        ] = int(admin_time)



        generated_otp = generate_otp()

        otp_expiry = generate_otp_expiry(5)



        session[
            "temp_admin_otp"
        ] = generated_otp



        session[
            "temp_admin_otp_expiry"
        ] = otp_expiry.isoformat()



        email_sent = send_email(

            receiver_email="admin.rmbakes@gmail.com",

            subject="RM Bakes Admin OTP Verification",

            body=f"""

RM Bakes Administrative Security

Your OTP is:

{generated_otp}

This OTP expires in 5 minutes.

"""

        )



        if not email_sent:

            flash(

                "Failed to send OTP email",

                "danger"

            )

            return redirect(

                url_for(
                    "admin.admin_login"
                )

            )



        flash(

            "OTP sent successfully 📩",

            "success"

        )



        return redirect(

            url_for(
                "admin.verify_admin_otp"
            )

        )



    return render_template(

        "admin/admin_login.html"

    )



# =========================================
# VERIFY OTP
# =========================================

@admin_bp.route(

    "/admin/verify-otp",

    methods=["GET", "POST"]

)
def verify_admin_otp():

    pending_admin_id = session.get(

        "pending_admin_id"

    )



    if not pending_admin_id:

        return redirect(

            url_for(
                "admin.admin_login"
            )

        )



    if request.method == "POST":

        entered_otp = request.form.get(
            "otp"
        )



        stored_otp = session.get(
            "temp_admin_otp"
        )



        stored_expiry = session.get(
            "temp_admin_otp_expiry"
        )



        if stored_expiry:

            expiry_datetime = datetime.fromisoformat(

                stored_expiry

            )



            if is_otp_expired(

                expiry_datetime

            ):

                flash(

                    "OTP expired",

                    "danger"

                )

                session.clear()

                return redirect(

                    url_for(
                        "admin.admin_login"
                    )

                )



        if entered_otp != stored_otp:

            create_admin_notification(

                title="Invalid OTP Attempt",

                message=f"""

Administrator:
{session.get('admin_username')}

entered incorrect OTP.

""",

                notification_type="security"

            )

            flash(

                "Invalid OTP",

                "danger"

            )

            return redirect(

                url_for(
                    "admin.verify_admin_otp"
                )

            )



        admin_user = User.query.get(

            pending_admin_id

        )



        if not admin_user:

            session.clear()

            return redirect(

                url_for(
                    "admin.admin_login"
                )

            )



        admin_minutes = session.get(

            "pending_admin_time",
            15

        )



        expiry_time = datetime.utcnow() + timedelta(

            minutes=admin_minutes

        )



        session.pop(
            "pending_admin_id",
            None
        )



        session.pop(
            "pending_admin_time",
            None
        )



        session.pop(
            "temp_admin_otp",
            None
        )



        session.pop(
            "temp_admin_otp_expiry",
            None
        )



        session[
            "admin_verified"
        ] = True



        session[
            "admin_id"
        ] = admin_user.user_id



        session[
            "admin_username"
        ] = admin_user.username



        session[
            "admin_role"
        ] = admin_user.admin_role



        session[
            "admin_expiry"
        ] = expiry_time.isoformat()



        session[
            "admin_minutes"
        ] = admin_minutes



        admin_user.admin_last_login = datetime.utcnow()

        db.session.commit()



        create_admin_notification(

            title="Admin Login",

            message=f"""

Administrator:
{admin_user.username}

successfully logged into
RM Bakes Control Center.

""",

            notification_type="admin_login"

        )



        flash(

            "Admin verified successfully 🔥",

            "success"

        )



        return redirect(

            url_for(
                "admin.admin_dashboard"
            )

        )



    return render_template(

        "admin/admin_verify_otp.html"

    )



# =========================================
# ADMIN DASHBOARD
# =========================================

@admin_bp.route(

    "/admin/dashboard"

)
@admin_required
def admin_dashboard():

    expiry_time = session.get(
        "admin_expiry"
    )



    return render_template(

        "admin/admin_dashboard.html",

        expiry_time=expiry_time,

        admin_username=session.get(
            "admin_username"
        ),

        admin_role=session.get(
            "admin_role"
        ),

        admin_minutes=session.get(
            "admin_minutes"
        )

    )



# =========================================
# ADMIN ORDERS
# =========================================

@admin_bp.route(
    "/admin/orders"
)
@admin_required
def admin_orders():

    status_filter = request.args.get(
        "status",
        "all"
    )

    # =================================
    # LOAD ALL ORDERS
    # =================================

    orders = Order.query.order_by(
        Order.created_at.desc()
    ).all()

    # =================================
    # FILTERS
    # =================================

    if status_filter == "all":

        filtered_orders = orders


    elif status_filter == "custom":

        filtered_orders = [

            order for order in orders

            if getattr(
                order,
                "is_custom_order",
                False
            )

        ]


    else:

        filtered_orders = [

            order for order in orders

            if getattr(
                order,
                "order_status",
                ""
            ) == status_filter

        ]

    # =================================
    # PRODUCTS DATA
    # =================================

    for order in filtered_orders:

        try:

            order.products_data = json.loads(
                order.products_json
            )

        except:

            order.products_data = []

    # =================================
    # RENDER
    # =================================

    return render_template(

        "admin/admin_orders.html",

        orders=filtered_orders,

        status_filter=status_filter,

        admin_username=session.get(
            "admin_username"
        ),

        admin_role=session.get(
            "admin_role"
        )

    )


# =========================================
# UPDATE ORDER STATUS
# =========================================

@admin_bp.route(

    "/admin/update-order-status/<int:order_id>",

    methods=["POST"]

)
@admin_required
def update_order_status(order_id):

    order = Order.query.get_or_404(

        order_id

    )



    new_status = request.form.get(
        "new_status"
    )



    valid_statuses = [

        "queued",
        "approved",
        "preparing",
        "baking",
        "packed",
        "out_for_delivery",
        "delivered",
        "cancelled"

    ]



    if new_status not in valid_statuses:

        flash(

            "Invalid status",

            "danger"

        )

        return redirect(

            url_for(
                "admin.admin_orders"
            )

        )



    current_status = order.order_status



    allowed_transitions = {

        "queued": [
            "approved",
            "cancelled"
        ],

        "approved": [
            "preparing",
            "cancelled"
        ],

        "preparing": [
            "baking"
        ],

        "baking": [
            "packed"
        ],

        "packed": [
            "out_for_delivery"
        ],

        "out_for_delivery": [
            "delivered"
        ],

        "delivered": [],

        "cancelled": []

    }



    if new_status not in allowed_transitions.get(

        current_status,
        []

    ):

        flash(

            f"Cannot change status from {current_status} to {new_status}",

            "danger"

        )

        return redirect(

            url_for(
                "admin.admin_orders"
            )

        )



    previous_status = order.order_status

    order.order_status = new_status

    db.session.commit()



    # =================================
    # ADMIN NOTIFICATION
    # =================================

    create_admin_notification(

        title="Order Status Updated",

        message=f"""

Order:
{order.order_number}

Changed From:
{previous_status.upper()}

To:
{new_status.upper()}

""",

        notification_type="status_update"

    )



    # =================================
    # EMOTIONAL USER NOTIFICATIONS
    # =================================

    status_messages = {

        "approved":
            "🎉 Your order has been approved by RM Bakes.",

        "preparing":
            "👨‍🍳 Our chefs have started preparing your order.",

        "baking":
            "🍰 Your cake is now baking with love.",

        "packed":
            "📦 Your order has been packed carefully.",

        "out_for_delivery":
            "🚚 Your order is out for delivery.",

        "delivered":
            "✅ Your order was delivered successfully.",

        "cancelled":
            "❌ Your order has been cancelled."

    }



    create_user_notification(

    user_id=order.user_id,

    title=f"Order {new_status.replace('_',' ').title()}",

    message=f"""

Order:
{order.order_number}

{status_messages.get(new_status)}

""",

    notification_type="order",



    order_id=

        order.order_id,



    notification_category=

        "order"

)







    flash(

        f"Order #{order.order_id} updated to {new_status}",

        "success"

    )


    # =================================
    # REVIEW NOTIFICATION
    # =================================
    
    if (

        new_status == "delivered"

    ):

        create_user_notification(

            user_id=order.user_id,

            title="💌 How was your sweet experience?",

            message=(

                "Your desserts were delivered successfully. "

                "We'd love to hear your sweet story 🌸"

            ),

            notification_type="review",

            order_id=order.order_id,

            notification_category="delivered_review"

        )



    return redirect(

        url_for(

            "admin.admin_orders",

            status=request.args.get(
                "status",
                "all"
            )

        )

    )



# =========================================
# ADMIN NOTIFICATIONS
# =========================================

@admin_bp.route(

    "/admin/notifications"

)
@admin_required
def admin_notifications():

    notifications = (

        AdminNotification.query

        .order_by(

            AdminNotification.created_at.desc()

        )

        .all()

    )



    return render_template(

        "admin/admin_notifications.html",

        notifications=notifications,

        admin_username=session.get(
            "admin_username"
        ),

        admin_role=session.get(
            "admin_role"
        )

    )


# =========================================
# GLOBAL NOTIFICATIONS MANAGEMENT
# =========================================

@admin_bp.route(

    "/admin/global-notifications",

    methods=["GET", "POST"]

)
@admin_required
def admin_global_notifications():

    # =====================================
    # CREATE ANNOUNCEMENT
    # =====================================

    if request.method == "POST":

        title = request.form.get(
            "title"
        )



        message = request.form.get(
            "message"
        )



        banner = request.files.get(
            "banner"
        )

        notification_type = request.form.get(
            "notification_type",
            "announcement"
        )
        
        action_text = request.form.get(
            "action_text"
        )
        
        action_link = request.form.get(
            "action_link"
        )
        
        coupon_code = request.form.get(
            "coupon_code"
        )
        
        product_id = request.form.get(
            "product_id"
        )
        
        priority = int(
            
            request.form.get(
                "priority",0
            )
        )
        
        is_featured = (

            request.form.get(
                "is_featured"
            )
            == "on"
        )
        
        starts_at = request.form.get(
            "starts_at"
        )

        expires_at = request.form.get(
            "expires_at"
        )

        if product_id:
            
            product_id = int(
                product_id
            )
            
        else:
            
            product_id = None

        if starts_at:
            
            starts_at = datetime.fromisoformat(
                starts_at
        )
            
        else:
            
            starts_at = None
            
        if expires_at:
            
            expires_at = datetime.fromisoformat(
                expires_at
            )
        
        else:
            expires_at = None

        
        
        if not title or not message or not banner:

            flash(

                "All fields are required",

                "danger"

            )

            return redirect(

                url_for(
                    "admin.admin_global_notifications"
                )

            )



        # =================================
        # SAVE IMAGE
        # =================================

        upload_folder = os.path.join(

            "static",
            "uploads",
            "notifications"

        )



        os.makedirs(

            upload_folder,

            exist_ok=True

        )



        upload_result = cloudinary.uploader.upload(

              banner,
              folder="rm_bakes/notifications"

        )

        banner_url = (

              upload_result["secure_url"]

        )




        # =================================
        # CREATE GLOBAL NOTIFICATION
        # =================================

        new_notification = GlobalNotification(
            
            title=title,

            message=message,

            banner_image=banner_url,

            notification_type=
            notification_type,

            action_text=
            action_text,

            action_link=    
            action_link,

            coupon_code=
            coupon_code,

            product_id=
            product_id,

            priority=
            priority,

            starts_at=
            starts_at,

            expires_at=
            expires_at,

            is_featured=
            is_featured,

            is_active=True
        
        )



        db.session.add(

            new_notification

        )



        db.session.commit()



        create_admin_notification(

            title="Global Announcement Published",

            message=f"""
            Title:
            {title}
            
            Type:
            {notification_type}
            
            Published globally.""",

            notification_type="announcement"

        )



        flash(

            "Global announcement published 🚀",

            "success"

        )



        return redirect(

            url_for(
                "admin.admin_global_notifications"
            )

        )



    # =====================================
    # FETCH ANNOUNCEMENTS
    # =====================================

    notifications = (

        GlobalNotification.query

        .order_by(

            GlobalNotification.created_at.desc()

        )

        .all()

    )



    return render_template(

        "admin/admin_global_notifications.html",

        notifications=notifications,

        admin_username=session.get(
            "admin_username"
        ),

        admin_role=session.get(
            "admin_role"
        )

    )
    
    
    
# =========================================
# TOGGLE GLOBAL NOTIFICATION
# =========================================

@admin_bp.route(

    "/admin/toggle-global-notification/<int:notification_id>",

    methods=["POST"]

)
@admin_required
def toggle_global_notification(notification_id):

    notification = GlobalNotification.query.get_or_404(

        notification_id

    )



    notification.is_active = (

        not notification.is_active

    )



    db.session.commit()



    state = "activated"



    if not notification.is_active:

        state = "deactivated"



    create_admin_notification(

        title="Global Announcement Updated",

        message=f"""

Announcement:

{notification.title}

was {state}.

""",

        notification_type="announcement"

    )



    flash(

        f"Announcement {state} successfully ✨",

        "success"

    )



    return redirect(

        url_for(
            "admin.admin_global_notifications"
        )

    )
    
    
    
# =========================================
# DELETE GLOBAL NOTIFICATION
# =========================================

@admin_bp.route(

    "/admin/delete-global-notification/<int:notification_id>",

    methods=["POST"]

)
@admin_required
def delete_global_notification(notification_id):

    notification = GlobalNotification.query.get_or_404(

        notification_id

    )



    notification_title = notification.title



    db.session.delete(

        notification

    )



    db.session.commit()



    create_admin_notification(

        title="Global Announcement Deleted",

        message=f"""

Announcement:

{notification_title}

was deleted.

""",

        notification_type="announcement"

    )



    flash(

        "Announcement deleted successfully 🗑",

        "success"

    )



    return redirect(

        url_for(
            "admin.admin_global_notifications"
        )

    )
    
    
    
    
# =========================================
# CLEAR ADMIN NOTIFICATIONS
# =========================================

@admin_bp.route(

    "/admin/clear-notifications",

    methods=["POST"]

)
@admin_required
def clear_admin_notifications():

    AdminNotification.query.delete()

    db.session.commit()



    flash(

        "All admin notifications cleared 🗑",

        "success"

    )



    return redirect(

        url_for(
            "admin.admin_notifications"
        )

    )
    
    
    
    
# =========================================
# REVIEW MANAGEMENT
# =========================================

@admin_bp.route(
    "/admin/reviews"
)
@admin_required
def admin_reviews():

    order_filter = request.args.get(
        "order_filter",
        "all"
    )
    
    review_filter = request.args.get(
        "review_filter",
        "all"
    )

    reviews = (

        ProductReview.query

        .order_by(
            ProductReview.created_at.desc()
        )

        .all()

    )

    if order_filter == "menu":
        
        reviews = [

            review

            for review in reviews

            if not review.is_custom_order

        ]
    
    elif order_filter == "custom":
        
        reviews = [

            review

            for review in reviews

            if review.is_custom_order

        ]

    total_reviews = len(reviews)

    average_rating = 0

    if reviews:

        average_rating = round(

            sum(
                review.rating
                for review in reviews
            )

            / total_reviews,

            1

        )

    # ============================
    # REVIEW INTELLIGENCE
    # ============================

    hidden_reviews_count = len(

        [

            review

            for review in reviews

            if not review.is_visible

        ]

    )

    five_star_reviews = len(

        [

            review

            for review in reviews

            if review.rating == 5

        ]

    )

    product_counter = {}

    product_rating_totals = {}

    product_rating_counts = {}

    for review in reviews:

        if review.product_name in [
            "Custom Order",
            "Rating Only"
        ]:
            continue

        product_name = review.product_name

        product_counter[product_name] = (

            product_counter.get(
                product_name,
                0
            ) + 1

        )

        product_rating_totals[product_name] = (

            product_rating_totals.get(
                product_name,
                0
            ) + review.rating

        )

        product_rating_counts[product_name] = (

            product_rating_counts.get(
                product_name,
                0
            ) + 1

        )

    most_reviewed_product = None

    if product_counter:

        most_reviewed_product = max(

            product_counter,

            key=product_counter.get

        )

    highest_rated_product = None

    highest_rating = 0

    for product_name in product_rating_totals:

        avg = (

            product_rating_totals[product_name]

            /

            product_rating_counts[product_name]

        )

        if avg > highest_rating:

            highest_rating = avg

            highest_rated_product = product_name

    for review in reviews:
        
        if review.is_custom_order:
            review.order = Order.query.filter_by(
                order_id=review.order_id
            ).first()
        

    return render_template(

        "admin/admin_reviews.html",

        reviews=reviews,

        total_reviews=total_reviews,

        average_rating=average_rating,

        hidden_reviews_count=hidden_reviews_count,

        five_star_reviews=five_star_reviews,

        most_reviewed_product=most_reviewed_product,

        highest_rated_product=highest_rated_product,

        order_filter=order_filter,
        
        review_filter=review_filter,

        admin_username=session.get(
            "admin_username"
        ),

        admin_role=session.get(
            "admin_role"
        )

    )



# =========================================
# REPLY TO REVIEW
# =========================================

@admin_bp.route(

    "/admin/reviews/reply/<int:review_id>",

    methods=["POST"]

)
@admin_required
def reply_review(review_id):

    review = ProductReview.query.get_or_404(

        review_id

    )

    if review.admin_reply:
        
        flash(
            "This review already has a reply 💌",
            "warning"
        )
        
        return redirect(
            url_for(
                "admin.admin_reviews"
            )
        )
    

    admin_reply = request.form.get(

        "admin_reply"
    )

    if not admin_reply:

        flash(

            "Reply cannot be empty",

            "danger"

        )

        return redirect(

            url_for(
                "admin.admin_reviews"
            )

        )

    review.admin_reply = admin_reply

    review.reply_by = session.get(

        "admin_username"
    )

    review.reply_date = datetime.utcnow()


    #=== Notify customer ===

    notification = UserNotification(

        user_id=review.customer_id,

        title="💌 We replied to your sweet words",

        message=(

            f"Our team replied to your review "

            f"for '{review.product_name}'. "

            f"Tap to read it ✨"

        ),

        notification_type="success",

        notification_category="review",

        order_id=review.order_id

    )

    db.session.add(notification)

    db.session.commit()

    flash(

        "Reply sent successfully 💌",

        "success"

    )

    return redirect(

        url_for(
            "admin.admin_reviews"
        )

    )




# =========================================
# TOGGLE REVIEW VISIBILITY
# =========================================

@admin_bp.route(

    "/admin/reviews/toggle/<int:review_id>",

    methods=["POST"]

)
@admin_required
def toggle_review_visibility(review_id):

    review = ProductReview.query.get_or_404(

        review_id

    )

    review.is_visible = (

        not review.is_visible

    )

    db.session.commit()

    state = "visible"

    if not review.is_visible:

        state = "hidden"

    flash(

        f"Review is now {state}",

        "success"

    )

    return redirect(

        url_for(
            "admin.admin_reviews"
        )

    )





# =========================================
# DELETE REVIEW
# =========================================

@admin_bp.route(

    "/admin/reviews/delete/<int:review_id>",

    methods=["POST"]

)
@admin_required
def delete_review_admin(review_id):

    review = ProductReview.query.get_or_404(

        review_id

    )

    db.session.delete(

        review

    )

    db.session.commit()

    flash(

        "Review deleted successfully 🗑",

        "success"

    )

    return redirect(

        url_for(
            "admin.admin_reviews"
        )

    )


# ====== Custom orders view in "REVIEWS" =======

@admin_bp.route(
    "/admin/order-details/<int:order_id>"
)
@admin_required
def admin_order_details(order_id):

    order = Order.query.get_or_404(
        order_id
    )

    try:

        order.products = json.loads(
            order.products_json
        )

    except:
        order.products = []

    return render_template(
        "order_details.html",
        order=order
    )



# =========================================
# ADMIN LOGOUT
# =========================================

@admin_bp.route(

    "/admin/logout"

)
def admin_logout():

    create_admin_notification(

        title="Admin Logout",

        message=f"""

Administrator:
{session.get('admin_username')}

logged out from
RM Bakes Control Center.

""",

        notification_type="admin"

    )



    session.clear()



    flash(

        "Admin logged out 🔒",

        "success"

    )



    return redirect(

        url_for(
            "admin.admin_login"
        )

    )

