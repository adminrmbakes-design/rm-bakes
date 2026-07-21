from flask import Flask
from flask import request
from flask import render_template
from flask import session
from flask_login import LoginManager
from flask_login import current_user

import os

from datetime import timedelta

from sqlalchemy import text
from sqlalchemy import inspect

# =========================================
# DATABASE IMPORTS
# =========================================

from database import db
from database import User
from database import UserNotification
from database import CouponUsage
from database import Carousel
from database import SiteFeature
from database import create_featured_product_slots

# Coupon database
from coupons_database import *

# =========================================
# ORDER MODELS
# =========================================

from orders_database import Order
from orders_database import (
    OrderFeedback,
    ProductReview,
    AnalyticsReset
)

# =========================================
# CUSTOM ORDER MODELS
# =========================================

from custom_orders_database import (
    CustomOrder,
    CustomOrderTimeline
)

# =========================================
# ROUTES
# =========================================

from routes.auth_routes import auth_bp
from routes.main_routes import main_bp
from routes.product_routes import product_bp
from routes.cart_routes import cart_bp
from routes.profile_routes import profile_bp
from routes.checkout_routes import checkout_bp
from routes.order_routes import order_bp
from routes.admin_routes import admin_bp
from routes.notification_routes import notification_bp
from routes.password_reset_routes import password_reset_bp
from routes.custom_order_routes import custom_order_bp
from routes.custom_order_profile_routes import (custom_order_profile_bp)
from routes.custom_order_cancellation_routes import (custom_order_cancellation_bp)
from routes.custom_order_conversion_routes import (custom_order_conversion_bp)
from routes.favourite_routes import favourite_bp
from routes.admin_analytics_routes import (admin_analytics_bp)
from routes.admin_product_routes import (admin_product_bp)
from utils.image_helpers import (get_product_image)
from routes.review_routes import (review_bp)
from routes.admin_coupon_routes import (admin_coupon_bp)
from routes.admin_carousel_routes import (admin_carousel_bp)
from routes.admin_user_routes import (admin_user_bp)
from routes.site_settings_routes import (site_settings_bp)
from utils.feature_manager import (
    ensure_default_features,
    is_feature_live,
    is_feature_disabled,
    is_feature_coming_soon
)
from utils.timezone_utils import (
    to_ist,
    format_ist
)
from utils.monitoring_utils import (
    health
)

# =========================================
# CREATE APP
# =========================================

app = Flask(__name__)

# =========================================
# SECRET KEY
# =========================================

app.config[
    "SECRET_KEY"
] = os.getenv("SECRET_KEY", "rm_bakes_secret_key")

# =========================================
# SESSION / COOKIE PERSISTENCE
# =========================================
# Fixes: customers were being logged out any time they closed the
# browser, since sessions defaulted to browser-session-only cookies
# and login_user() never used Flask-Login's "remember me" cookie.
#
# Set FLASK_ENV=development in your local .env to disable Secure
# cookies for local HTTP testing — defaults to production-safe
# (Secure=True) otherwise, since this is what's deployed live.

IS_PRODUCTION = os.getenv("FLASK_ENV", "production").lower() != "development"

app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=365)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = IS_PRODUCTION

app.config["REMEMBER_COOKIE_DURATION"] = timedelta(days=365)
app.config["REMEMBER_COOKIE_HTTPONLY"] = True
app.config["REMEMBER_COOKIE_SAMESITE"] = "Lax"
app.config["REMEMBER_COOKIE_SECURE"] = IS_PRODUCTION


@app.before_request
def make_session_permanent():
    # Applies PERMANENT_SESSION_LIFETIME (365 days) to every session
    # cookie. Doesn't affect the admin / site-settings short-timeout
    # logic — those enforce their own expiry inside the session data
    # itself, independent of how long the underlying cookie lives.
    session.permanent = True

# =========================================
# DATABASE CONFIG
# =========================================

