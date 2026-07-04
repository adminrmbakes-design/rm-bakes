from collections import Counter
from datetime import datetime, timedelta
import json

from flask import Blueprint, render_template, session, redirect, url_for, flash

from utils.admin_guard import admin_required
from database import db, User, Product, Favourite
from orders_database import Order, AnalyticsReset
from custom_orders_database import CustomOrder

# =========================================
# BLUEPRINT
# =========================================

admin_analytics_bp = Blueprint(
    "admin_analytics",
    __name__
)


# =========================================
# HELPERS
# =========================================

# Friendly icon per Razorpay payment mode, used on the
# "Payment Mode Breakdown" cards.
PAYMENT_MODE_ICONS = {
    "UPI":            "📱",
    "Card":           "💳",
    "Net Banking":    "🏦",
    "EMI":            "🧾",
    "Wallet":         "👛",
    "Bank Transfer":  "🏧",
    "Pay Later":      "🕒",
}


def _get_reset_cutoff():
    """
    Returns (cutoff_datetime_or_None, latest_reset_row_or_None).
    See the AnalyticsReset model (orders_database.py) for why this
    is a "soft reset" — it never deletes real order data.
    """
    latest = (
        AnalyticsReset.query
        .order_by(AnalyticsReset.reset_at.desc())
        .first()
    )
    return (latest.reset_at if latest else None), latest


def _is_collected(order):
    """
    True if the money for this order is actually in hand:
      - Online orders: only once payment_verified is True.
      - Cash on Delivery orders: only once delivered (cash is
        collected at the door on delivery).
    """
    if order.payment_method == "Online":
        return bool(order.payment_verified)
    if order.payment_method == "Cash On Delivery":
        return order.order_status == "delivered"
    return False


# =========================================
# ANALYTICS DASHBOARD  (FIX #3 — recreated)
# =========================================

