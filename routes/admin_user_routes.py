"""
ADMIN USER ROUTES — RM Bakes
Implements the "Customer Network" User Management module that lives
behind the admin dashboard's Customer Network card.

Covers:
  - Full customer/administrator listing with live search, filters,
    sorting and pagination (all handled client-side in admin_users.html
    so the table never needs a page reload).
  - A statistics dashboard summarising the customer base.
  - A per-customer details page with order history and analytics.
  - Soft delete / recover, with administrator-protection rules.

Nothing in this file ever issues a DELETE query — accounts are only
ever flagged with is_deleted, so orders, payments, notifications,
reviews, coupons and carts always stay intact.

Gated behind the "customer_network" platform feature (see
utils/feature_manager.py) — if it's ever set to COMING_SOON or
DISABLED from /site-settings, these routes respond exactly like
every other feature-gated admin module (Analytics, Broadcast, etc).
"""

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from datetime import datetime

from sqlalchemy import func

from database import (
    db,
    User,
    UserNotification,
    CouponUsage
)

from orders_database import Order

from utils.admin_guard import admin_required

from utils.notification_utils import create_admin_notification

from utils.feature_manager import feature_gate


# =========================================
# BLUEPRINT
# =========================================

admin_user_bp = Blueprint(
    "admin_user",
    __name__
)


# =========================================
# HELPERS
# =========================================

def _build_user_activity_maps():
    """
    Aggregates order / notification / coupon activity for EVERY user
    in a handful of grouped queries, instead of running a separate
    query per user on the listing page (keeps the table fast no
    matter how many customers RM Bakes has).
    """

    order_counts = dict(
        db.session.query(
            Order.user_id,
            func.count(Order.order_id)
        ).group_by(Order.user_id).all()
    )

    # Lifetime spending only counts orders that weren't cancelled —
    # a cancelled order never became real revenue.
    order_spend = dict(
        db.session.query(
            Order.user_id,
            func.sum(Order.grand_total)
        ).filter(
            Order.is_cancelled.is_(False)
        ).group_by(Order.user_id).all()
    )

    last_order_dates = dict(
        db.session.query(
            Order.user_id,
            func.max(Order.created_at)
        ).filter(
            Order.is_cancelled.is_(False)
        ).group_by(Order.user_id).all()
    )

    notification_counts = dict(
        db.session.query(
            UserNotification.user_id,
            func.count(UserNotification.notification_id)
        ).group_by(UserNotification.user_id).all()
    )

    coupon_counts = dict(
        db.session.query(
            CouponUsage.user_id,
            func.count(CouponUsage.usage_id)
        ).group_by(CouponUsage.user_id).all()
    )

    return {
        "orders": order_counts,
        "spend": order_spend,
        "last_order": last_order_dates,
        "notifications": notification_counts,
        "coupons": coupon_counts
    }


def _annotate_user(user, activity):
    """
    Attaches computed, read-only display fields onto a User row for
    the template to render. Nothing here touches the database.
    """

    user.total_orders = activity["orders"].get(user.user_id, 0)

    user.lifetime_spending = round(
        activity["spend"].get(user.user_id) or 0,
        2
    )

    user.last_order_at = activity["last_order"].get(user.user_id)

    user.notification_count = activity["notifications"].get(
        user.user_id, 0
    )

    user.coupon_usage_count = activity["coupons"].get(
        user.user_id, 0
    )

    user.account_status = "deleted" if user.is_deleted else "active"

    return user


def _other_active_admin_exists(user_id):
    """True if there is at least one OTHER active administrator."""

    return User.query.filter(
        User.is_admin.is_(True),
        User.is_deleted.is_(False),
        User.user_id != user_id
    ).count() > 0


def _safe_redirect_target(fallback_endpoint):
    """
    Only ever redirects to an internal path supplied by our own forms
    (never trusts an arbitrary external URL) — same pattern already
    used for the ?next= redirects in auth_routes.py.
    """

    candidate = request.form.get("redirect_to", "")

    if candidate and candidate.startswith("/"):
        return candidate

    return url_for(fallback_endpoint)


# =========================================
# USER MANAGEMENT — LISTING + STATISTICS
# =========================================

@admin_user_bp.route(
    "/admin/users"
)
@admin_required
@feature_gate("customer_network")
def admin_users():

    users = User.query.order_by(
        User.user_id.desc()
    ).all()

    activity = _build_user_activity_maps()

    for user in users:
        _annotate_user(user, activity)

    # =====================================
    # STATISTICS DASHBOARD
    # =====================================

    total_users = len(users)
    active_users = len([u for u in users if not u.is_deleted])
    deleted_users = len([u for u in users if u.is_deleted])
    admin_count = len([u for u in users if u.is_admin])
    customer_count = total_users - admin_count

    today = datetime.utcnow()

    new_this_month = len([
        u for u in users
        if u.created_at
        and u.created_at.year == today.year
        and u.created_at.month == today.month
    ])

    returning_customers = len([
        u for u in users if u.total_orders > 1
    ])

    total_revenue = round(
        sum(u.lifetime_spending for u in users),
        2
    )

    return render_template(

        "admin/admin_users.html",

        users=users,

        total_users=total_users,
        active_users=active_users,
        deleted_users=deleted_users,
        admin_count=admin_count,
        customer_count=customer_count,
        new_this_month=new_this_month,
        returning_customers=returning_customers,
        total_revenue=total_revenue,

        initial_filter=request.args.get("filter", "all"),

        admin_username=session.get("admin_username"),

        admin_role=session.get("admin_role")

    )