database_url = os.getenv(
    "DATABASE_URL"
)

if database_url.startswith(
    "postgres://"
):

    database_url = database_url.replace(

        "postgres://",
        "postgresql://",
        1

    )

app.config[
    "SQLALCHEMY_DATABASE_URI"
] = database_url

app.config[
    "SQLALCHEMY_TRACK_MODIFICATIONS"
] = False

# =========================================
# INITIALIZE DATABASE
# =========================================

db.init_app(app)

# =========================================
# LOGIN MANAGER
# =========================================

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = "auth.login"

@login_manager.user_loader
def load_user(user_id):

    return User.query.get(
        int(user_id)
    )

# =========================================
# GLOBAL NOTIFICATION COUNT
# =========================================

@app.context_processor
def notification_counts():

    from database import (
        UserNotification,
        GlobalNotification
    )

    if current_user.is_authenticated:

        count = (
            UserNotification.query.filter_by(
                user_id=current_user.user_id,
                is_read=False,
                is_cleared=False
            ).count()
        )

    else:

        count = (
            GlobalNotification.query.filter_by(
                is_active=True
            ).count()
        )

    return dict(
        notification_badge_count=count
    )

# =========================================
# REGISTER BLUEPRINTS
# =========================================

app.register_blueprint(main_bp)

app.register_blueprint(auth_bp)

app.register_blueprint(product_bp)

app.register_blueprint(cart_bp)

app.register_blueprint(profile_bp)

app.register_blueprint(checkout_bp)

app.register_blueprint(order_bp)

app.register_blueprint(admin_bp)

app.register_blueprint(notification_bp)

app.register_blueprint(password_reset_bp)

app.register_blueprint(custom_order_bp)

app.register_blueprint(custom_order_profile_bp)

app.register_blueprint(custom_order_cancellation_bp)

app.register_blueprint(custom_order_conversion_bp)

app.register_blueprint(favourite_bp)

app.register_blueprint(admin_analytics_bp)

app.register_blueprint(admin_product_bp)

app.jinja_env.globals.update(
    get_product_image=
    get_product_image
)

app.register_blueprint(review_bp)

app.register_blueprint(admin_coupon_bp)

app.register_blueprint(admin_carousel_bp)

app.register_blueprint(admin_user_bp)

# Not linked from the Admin Dashboard — reachable only by URL.
app.register_blueprint(site_settings_bp)

app.jinja_env.globals.update(
    is_feature_live=is_feature_live,
    is_feature_disabled=is_feature_disabled,
    is_feature_coming_soon=is_feature_coming_soon
)

# Every stored timestamp is UTC — this filter is the one place templates
# convert to IST for display: {{ order.created_at | ist }} or
# {{ order.created_at | ist('%d %b %Y') }} for a custom format.
app.jinja_env.filters["ist"] = format_ist
app.jinja_env.filters["to_ist"] = to_ist

# =========================================
# FULL SITE MAINTENANCE MODE
# =========================================
# When the "full_webpage" Platform Settings feature is DISABLED,
# every route shows the same friendly maintenance page — except
# /site-settings (so the owner can always turn it back on) and
# /static (so that page can still load its own CSS/fonts/images).

@app.before_request
def check_full_site_maintenance():

    if request.path.startswith("/site-settings"):
        return None

    if request.path.startswith("/static"):
        return None

    if is_feature_disabled("full_webpage"):

        return render_template(

            "site_settings/feature_status.html",

            feature_name="RM Bakes",

            description=None,

            custom_message=(
                "RM Bakes is currently taking a short break for some "
                "behind-the-scenes baking. We'll be back very soon — "
                "thank you for your patience! 🍰"
            ),

            is_full_site_maintenance=True

        ), 503

    return None


        
# =========================================
# CREATE DATABASE TABLES
# =========================================

with app.app_context():

    db.create_all()
        
    
# =========================================
# RUN APP
# =========================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True

    )