@admin_analytics_bp.route("/admin/analytics")
@admin_required
def analytics_dashboard():

    reset_cutoff, reset_row = _get_reset_cutoff()

    # =================================
    # ORDERS IN SCOPE
    # (everything since the last analytics reset, or all-time
    # if the dashboard has never been reset)
    # =================================

    order_query = Order.query
    if reset_cutoff:
        order_query = order_query.filter(Order.ordered_at >= reset_cutoff)
    all_orders = order_query.all()

    custom_order_query = CustomOrder.query
    if reset_cutoff:
        custom_order_query = custom_order_query.filter(CustomOrder.created_at >= reset_cutoff)
    custom_orders = custom_order_query.all()

    total_orders = len(all_orders)
    total_custom_orders = len(custom_orders)
    total_customers = User.query.filter_by(is_deleted=False).count()
    total_products = Product.query.count()
    total_favourites = Favourite.query.count()

    # Cancelled orders never represent real or expected revenue —
    # excluded from every revenue figure below (previously they
    # were silently counted as "Total Revenue", which overstated it).
    active_orders = [o for o in all_orders if o.order_status != "cancelled"]
    cancelled_orders_list = [o for o in all_orders if o.order_status == "cancelled"]
    cancelled_value = sum(o.grand_total or 0 for o in cancelled_orders_list)

    # =================================
    # FIX #3: TWO REAL REVENUE TYPES
    # =================================

    income_generated = sum(
        o.grand_total or 0 for o in active_orders if _is_collected(o)
    )

    pending_income = sum(
        o.grand_total or 0
        for o in active_orders
        if o.payment_method == "Cash On Delivery" and o.order_status != "delivered"
    )

    total_potential_revenue = income_generated + pending_income

    unverified_online_orders = [
        o for o in active_orders
        if o.payment_method == "Online" and not o.payment_verified
    ]
    unverified_value = sum(o.grand_total or 0 for o in unverified_online_orders)

    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    def _collected_since(start_date):
        return sum(
            o.grand_total or 0
            for o in active_orders
            if _is_collected(o) and o.ordered_at and o.ordered_at.date() >= start_date
        )

    today_revenue = _collected_since(today)
    weekly_revenue = _collected_since(week_ago)
    monthly_revenue = _collected_since(month_ago)

    average_order_value = (
        round(total_potential_revenue / len(active_orders), 2)
        if active_orders else 0
    )

    # =================================
    # PAYMENT SPLIT — Prepaid vs COD
    # =================================

    prepaid_orders = [o for o in active_orders if o.payment_method == "Online"]
    cod_orders     = [o for o in active_orders if o.payment_method == "Cash On Delivery"]

    prepaid_count = len(prepaid_orders)
    cod_count     = len(cod_orders)
    payment_split_total = prepaid_count + cod_count

    prepaid_pct = round((prepaid_count / payment_split_total) * 100, 1) if payment_split_total else 0
    cod_pct     = round(100 - prepaid_pct, 1) if payment_split_total else 0

    prepaid_revenue = sum(o.grand_total or 0 for o in prepaid_orders)
    cod_revenue     = sum(o.grand_total or 0 for o in cod_orders)

    # Payment mode breakdown (UPI / Card / Net Banking / EMI / Wallet...)
    # — only possible now that Razorpay's payment_mode is actually
    # captured at checkout.
    payment_mode_counter = Counter()
    for o in prepaid_orders:
        payment_mode_counter[o.payment_mode or "Unknown"] += 1

    payment_mode_breakdown = [
        {"mode": mode, "count": count, "icon": PAYMENT_MODE_ICONS.get(mode, "💳")}
        for mode, count in payment_mode_counter.most_common()
    ]

    # =================================
    # ORDER STATUS PIPELINE
    # =================================

    status_counter = Counter(o.order_status for o in all_orders)

    queued_orders     = status_counter.get("queued", 0)
    approved_orders   = status_counter.get("approved", 0)
    preparing_orders  = status_counter.get("preparing", 0)
    baking_orders     = status_counter.get("baking", 0)
    packed_orders     = status_counter.get("packed", 0)
    delivery_orders   = status_counter.get("out_for_delivery", 0)
    delivered_orders  = status_counter.get("delivered", 0)
    cancelled_orders  = status_counter.get("cancelled", 0)

    # =================================
    # DESSERT STUDIO METRICS
    # =================================

    quoted_requests    = len([o for o in custom_orders if o.custom_status == "quoted"])
    converted_requests = len([o for o in custom_orders if o.converted_to_order])

    # =================================
    # PRODUCT INTELLIGENCE
    # (cancelled orders excluded — a cancelled order's items were
    # never actually sold)
    # =================================

    product_counter = Counter()
    product_revenue = Counter()

    for order in active_orders:
        try:
            products = json.loads(order.products_json)

            for item in products:
                name  = item.get("product_name", "Unknown")
                qty   = item.get("product_quantity", 0)
                total = item.get("total_price", 0)

                product_counter[name] += qty
                product_revenue[name] += total
        except Exception:
            continue

    top_products = product_counter.most_common(10)
    top_product_revenue = product_revenue.most_common(10)

    # =================================
    # FAVOURITES
    # (a live engagement snapshot, not a time-windowed performance
    # stat — intentionally NOT affected by the analytics reset)
    # =================================

    favourite_products = Counter()

    for favourite in Favourite.query.all():
        if favourite.product:
            favourite_products[favourite.product.product_name] += 1

    top_favourites = favourite_products.most_common(10)

    # =================================
    # CUSTOMER SPENDING (VIP)
    # =================================

    customer_spend = Counter()

    for order in active_orders:
        customer_spend[order.full_name or order.username] += (order.grand_total or 0)

    vip_customers = customer_spend.most_common(10)

    # =================================
    # HEATMAP (order activity by time of day)
    # =================================

    heatmap = [0, 0, 0, 0]

    for order in all_orders:
        if not order.ordered_at:
            continue

        hour = order.ordered_at.hour

        if 6 <= hour < 12:
            heatmap[0] += 1
        elif 12 <= hour < 17:
            heatmap[1] += 1
        elif 17 <= hour < 22:
            heatmap[2] += 1
        else:
            heatmap[3] += 1

    # =================================
    # BUSINESS HEALTH
    # =================================

    health_score = 100

    cancellation_rate = 0
    if total_orders > 0:
        cancellation_rate = round((cancelled_orders / total_orders) * 100, 1)
        health_score -= int(cancellation_rate * 1.5)

    delivery_rate = 0
    if total_orders > 0:
        delivery_rate = round((delivered_orders / total_orders) * 100, 1)
        health_score += int(delivery_rate * 0.10)

    conversion_rate = 0
    if total_custom_orders > 0:
        conversion_rate = round((converted_requests / total_custom_orders) * 100, 1)
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

    # =================================
    # QUOTE ACCEPTANCE
    # =================================

    accepted_quotes = len([o for o in custom_orders if o.customer_response == "accepted"])
    rejected_quotes = len([o for o in custom_orders if o.customer_response == "rejected"])
    pending_quote_responses = len([o for o in custom_orders if o.customer_response == "pending"])

    quote_acceptance_rate = 0
    if quoted_requests > 0:
        quote_acceptance_rate = round((accepted_quotes / quoted_requests) * 100, 1)

    # =================================
    # 30-DAY FORECAST (at current pace)
    # Previously this "forecast" just re-derived monthly_revenue
    # from itself (daily_average = monthly/30, forecast = daily*30
    # — mathematically a no-op). Now it actually forecasts: it
    # projects the trailing-7-day collection pace forward 30 days,
    # so a busy/quiet recent week actually moves the number.
    # =================================

    daily_avg_recent = (weekly_revenue / 7) if weekly_revenue else 0
    forecast_revenue = round(daily_avg_recent * 30, 0)

    # =================================
    # FLAVOURS & OCCASIONS
    # =================================

    flavour_counter = Counter()
    occasion_counter = Counter()

    for order in custom_orders:
        if getattr(order, "flavor", None):
            flavour_counter[order.flavor] += 1

        if getattr(order, "occasion", None):
            occasion_counter[order.occasion] += 1

    top_flavours = flavour_counter.most_common(5)
    top_occasions = occasion_counter.most_common(5)

    # =================================
    # DESSERT STUDIO INTELLIGENCE
    # =================================

    budget_orders = [
        order.budget for order in custom_orders if getattr(order, "budget", None)
    ]

    average_budget = 0
    if budget_orders:
        average_budget = round(sum(budget_orders) / len(budget_orders), 2)

    studio_success_rate = 0
    if total_custom_orders > 0:
        studio_success_rate = round((converted_requests / total_custom_orders) * 100, 1)

    # =================================
    # AI INSIGHTS
    # =================================

    insights = []

    if top_products:
        insights.append(f"🔥 {top_products[0][0]} is currently the best selling dessert.")

    if top_favourites:
        insights.append(f"❤️ {top_favourites[0][0]} is the most loved product.")

    if converted_requests > 0:
        insights.append(f"💎 {converted_requests} Dessert Studio requests became real orders.")

    if average_order_value > 0:
        insights.append(f"💰 Average order value is ₹{average_order_value}")

    if payment_split_total > 0:
        insights.append(
            f"💳 {prepaid_pct}% of orders are prepaid online, {cod_pct}% choose Cash on Delivery."
        )

    if pending_income > 0:
        insights.append(
            f"⏳ ₹{'{:,.0f}'.format(pending_income)} is still pending collection from COD orders in the pipeline."
        )

    if unverified_online_orders:
        insights.append(
            f"⚠️ {len(unverified_online_orders)} online order(s) have unverified payments — worth a manual check."
        )

    # =================================
    # REVENUE CHART — Collected vs Pending, last 7 days
    # =================================

    revenue_chart_labels = []
    collected_chart_values = []
    pending_chart_values = []

    for days_back in range(6, -1, -1):
        target_date = today - timedelta(days=days_back)

        day_orders = [
            o for o in active_orders
            if o.ordered_at and o.ordered_at.date() == target_date
        ]

        day_collected = sum(o.grand_total or 0 for o in day_orders if _is_collected(o))
        day_pending = sum(
            o.grand_total or 0 for o in day_orders
            if o.payment_method == "Cash On Delivery" and o.order_status != "delivered"
        )

        revenue_chart_labels.append(target_date.strftime("%a"))
        collected_chart_values.append(round(day_collected, 2))
        pending_chart_values.append(round(day_pending, 2))

    revenue_growth = 0
    if len(collected_chart_values) > 1:
        revenue_growth = round(
            (
                (collected_chart_values[-1] - collected_chart_values[-2])
                / max(collected_chart_values[-2], 1)
            ) * 100,
            1
        )

    product_chart_labels = [product[0] for product in top_products[:5]]
    product_chart_values = [product[1] for product in top_products[:5]]

    status_chart_values = [
        queued_orders, approved_orders, preparing_orders, baking_orders,
        packed_orders, delivery_orders, delivered_orders, cancelled_orders
    ]

    return render_template(
        "admin/admin_analytics.html",

        # revenue — two real types (FIX #3)
        income_generated=income_generated,
        pending_income=pending_income,
        total_potential_revenue=total_potential_revenue,
        cancelled_value=cancelled_value,
        unverified_online_orders=unverified_online_orders,
        unverified_value=unverified_value,
        today_revenue=today_revenue,
        weekly_revenue=weekly_revenue,
        monthly_revenue=monthly_revenue,

        # payment split
        prepaid_count=prepaid_count,
        cod_count=cod_count,
        prepaid_pct=prepaid_pct,
        cod_pct=cod_pct,
        prepaid_revenue=prepaid_revenue,
        cod_revenue=cod_revenue,
        payment_mode_breakdown=payment_mode_breakdown,

        # counts
        total_orders=total_orders,
        total_custom_orders=total_custom_orders,
        total_customers=total_customers,
        total_products=total_products,
        total_favourites=total_favourites,

        # order pipeline
        queued_orders=queued_orders,
        approved_orders=approved_orders,
        preparing_orders=preparing_orders,
        baking_orders=baking_orders,
        packed_orders=packed_orders,
        delivery_orders=delivery_orders,
        delivered_orders=delivered_orders,
        cancelled_orders=cancelled_orders,

        # dessert studio
        quoted_requests=quoted_requests,
        converted_requests=converted_requests,

        # product intelligence
        top_products=top_products,
        top_product_revenue=top_product_revenue,
        top_favourites=top_favourites,
        vip_customers=vip_customers,
        average_order_value=average_order_value,
        heatmap=heatmap,
        insights=insights,

        # charts
        revenue_chart_labels=revenue_chart_labels,
        collected_chart_values=collected_chart_values,
        pending_chart_values=pending_chart_values,
        revenue_growth=revenue_growth,
        product_chart_labels=product_chart_labels,
        product_chart_values=product_chart_values,
        status_chart_values=status_chart_values,

        # dessert studio intelligence
        average_budget=average_budget,
        accepted_quotes=accepted_quotes,
        rejected_quotes=rejected_quotes,
        pending_quote_responses=pending_quote_responses,
        studio_success_rate=studio_success_rate,

        # health
        health_score=health_score,
        health_status=health_status,
        cancellation_rate=cancellation_rate,
        delivery_rate=delivery_rate,
        conversion_rate=conversion_rate,
        quote_acceptance_rate=quote_acceptance_rate,
        forecast_revenue=forecast_revenue,

        # flavours & occasions
        top_flavours=top_flavours,
        top_occasions=top_occasions,

        # FIX #4: reset state
        reset_at=reset_cutoff,
        reset_by=(reset_row.reset_by if reset_row else None),

        admin_username=session.get("admin_username"),
        admin_role=session.get("admin_role")
    )


# =========================================
# RESET ANALYTICS  (FIX #4)
# =========================================
# Does NOT delete any Order / CustomOrder rows — those are real
# customer + business records (order history, invoices, "My
# Orders", reorder, accounting). Instead this inserts a new
# AnalyticsReset checkpoint, and analytics_dashboard() above only
# counts orders placed after the most recent checkpoint. The
# dashboard genuinely "starts fresh from today" without destroying
# any real data.

@admin_analytics_bp.route("/admin/analytics/reset", methods=["POST"])
@admin_required
def reset_analytics():

    entry = AnalyticsReset(
        reset_at=datetime.utcnow(),
        reset_by=session.get("admin_username")
    )

    db.session.add(entry)
    db.session.commit()

    flash(
        "📊 Analytics dashboard reset! Now showing fresh stats from today. "
        "Your real orders and order history are completely safe and untouched.",
        "success"
    )

    return redirect(url_for("admin_analytics.analytics_dashboard"))