# =========================================
# USER DETAILS PAGE
# =========================================

@admin_user_bp.route(
    "/admin/users/<int:user_id>"
)
@admin_required
@feature_gate("customer_network")
def admin_user_details(user_id):

    user = User.query.get_or_404(user_id)

    orders = (
        Order.query
        .filter_by(user_id=user.user_id)
        .order_by(Order.created_at.desc())
        .all()
    )

    active_orders = [
        order for order in orders if not order.is_cancelled
    ]

    total_orders = len(orders)

    total_spending = round(
        sum(order.grand_total or 0 for order in active_orders),
        2
    )

    average_order_value = round(
        total_spending / len(active_orders),
        2
    ) if active_orders else 0

    highest_order_value = round(
        max(
            (order.grand_total or 0 for order in active_orders),
            default=0
        ),
        2
    )

    # active_orders is already newest-first, so the first entry
    # (if any) is the most recent non-cancelled purchase.
    last_purchase_date = (
        active_orders[0].created_at if active_orders else None
    )

    days_since_last_login = None

    if user.last_login:
        days_since_last_login = (
            datetime.utcnow() - user.last_login
        ).days

    notification_count = UserNotification.query.filter_by(
        user_id=user.user_id
    ).count()

    coupon_usage_count = CouponUsage.query.filter_by(
        user_id=user.user_id
    ).count()

    can_delete = (
        not user.is_admin
        or _other_active_admin_exists(user.user_id)
    )

    return render_template(

        "admin/admin_user_details.html",

        user=user,

        recent_orders=orders[:10],

        total_orders=total_orders,
        total_spending=total_spending,
        average_order_value=average_order_value,
        highest_order_value=highest_order_value,
        last_purchase_date=last_purchase_date,
        days_since_last_login=days_since_last_login,
        notification_count=notification_count,
        coupon_usage_count=coupon_usage_count,

        is_self=(session.get("admin_id") == user.user_id),
        can_delete=can_delete,

        admin_username=session.get("admin_username"),

        admin_role=session.get("admin_role")

    )


# =========================================
# SOFT DELETE (DEACTIVATE) A USER
# =========================================

@admin_user_bp.route(
    "/admin/users/<int:user_id>/delete",

    methods=["POST"]
)
@admin_required
@feature_gate("customer_network")
def admin_delete_user(user_id):

    target_user = User.query.get_or_404(user_id)

    redirect_to = _safe_redirect_target("admin_user.admin_users")

    # =====================================
    # PROTECTED ACCOUNT (never deactivatable)
    # =====================================

    if user_id == 1:

        flash(
            "Access Denied for this account!",
            "danger"
        )

        return redirect(redirect_to)

    # =====================================
    # ALREADY DEACTIVATED
    # =====================================

    if target_user.is_deleted:

        flash(
            "This account is already deactivated 🚫",
            "warning"
        )

        return redirect(redirect_to)

    # =====================================
    # CANNOT DEACTIVATE YOUR OWN ACCOUNT
    # =====================================

    if target_user.user_id == session.get("admin_id"):

        flash(
            "You can't deactivate your own admin account 🔒",
            "danger"
        )

        return redirect(redirect_to)

    # =====================================
    # CANNOT DEACTIVATE THE FINAL ADMIN
    # =====================================

    if target_user.is_admin and not _other_active_admin_exists(
        target_user.user_id
    ):

        flash(
            "You can't deactivate the final administrator account 🔒",
            "danger"
        )

        return redirect(redirect_to)

    # =====================================
    # SOFT DELETE — ONLY is_deleted CHANGES
    # Orders, payments, notifications, reviews,
    # coupons and cart rows are all left untouched.
    # =====================================

    target_user.is_deleted = True

    db.session.commit()

    create_admin_notification(

        title="Customer Account Deactivated",

        message=(
            f"\nAdministrator:\n{session.get('admin_username')}\n\n"
            f"deactivated the account for:\n{target_user.username} "
            f"({target_user.email})\n"
        ),

        notification_type="admin"

    )

    flash(
        f"{target_user.username}'s account has been deactivated 😭 "
        f"They can no longer log in until it's recovered.",
        "success"
    )

    return redirect(redirect_to)


# =========================================
# RECOVER A DEACTIVATED USER
# =========================================

@admin_user_bp.route(
    "/admin/users/<int:user_id>/recover",

    methods=["POST"]
)
@admin_required
@feature_gate("customer_network")
def admin_recover_user(user_id):

    target_user = User.query.get_or_404(user_id)

    redirect_to = _safe_redirect_target("admin_user.admin_users")

    # =====================================
    # ALREADY ACTIVE
    # =====================================

    if not target_user.is_deleted:

        flash(
            "This account is already active ✓",
            "warning"
        )

        return redirect(redirect_to)

    # =====================================
    # RECOVER — ONLY is_deleted CHANGES
    # =====================================

    target_user.is_deleted = False

    db.session.commit()

    create_admin_notification(

        title="Customer Account Recovered",

        message=(
            f"\nAdministrator:\n{session.get('admin_username')}\n\n"
            f"recovered the account for:\n{target_user.username} "
            f"({target_user.email})\n"
        ),

        notification_type="admin"

    )

    flash(
        f"{target_user.username}'s account has been recovered ✨",
        "success"
    )

    return redirect(redirect_to)
