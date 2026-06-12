from flask import Flask
from flask_login import LoginManager
from flask_login import current_user

import os

# =========================================
# DATABASE
# =========================================

from database import db
from database import User
from database import UserNotification
from database import CouponUsage

# Coupon database
from coupons_database import *

# =========================================
# ORDER MODELS
# =========================================

from orders_database import Order
from orders_database import (
    OrderFeedback,
    ProductReview
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

# =========================================
# CREATE APP
# =========================================

app = Flask(__name__)

# =========================================
# SECRET KEY
# =========================================

app.config[
    "SECRET_KEY"
] = "rm_bakes_secret_key"

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


# =========================================
# CREATE DATABASE TABLES
# =========================================

from sqlalchemy import text

with app.app_context():

    db.create_all()

    try:

        db.session.execute(text("""
            ALTER TABLE global_notifications
            ADD COLUMN notification_type VARCHAR(50)
            DEFAULT 'announcement'
        """))

        print("✅ notification_type added")

    except Exception as e:

        print("⏭ notification_type exists")

    try:

        db.session.execute(text("""
            ALTER TABLE global_notifications
            ADD COLUMN action_text VARCHAR(100)
        """))

        print("✅ action_text added")

    except Exception:

        print("⏭ action_text exists")

    try:

        db.session.execute(text("""
            ALTER TABLE global_notifications
            ADD COLUMN action_link VARCHAR(300)
        """))

        print("✅ action_link added")

    except Exception:

        print("⏭ action_link exists")

    try:

        db.session.execute(text("""
            ALTER TABLE global_notifications
            ADD COLUMN product_id INTEGER
        """))

        print("✅ product_id added")

    except Exception:

        print("⏭ product_id exists")

    try:

        db.session.execute(text("""
            ALTER TABLE global_notifications
            ADD COLUMN coupon_code VARCHAR(100)
        """))

        print("✅ coupon_code added")

    except Exception:

        print("⏭ coupon_code exists")

    try:

        db.session.execute(text("""
            ALTER TABLE global_notifications
            ADD COLUMN priority INTEGER DEFAULT 0
        """))

        print("✅ priority added")

    except Exception:

        print("⏭ priority exists")

    try:

        db.session.execute(text("""
            ALTER TABLE global_notifications
            ADD COLUMN starts_at TIMESTAMP
        """))

        print("✅ starts_at added")

    except Exception:

        print("⏭ starts_at exists")

    try:

        db.session.execute(text("""
            ALTER TABLE global_notifications
            ADD COLUMN expires_at TIMESTAMP
        """))

        print("✅ expires_at added")

    except Exception:

        print("⏭ expires_at exists")

    try:

        db.session.execute(text("""
            ALTER TABLE global_notifications
            ADD COLUMN is_featured BOOLEAN DEFAULT FALSE
        """))

        print("✅ is_featured added")

    except Exception:

        print("⏭ is_featured exists")

    db.session.commit()

    print("🚀 GlobalNotification migration complete")


# =========================================
# RUN APP
# =========================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True

    )
