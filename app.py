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
def inject_notification_count():

    unread_notifications_count = 0

    if current_user.is_authenticated:

        unread_notifications_count = (

            UserNotification.query.filter_by(

                user_id=current_user.user_id,

                is_read=False,

                is_cleared=False

            ).count()

        )

    return dict(

        unread_notifications_count=
            unread_notifications_count

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
