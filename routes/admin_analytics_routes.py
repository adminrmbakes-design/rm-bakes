from collections import Counter
from datetime import datetime, timedelta
import json

from flask import (
    Blueprint,
    render_template,
    session
)

from utils.admin_guard import admin_required

from database import (
    User,
    Product,
    Favourite
)

from orders_database import Order

from custom_orders_database import (
    CustomOrder
)

# =========================================
# BLUEPRINT
# =========================================

admin_analytics_bp = Blueprint(

    "admin_analytics",

    __name__

)



# =========================================
# ANALYTICS DASHBOARD
# =========================================

@admin_analytics_bp.route(

    "/admin/analytics"

)
@admin_required
def analytics_dashboard():

    # =====================================
    # BASIC COUNTS
    # =====================================

    total_orders = Order.query.count()

    total_custom_orders = (

        CustomOrder.query.count()

    )

    total_customers = (

        User.query.filter_by(

            is_deleted=False

        ).count()

    )

    total_products = (

        Product.query.count()

    )

    total_favourites = (

        Favourite.query.count()

    )



    # =====================================
    # REVENUE
    # =====================================

    all_orders = Order.query.all()

    total_revenue = sum(

        order.grand_total or 0

        for order in all_orders

    )



    today = datetime.utcnow().date()

    week_ago = today - timedelta(days=7)

    month_ago = today - timedelta(days=30)



    today_revenue = sum(

        order.grand_total or 0

        for order in all_orders

        if order.created_at

        and order.created_at.date() == today

    )



    weekly_revenue = sum(

        order.grand_total or 0

        for order in all_orders

        if order.created_at

        and order.created_at.date() >= week_ago

    )



    monthly_revenue = sum(

        order.grand_total or 0

        for order in all_orders

        if order.created_at

        and order.created_at.date() >= month_ago

    )



    # =====================================
    # ORDER STATUS COUNTS
    # =====================================

    queued_orders = Order.query.filter_by(

        order_status="queued"

    ).count()



    production_orders = Order.query.filter_by(

        order_status="production"

    ).count()



    ready_orders = Order.query.filter_by(

        order_status="ready"

    ).count()



    delivered_orders = Order.query.filter_by(

        order_status="delivered"

    ).count()



    cancelled_orders = Order.query.filter_by(

        is_cancelled=True

    ).count()



    # =====================================
    # DESSERT STUDIO PIPELINE
    # =====================================

    pending_requests = (

        CustomOrder.query.filter_by(

            custom_status="pending"

        ).count()

    )



    quoted_requests = (

        CustomOrder.query.filter_by(

            custom_status="quoted"

        ).count()

    )



    approved_requests = (

        CustomOrder.query.filter_by(

            custom_status="approved"

        ).count()

    )



    converted_requests = (

        CustomOrder.query.filter_by(

            converted_to_order=True

        ).count()

    )



    # =====================================
    # PRODUCT INTELLIGENCE
    # =====================================

    product_counter = Counter()

    product_revenue = Counter()



    for order in all_orders:

        try:

            products = json.loads(

                order.products_json

            )



            for item in products:

                name = item.get(

                    "product_name",

                    "Unknown"

                )



                qty = item.get(

                    "quantity",

                    0

                )



                total = item.get(

                    "total",

                    0

                )



                product_counter[name] += qty

                product_revenue[name] += total



        except:

            continue



    top_products = (

        product_counter.most_common(10)

    )



    # =====================================
    # FAVOURITES
    # =====================================

    favourite_products = Counter()



    favourites = Favourite.query.all()



    for favourite in favourites:

        if favourite.product:

            favourite_products[
                favourite.product.product_name
            ] += 1



    top_favourites = (

        favourite_products.most_common(10)

    )



    # =====================================
    # CUSTOMER SPENDING
    # =====================================

    customer_spend = Counter()



    for order in all_orders:

        customer_spend[
            order.full_name or order.username
        ] += (

            order.grand_total or 0

        )



    vip_customers = (

        customer_spend.most_common(10)

    )



    average_order_value = 0

    if total_orders > 0:

        average_order_value = round(

            total_revenue / total_orders,

            2

        )



    # =====================================
    # HEATMAP DATA
    # =====================================

    heatmap = [

        0, 0, 0, 0

    ]



    for order in all_orders:

        if not order.created_at:

            continue



        hour = order.created_at.hour



        if 6 <= hour < 12:

            heatmap[0] += 1

        elif 12 <= hour < 17:

            heatmap[1] += 1

        elif 17 <= hour < 22:

            heatmap[2] += 1

        else:

            heatmap[3] += 1



    # =====================================
    # AI INSIGHTS
    # =====================================

    insights = []



    if top_products:

        insights.append(

            f"🔥 {top_products[0][0]} is currently the best selling dessert."

        )



    if top_favourites:

        insights.append(

            f"❤️ {top_favourites[0][0]} is the most loved product."

        )



    if converted_requests > 0:

        insights.append(

            f"💎 {converted_requests} Dessert Studio requests became real orders."

        )



    if average_order_value > 0:

        insights.append(

            f"💰 Average order value is ₹{average_order_value}"

        )

    # =====================================
    # CHART DATA
    # =====================================

    revenue_chart_labels = [

    "Mon",
    "Tue",
    "Wed",
    "Thu",
    "Fri",
    "Sat",
    "Sun"

    ]

    revenue_chart_values = [

    1200,
    1800,
    1600,
    2400,
    3000,
    4200,
    5000

    ]

    product_chart_labels = [

         product[0]

         for product in top_products[:5]
    ]

    product_chart_values = [

         product[1]

         for product in top_products[:5]

    ]

    status_chart_values = [

    queued_orders,

    production_orders,

    ready_orders,

    delivered_orders,

    cancelled_orders

    ]



    # =====================================
    # RENDER
    # =====================================

    return render_template(

        "admin/admin_analytics.html",

        total_revenue=total_revenue,

        today_revenue=today_revenue,

        weekly_revenue=weekly_revenue,

        monthly_revenue=monthly_revenue,

        total_orders=total_orders,

        total_custom_orders=total_custom_orders,

        total_customers=total_customers,

        total_products=total_products,

        total_favourites=total_favourites,

        queued_orders=queued_orders,

        production_orders=production_orders,

        ready_orders=ready_orders,

        delivered_orders=delivered_orders,

        cancelled_orders=cancelled_orders,

        pending_requests=pending_requests,

        quoted_requests=quoted_requests,

        approved_requests=approved_requests,

        converted_requests=converted_requests,

        top_products=top_products,

        top_favourites=top_favourites,

        vip_customers=vip_customers,

        average_order_value=average_order_value,

        heatmap=heatmap,

        insights=insights,

        revenue_chart_labels=revenue_chart_labels,

        revenue_chart_values=revenue_chart_values,

        product_chart_labels=product_chart_labels,

        product_chart_values=product_chart_values,

        status_chart_values=status_chart_values,

        admin_username=session.get(

            "admin_username"

        ),

        admin_role=session.get(

            "admin_role"

        )

    )
