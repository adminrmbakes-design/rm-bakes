from collections import Counter, defaultdict
from datetime import datetime, timedelta
import json

from flask import Blueprint, render_template, session

from utils.admin_guard import admin_required
from database import User, Product, Favourite
from orders_database import Order
from custom_orders_database import CustomOrder

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

@admin_analytics_bp.route("/admin/analytics")
@admin_required
def analytics_dashboard():

    # BASIC COUNTS
    total_orders = Order.query.count()
    total_custom_orders = CustomOrder.query.count()
    total_customers = User.query.filter_by(is_deleted=False).count()
    total_products = Product.query.count()
    total_favourites = Favourite.query.count()

    # REVENUE
    all_orders = Order.query.all()
    total_revenue = sum(order.grand_total or 0 for order in all_orders)

    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    today_revenue = sum(
        order.grand_total or 0
        for order in all_orders
        if order.created_at and order.created_at.date() == today
    )

    weekly_revenue = sum(
        order.grand_total or 0
        for order in all_orders
        if order.created_at and order.created_at.date() >= week_ago
    )

    monthly_revenue = sum(
        order.grand_total or 0
        for order in all_orders
        if order.created_at and order.created_at.date() >= month_ago
    )

    # ORDER STATUS
    queued_orders = Order.query.filter_by(order_status="queued").count()
    approved_orders = Order.query.filter_by(order_status="approved").count()
    preparing_orders = Order.query.filter_by(order_status="preparing").count()
    baking_orders = Order.query.filter_by(order_status="baking").count()
    packed_orders = Order.query.filter_by(order_status="packed").count()
    delivery_orders = Order.query.filter_by(order_status="out_for_delivery").count()
    delivered_orders = Order.query.filter_by(order_status="delivered").count()
    cancelled_orders = Order.query.filter_by(order_status="cancelled").count()
    # DESSERT STUDIO METRICS
    quoted_requests = CustomOrder.query.filter_by(custom_status="quoted").count()
    converted_requests = CustomOrder.query.filter_by(converted_to_order=True).count()
    
    # PRODUCT INTELLIGENCE
    product_counter = Counter()
    product_revenue = Counter()

    for order in all_orders:
        try:
            products = json.loads(order.products_json)

            for item in products:
                name = item.get("product_name", "Unknown")
                qty = item.get("quantity", 0)
                total = item.get("total", 0)

                product_counter[name] += qty
                product_revenue[name] += total
        except Exception:
            continue

    top_products = product_counter.most_common(10)
    top_product_revenue = product_revenue.most_common(10)

    # FAVOURITES
    favourite_products = Counter()

    for favourite in Favourite.query.all():
        if favourite.product:
            favourite_products[favourite.product.product_name] += 1

    top_favourites = favourite_products.most_common(10)

    # CUSTOMER SPENDING
    customer_spend = Counter()

    for order in all_orders:
        customer_spend[order.full_name or order.username] += (
            order.grand_total or 0
        )

    vip_customers = customer_spend.most_common(10)

    average_order_value = (
        round(total_revenue / total_orders, 2)
        if total_orders > 0 else 0
    )

    # HEATMAP
    heatmap = [0, 0, 0, 0]

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

    # BUSINESS HEALTH
    health_score = 100

    cancellation_rate = 0
    if total_orders > 0:
        cancellation_rate = round(
            (cancelled_orders / total_orders) * 100, 1
        )
        health_score -= int(cancellation_rate * 1.5)

    delivery_rate = 0
    if total_orders > 0:
        delivery_rate = round(
            (delivered_orders / total_orders) * 100, 1
        )
        health_score += int(delivery_rate * 0.10)

    conversion_rate = 0
    if total_custom_orders > 0:
        conversion_rate = round(
            (converted_requests / total_custom_orders) * 100, 1
        )
        health_score += int(conversion_rate * 0.15)

    health_score = max(0, min(100, health_score))

    if health_score >= 85:
        health_status = "EXCELLENT"
    elif health_score >= 70:
        health_status = "GOOD"
    elif health_score >= 50:
        health_status = "AVERAGE"
    else:
        health_status = "NEEDS ATTENTION"

    # QUOTE ACCEPTANCE
    accepted_quotes = CustomOrder.query.filter_by(
        customer_response="accepted"
    ).count()

    rejected_quotes = CustomOrder.query.filter_by(
        customer_response="rejected"
    ).count()

    pending_quote_responses = CustomOrder.query.filter_by(
        customer_response="pending"
    ).count()

    quote_acceptance_rate = 0
    if quoted_requests > 0:
        quote_acceptance_rate = round(
            (accepted_quotes / quoted_requests) * 100, 1
        )

    # FORECAST
    forecast_revenue = monthly_revenue
    if monthly_revenue > 0:
        daily_average = monthly_revenue / 30
        forecast_revenue = round(daily_average * 30, 0)

    # FLAVOURS & OCCASIONS
    flavour_counter = Counter()
    occasion_counter = Counter()

    custom_orders = CustomOrder.query.all()

    for order in custom_orders:
        if getattr(order, "flavor", None):
            flavour_counter[order.flavor] += 1

        if getattr(order, "occasion", None):
            occasion_counter[order.occasion] += 1

    top_flavours = flavour_counter.most_common(5)
    top_occasions = occasion_counter.most_common(5)

    # DESSERT STUDIO INTELLIGENCE
    budget_orders = [
        order.budget
        for order in custom_orders
        if getattr(order, "budget", None)
    ]

    average_budget = 0
    if budget_orders:
        average_budget = round(
            sum(budget_orders) / len(budget_orders), 2
        )

    studio_success_rate = 0
    if total_custom_orders > 0:
        studio_success_rate = round(
            (converted_requests / total_custom_orders) * 100, 1
        )

    # AI INSIGHTS
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

    # REAL REVENUE CHART DATA
    revenue_chart_labels = []
    revenue_chart_values = []

    for days_back in range(6, -1, -1):
        target_date = today - timedelta(days=days_back)

        day_revenue = sum(
            order.grand_total or 0
            for order in all_orders
            if order.created_at
            and order.created_at.date() == target_date
        )

        revenue_chart_labels.append(
            target_date.strftime("%a")
        )

        revenue_chart_values.append(
            round(day_revenue, 2)
        )

    revenue_growth = 0
    if len(revenue_chart_values) > 1:
        revenue_growth = round(
            (
                (revenue_chart_values[-1] - revenue_chart_values[-2])
                / max(revenue_chart_values[-2], 1)
            ) * 100,
            1
        )

    product_chart_labels = [
        product[0] for product in top_products[:5]
    ]

    product_chart_values = [
        product[1] for product in top_products[:5]
    ]

    status_chart_values = [
       "Queued",
       "Approved",
       "Preparing",
       "Baking",
       "Packed",
       "Delivery",
       "Delivered",
       "Cancelled"
    ]

    

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
        approved_orders=approved_orders,
        preparing_orders=preparing_orders,
        baking_orders=baking_orders,
        packed_orders=packed_orders,
        delivery_orders=delivery_orders,
        delivered_orders=delivered_orders,
        cancelled_orders=cancelled_orders,
        quoted_requests=quoted_requests,
        converted_requests=converted_requests,
        top_products=top_products,
        top_product_revenue=top_product_revenue,
        top_favourites=top_favourites,
        vip_customers=vip_customers,
        average_order_value=average_order_value,
        heatmap=heatmap,
        insights=insights,
        revenue_chart_labels=revenue_chart_labels,
        revenue_chart_values=revenue_chart_values,
        revenue_growth=revenue_growth,
        product_chart_labels=product_chart_labels,
        product_chart_values=product_chart_values,
        status_chart_values=status_chart_values,
        average_budget=average_budget,
        accepted_quotes=accepted_quotes,
        rejected_quotes=rejected_quotes,
        pending_quote_responses=pending_quote_responses,
        studio_success_rate=studio_success_rate,
        health_score=health_score,
        health_status=health_status,
        cancellation_rate=cancellation_rate,
        delivery_rate=delivery_rate,
        conversion_rate=conversion_rate,
        quote_acceptance_rate=quote_acceptance_rate,
        forecast_revenue=forecast_revenue,
        top_flavours=top_flavours,
        top_occasions=top_occasions,
        admin_username=session.get("admin_username"),
        admin_role=session.get("admin_role")
    )
