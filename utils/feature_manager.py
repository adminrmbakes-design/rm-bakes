from functools import wraps

from flask import (

    render_template,
    abort,
    request

)

from database import (

    db,
    SiteFeature

)


# =========================================
# STATUS CONSTANTS
# =========================================

STATUS_LIVE = "LIVE"
STATUS_COMING_SOON = "COMING_SOON"
STATUS_DISABLED = "DISABLED"

VALID_STATUSES = [

    STATUS_LIVE,
    STATUS_COMING_SOON,
    STATUS_DISABLED

]


# =========================================
# TWO-STATE FEATURES
# =========================================
# A small number of features don't make sense as "Coming Soon" — they
# only ever need Live/Disabled. The dashboard renders a 2-option
# dropdown for these, and update_feature_status() rejects COMING_SOON
# if it's ever submitted for one of these anyway (defense in depth).

TWO_STATE_FEATURE_KEYS = [

    "full_webpage"

]


# =========================================
# DEFAULT FEATURE DEFINITIONS
# (feature_key, feature_name, description)
#
# Adding a new controllable feature later only
# requires one new tuple here (auto-seeded on
# next app start) plus one helper/gate call at
# the route that should be protected.
# =========================================

DEFAULT_FEATURES = [

    (
        "custom_orders",
        "Custom Orders",
        "Dessert Studio — lets customers request bespoke custom desserts."
    ),

    (
        "global_notifications",
        "Global Notifications",
        "Customer-facing notification centre showing announcements and order updates."
    ),

    (
        "forgot_password",
        "Forgot Password",
        "Self-service password reset flow for customer accounts."
    ),

    (
        "guest_cart",
        "Guest Cart",
        "Allows shoppers to build a cart before creating an account."
    ),

    (
        "payments",
        "Payments",
        "Razorpay online payment processing during checkout."
    ),

    (
        "cafe_notifications",
        "Cafe Notifications",
        "Internal live alert feed used by RM Bakes staff."
    ),

    (
        "analytics",
        "Analytics",
        "Admin analytics dashboard covering revenue, orders, and trends."
    ),

    (
        "broadcast",
        "Broadcast Messages",
        "Admin tool for publishing site-wide announcements to customers."
    ),

    (
        "customer_network",
        "Customer Network",
        "Admin User Management — view, search, and soft delete/recover customer and administrator accounts."
    ),

    (
        "dark_mode",
        "Dark Mode",
        "The light/dark theme toggle shown in the navbar and Account Settings."
    ),

    (
        "full_webpage",
        "Full Webpage",
        "Master switch for the entire storefront. Disabling this takes the whole site down for maintenance — only /site-settings stays reachable."
    ),

]


# =========================================
# SEED DEFAULTS
# =========================================

def ensure_default_features():
    """Populate the SiteFeature table with defaults for any feature_key
    that doesn't already have a row. Safe to call on every app start."""

    try:

        existing_keys = {

            feature.feature_key
            for feature in SiteFeature.query.all()

        }

        created_any = False

        for feature_key, feature_name, description in DEFAULT_FEATURES:

            if feature_key not in existing_keys:

                db.session.add(

                    SiteFeature(

                        feature_key=feature_key,
                        feature_name=feature_name,
                        description=description,
                        status=STATUS_LIVE

                    )

                )

                created_any = True

        if created_any:

            db.session.commit()

    except Exception as error:

        db.session.rollback()

        print(f"site feature seed error: {error}")


# =========================================
# STATUS LOOKUP
# =========================================

def get_feature(feature_key):
    """Return the SiteFeature row for a key, or None if it doesn't exist yet."""

    return SiteFeature.query.filter_by(

        feature_key=feature_key

    ).first()


def get_feature_status(feature_key):
    """Return the current status string for a feature_key.
    Defaults to LIVE if the feature has no row yet, so an unrecognised
    or not-yet-seeded key never accidentally blocks a route."""

    feature = get_feature(feature_key)

    if not feature:

        return STATUS_LIVE

    return feature.status


def is_feature_live(feature_key):

    return get_feature_status(feature_key) == STATUS_LIVE


def is_feature_disabled(feature_key):

    return get_feature_status(feature_key) == STATUS_DISABLED


def is_feature_coming_soon(feature_key):

    return get_feature_status(feature_key) == STATUS_COMING_SOON


# =========================================
# STANDARD ROUTE GATE
# =========================================
#
# Covers the common 3-state pattern used by most protected features:
#   LIVE         -> run the view normally
#   COMING_SOON  -> render feature_status.html
#   DISABLED     -> 404
#
# guest_cart and payments do NOT use this decorator — their spec calls
# for bespoke behaviour (redirect-to-login / friendly JSON error) and
# that logic lives inline in their own routes, calling the helpers
# above directly. This keeps feature_manager.py the single source of
# truth for STATUS while letting response shape stay route-specific.
# =========================================

def feature_gate(feature_key):

    def decorator(route_function):

        @wraps(route_function)
        def wrapper(*args, **kwargs):

            feature = get_feature(feature_key)

            status = feature.status if feature else STATUS_LIVE

            if status == STATUS_DISABLED:

                abort(404)

            if status == STATUS_COMING_SOON:

                # Admin-facing features (analytics, cafe_notifications,
                # broadcast) should look like the admin panel, not the
                # customer site suddenly appearing inside it.
                template_name = (
                    "site_settings/feature_status_admin.html"
                    if request.path.startswith("/admin")
                    else "site_settings/feature_status.html"
                )

                return render_template(

                    template_name,

                    feature_name=(
                        feature.feature_name if feature else feature_key
                    ),

                    description=(
                        feature.description if feature else ""
                    )

                )

            return route_function(*args, **kwargs)

        return wrapper

    return decorator
