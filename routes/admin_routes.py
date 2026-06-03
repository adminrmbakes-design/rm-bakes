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

    Order

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

            is_active=True

        )



        db.session.add(

            new_notification

        )



        db.session.commit()



        create_admin_notification(

            title="Global Announcement Published",

            message=f"""

Announcement:

{title}

was published globally.

""",

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
# ADMIN ANALYTICS
# =========================================

@admin_bp.route(
    "/admin/analytics"
)
@admin_required
def admin_analytics():

    # =====================================
    # LOAD DATA
    # =====================================

    all_orders = Order.query.all()

    custom_orders = CustomOrder.query.all()

    # =====================================
    # BASIC METRICS
    # =====================================

    total_orders = len(all_orders)

    total_custom_orders = len(custom_orders)

    delivered_orders = [

        order for order in all_orders

        if order.order_status == "delivered"

    ]

    cancelled_orders = [

        order for order in all_orders

        if order.order_status == "cancelled"

    ]

    active_orders = [

        order for order in all_orders

        if order.order_status not in [

            "delivered",
            "cancelled"

        ]

    ]

    # =====================================
    # REVENUE
    # =====================================

    total_revenue = sum(

        order.grand_total or 0

        for order in delivered_orders

    )

    pending_revenue = sum(

        order.grand_total or 0

        for order in active_orders

    )

    # =====================================
    # PRODUCTION STATES
    # =====================================

    queued_count = len([

        order for order in all_orders

        if order.order_status == "queued"

    ])

    preparing_count = len([

        order for order in all_orders

        if order.order_status == "preparing"

    ])

    baking_count = len([

        order for order in all_orders

        if order.order_status == "baking"

    ])

    packed_count = len([

        order for order in all_orders

        if order.order_status == "packed"

    ])

    delivery_count = len([

        order for order in all_orders

        if order.order_status == "out_for_delivery"

    ])

    # =====================================
    # CUSTOM ORDER CONVERSION
    # =====================================

    approved_custom_orders = len([

        order for order in custom_orders

        if order.customer_response == "accepted"

    ])

    converted_custom_orders = len([

        order for order in custom_orders

        if order.converted_to_order

    ])

    # =====================================
    # RECENT REVENUE GRAPH
    # =====================================

    recent_orders = sorted(

        delivered_orders,

        key=lambda x: x.created_at

    )[-7:]

    revenue_labels = [

        order.created_at.strftime("%d %b")

        for order in recent_orders

    ]

    revenue_data = [

        float(order.grand_total or 0)

        for order in recent_orders

    ]




# =====================================
    # PRODUCT INTELLIGENCE
    # =====================================

    all_products = Product.query.all()

    # ================================
    # TOP EXPENSIVE PRODUCTS
    # ================================

    top_products = sorted(

        all_products,

        key=lambda x: x.product_price,

        reverse=True

    )[:5]

    top_product_names = [

        product.product_name

        for product in top_products

    ]

    top_product_prices = [

        float(product.product_price)

        for product in top_products

    ]

    # ================================
    # CATEGORY DISTRIBUTION
    # ================================

    category_counts = {}

    for product in all_products:

        category = product.product_category

        category_counts[category] = (

            category_counts.get(category, 0)

            + 1

        )

    category_labels = list(

        category_counts.keys()

    )

    category_data = list(

        category_counts.values()

    )
    
    
    
# =====================================
    # LIVE ACTIVITY FEED
    # =====================================

    recent_orders = sorted(

        all_orders,

        key=lambda x: x.created_at,

        reverse=True

    )[:6]

    activity_feed = []

    for order in recent_orders:

        icon = "🟢"

        if order.order_status == "cancelled":

            icon = "🔴"

        elif order.order_status == "queued":

            icon = "🟡"

        elif order.is_custom_order:

            icon = "✨"

        activity_feed.append({

            "icon": icon,

            "message": (

                f"{order.order_number} "

                f"→ "

                f"{order.order_status.replace('_',' ').title()}"

            ),

            "time": order.created_at.strftime(
                "%d %b • %I:%M %p"
            )

        })
        
        
# =====================================
    # ORDER HEATMAP
    # =====================================

    morning_orders = 0
    afternoon_orders = 0
    evening_orders = 0
    night_orders = 0

    for order in all_orders:

        hour = order.created_at.hour

        # ================================
        # MORNING
        # ================================

        if 6 <= hour < 12:

            morning_orders += 1

        # ================================
        # AFTERNOON
        # ================================

        elif 12 <= hour < 17:

            afternoon_orders += 1

        # ================================
        # EVENING
        # ================================

        elif 17 <= hour < 22:

            evening_orders += 1

        # ================================
        # NIGHT
        # ================================

        else:

            night_orders += 1
            
               
# =====================================
    # AI BUSINESS INSIGHTS
    # =====================================

    ai_insights = []
    
    # DEFAULT VALUES
    conversion_rate = 0
    cancel_rate = 0

    # ================================
    # EVENING PEAK
    # ================================

    if evening_orders > (

        morning_orders
        +
        afternoon_orders

    ):

        ai_insights.append({

            "type":"warning",

            "message":(

                "🌆 Evening traffic dominates "
                "order flow. Delivery pressure "
                "likely during peak hours."

            )

        })

    # ================================
    # CUSTOM CONVERSION
    # ================================

    if total_custom_orders > 0:

        conversion_rate = round(

            (
                converted_custom_orders
                /
                total_custom_orders
            ) * 100,

            1

        )

        ai_insights.append({

            "type":"success",

            "message":(

                f"✨ Dessert Studio conversion "
                f"rate is currently "
                f"{conversion_rate}%."

            )

        })

    # ================================
    # CANCELLATION WARNING
    # ================================

    if cancelled_orders:

        cancel_rate = round(

            (
                len(cancelled_orders)
                /
                total_orders
            ) * 100,

            1

        )

        if cancel_rate >= 20:

            ai_insights.append({

                "type":"danger",

                "message":(

                    f"🔴 Cancellation rate is "
                    f"{cancel_rate}%. "
                    f"Operational review advised."

                )

            })

    # ================================
    # PREMIUM PRODUCT ANALYSIS
    # ================================

    premium_products = [

        product for product in all_products

        if product.product_price >= 1000

    ]

    if len(premium_products) >= 5:

        ai_insights.append({

            "type":"success",

            "message":(

                "💎 Premium dessert portfolio "
                "is strongly positioned "
                "for luxury branding."

            )

        })

    # ================================
    # ACTIVE WORKLOAD
    # ================================

    if len(active_orders) >= 10:

        ai_insights.append({

            "type":"warning",

            "message":(

                "⚙ Kitchen workload currently "
                "running at elevated capacity."

            )

        })
        
# =====================================
    # PREDICTIVE FORECASTING
    # =====================================

    recent_completed_orders = [

        order for order in all_orders

        if order.order_status == "delivered"

    ]

    recent_completed_orders = sorted(

        recent_completed_orders,

        key=lambda x: x.created_at,

        reverse=True

    )[:10]



    if recent_completed_orders:

        avg_recent_revenue = round(

            sum(

                float(order.grand_total)

                for order in recent_completed_orders

            ) / len(recent_completed_orders),

            2

        )

    else:

        avg_recent_revenue = 0



    # ================================
    # PREDICTED TOMORROW REVENUE
    # ================================

    predicted_revenue = round(

        avg_recent_revenue
        *
        1.18,

        2

    )



    # ================================
    # BUSINESS HEALTH SCORE
    # ================================

    business_health = 70

    if conversion_rate >= 60:

        business_health += 10

    if cancel_rate < 15:

        business_health += 10

    if active_orders:

        business_health += 5

    if total_revenue >= 50000:

        business_health += 5



    business_health = min(
        business_health,
        100
    )
    
    
    
# =====================================
    # CUSTOMER INTELLIGENCE
    # =====================================

    customer_stats = {}

    for order in all_orders:

        full_name = (
            order.full_name
            or
            "Unknown"
        )

        if full_name not in customer_stats:

            customer_stats[full_name] = {

                "orders":0,
                "spent":0

            }

        customer_stats[full_name]["orders"] += 1

        customer_stats[full_name]["spent"] += float(

            order.grand_total or 0

        )



    # ================================
    # REPEAT CUSTOMERS
    # ================================

    repeat_customers = [

        customer

        for customer, data

        in customer_stats.items()

        if data["orders"] >= 2

    ]



    if total_orders > 0:

        retention_rate = round(

            (
                len(repeat_customers)
                /
                len(customer_stats)
            ) * 100,

            1

        )

    else:

        retention_rate = 0



    # ================================
    # VIP CUSTOMERS
    # ================================

    vip_customers = sorted(

        customer_stats.items(),

        key=lambda x: x[1]["spent"],

        reverse=True

    )[:5]
    
    
    
# =====================================
    # DELIVERY INTELLIGENCE
    # =====================================

    delivered_orders_with_time = [

        order for order in all_orders

        if (
            order.delivered_at
            and
            order.created_at
        )

    ]



    if delivered_orders_with_time:

        avg_delivery_minutes = round(

            sum(

                (
                    order.delivered_at
                    -
                    order.created_at
                ).total_seconds() / 60

                for order in delivered_orders_with_time

            ) / len(delivered_orders_with_time),

            1

        )

    else:

        avg_delivery_minutes = 0



    # =====================================
    # PRODUCT PERFORMANCE AI
    # =====================================

    product_performance = {}

    flavor_performance = {}



    for order in all_orders:

        try:

            products = json.loads(
                order.products_json
            )

        except:

            products = []



        for item in products:

            name = item.get(
                "product_name",
                "Unknown"
            )

            total = float(

                item.get(
                    "total_price",
                    0
                )

            )

            product_performance[name] = (

                product_performance.get(
                    name,
                    0
                )

                + total

            )



            # ================================
            # FLAVOR AI
            # ================================

            lower_name = name.lower()

            flavors = [

                "chocolate",
                "vanilla",
                "strawberry",
                "pistachio",
                "lotus",
                "blueberry",
                "mango",
                "caramel"

            ]



            for flavor in flavors:

                if flavor in lower_name:

                    flavor_performance[flavor] = (

                        flavor_performance.get(
                            flavor,
                            0
                        )

                        + 1

                    )



    # ================================
    # TOP PRODUCTS
    # ================================

    top_products_live = sorted(

        product_performance.items(),

        key=lambda x: x[1],

        reverse=True

    )[:5]



    top_product_live_names = [

        item[0]

        for item in top_products_live

    ]



    top_product_live_sales = [

        round(item[1],2)

        for item in top_products_live

    ]



    # ================================
    # TOP FLAVORS
    # ================================

    top_flavors = sorted(

        flavor_performance.items(),

        key=lambda x: x[1],

        reverse=True

    )[:5]



    # =====================================
    # INVENTORY INTELLIGENCE
    # =====================================

    #inventory_alerts = []



    #for product in all_products:

        #if product.product_quantity <= 5:

            #inventory_alerts.append(

                #f"⚠ {product.product_name} "
                #f"stock running low."

            #)



    # =====================================
    # MOMENTUM ENGINE
    # =====================================

    momentum_score = 50



    if total_revenue >= 50000:

        momentum_score += 15

    if len(active_orders) >= 10:

        momentum_score += 10

    if retention_rate >= 30:

        momentum_score += 10

    if conversion_rate >= 50:

        momentum_score += 15



    momentum_score = min(
        momentum_score,
        100
    )



    # =====================================
    # SMART ALERTS
    # =====================================

    smart_alerts = []



    if avg_delivery_minutes >= 180:

        smart_alerts.append(

            "🚚 Delivery duration increasing."

        )



    if evening_orders > morning_orders:

        smart_alerts.append(

            "🌆 Evening traffic surge detected."

        )



    if conversion_rate >= 70:

        smart_alerts.append(

            "✨ Dessert Studio conversion "
            "performing strongly."

        )



    if retention_rate >= 40:

        smart_alerts.append(

            "👑 Customer loyalty metrics "
            "looking healthy."

        )



    # =====================================
    # SALES TREND CURVE
    # =====================================

    monthly_sales_labels = []

    monthly_sales_data = []



    monthly_buckets = {}



    for order in delivered_orders:

        month = order.created_at.strftime(
            "%b"
        )

        monthly_buckets[month] = (

            monthly_buckets.get(
                month,
                0
            )

            + float(order.grand_total or 0)

        )



    for key, value in monthly_buckets.items():

        monthly_sales_labels.append(key)

        monthly_sales_data.append(value)
        
                                                      
                                                                                                                                                  
    # =====================================
    # RENDER
    # =====================================

    return render_template(

        "admin/admin_analytics.html",

        expiry_time=session.get(
            "admin_expiry"
        ),

        admin_username=session.get(
            "admin_username"
        ),

        admin_role=session.get(
            "admin_role"
        ),

        admin_minutes=session.get(
            "admin_minutes"
        ),

        total_orders=total_orders,

        total_custom_orders=total_custom_orders,

        delivered_orders=len(
            delivered_orders
        ),

        cancelled_orders=len(
            cancelled_orders
        ),

        active_orders=len(
            active_orders
        ),

        total_revenue=round(
            total_revenue,
            2
        ),

        pending_revenue=round(
            pending_revenue,
            2
        ),

        queued_count=queued_count,

        preparing_count=preparing_count,

        baking_count=baking_count,

        packed_count=packed_count,

        delivery_count=delivery_count,

        approved_custom_orders=
            approved_custom_orders,

        converted_custom_orders=
            converted_custom_orders,

        revenue_labels=revenue_labels,

        revenue_data=revenue_data,
        
        top_product_names=
            top_product_names,

        top_product_prices=
            top_product_prices,

        category_labels=
            category_labels,

        category_data=
            category_data,
            
            activity_feed=
            activity_feed,
            
            morning_orders=
            morning_orders,

        afternoon_orders=
            afternoon_orders,

        evening_orders=
            evening_orders,

        night_orders=
            night_orders,
            
            ai_insights=
            ai_insights,
            
            predicted_revenue=
            predicted_revenue,

        business_health=
            business_health,
            
            retention_rate=
            retention_rate,

        vip_customers=
            vip_customers,
            
            avg_delivery_minutes=
            avg_delivery_minutes,

        top_product_live_names=
            top_product_live_names,

        top_product_live_sales=
            top_product_live_sales,

        top_flavors=
            top_flavors,

        #inventory_alerts=
            #inventory_alerts,

        momentum_score=
            momentum_score,

        smart_alerts=
            smart_alerts,

        monthly_sales_labels=
            monthly_sales_labels,

        monthly_sales_data=
            monthly_sales_data

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
