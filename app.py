from flask import Flask

from flask_login import LoginManager

from flask_login import current_user

from database import UserNotification

# =========================================
# DATABASE
# =========================================

from database import db
from database import User


# =========================================
# ORDER MODELS
# =========================================

from orders_database import Order



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


# =========================================
# CREATE APP
# =========================================

app = Flask(__name__)


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
# CONFIGURATION
# =========================================

app.config["SECRET_KEY"] = "rm_bakes_secret_key"



# =========================================
# MAIN DATABASE
# =========================================

app.config["SQLALCHEMY_DATABASE_URI"] = (

    "sqlite:///rm_database.db"

)



# =========================================
# SECOND DATABASE
# =========================================

import os



BASE_DIR = os.path.abspath(
    os.path.dirname(__file__)
)



INSTANCE_DIR = os.path.join(
    BASE_DIR,
    "instance"
)



# =====================================
# CREATE INSTANCE FOLDER
# =====================================

os.makedirs(
    INSTANCE_DIR,
    exist_ok=True
)



# =====================================
# DATABASE PATHS
# =====================================

main_db_path = os.path.join(
    INSTANCE_DIR,
    "rm_database.db"
)



orders_db_path = os.path.join(
    INSTANCE_DIR,
    "orders.db"
)



# =====================================
# SQLALCHEMY CONFIG
# =====================================

app.config[
    "SQLALCHEMY_DATABASE_URI"
] = f"sqlite:///{main_db_path}"



app.config[
    "SQLALCHEMY_BINDS"
] = {

    "orders":
        f"sqlite:///{orders_db_path}",

    "custom_orders":
        f"sqlite:///{os.path.join(INSTANCE_DIR, 'custom_orders.db')}"

}



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

    return User.query.get(int(user_id))



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


# =========================================
# CREATE DATABASES
# =========================================

with app.app_context():

    db.create_all()

    db.create_all(bind_key="orders")

    db.create_all(bind_key="custom_orders")
    



# =========================================
# RUN APP
# =========================================

if __name__ == "__main__":

    app.run(

        debug=True

    )
