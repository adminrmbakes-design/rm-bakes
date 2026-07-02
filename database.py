from flask_sqlalchemy import SQLAlchemy

from flask_login import UserMixin

from datetime import datetime



# =========================================
# DATABASE
# =========================================

db = SQLAlchemy()



# =========================================
# USER MODEL
# =========================================

class User(UserMixin, db.Model):

    __tablename__ = "users"



    user_id = db.Column(

        db.Integer,

        primary_key=True

    )



    username = db.Column(

        db.String(100),

        unique=True,

        nullable=False

    )



    email = db.Column(

        db.String(120),

        unique=True,

        nullable=False

    )



    password = db.Column(

        db.String(300),

        nullable=False

    )



    # =====================================
    # ADMIN
    # =====================================

    is_admin = db.Column(

        db.Boolean,

        default=False

    )



    admin_role = db.Column(

        db.String(50),

        nullable=True

    )



    admin_last_login = db.Column(

        db.DateTime,

        nullable=True

    )



    # =====================================
    # PROFILE
    # =====================================

    full_name = db.Column(

        db.String(120)

    )



    phone_number = db.Column(

        db.String(20)

    )



    delivery_address = db.Column(

        db.Text

    )



    landmark = db.Column(

        db.String(200)

    )



    city = db.Column(

        db.String(100)

    )



    pincode = db.Column(

        db.String(10)

    )



    google_maps_link = db.Column(

        db.Text

    )



    preferred_payment_method = db.Column(

        db.String(50),

        default="Online"

    )



    is_deleted = db.Column(

        db.Boolean,

        default=False

    )



    # =====================================
    # RELATIONSHIP
    # =====================================

    cart_items = db.relationship(

        "Cart",

        backref="user",

        lazy=True,

        cascade="all, delete-orphan"

    )



    # =====================================
    # FLASK LOGIN
    # =====================================

    def get_id(self):

        return str(self.user_id)



# =========================================
# PRODUCT MODEL
# =========================================

class Product(db.Model):

    __tablename__ = "products"



    product_id = db.Column(

        db.Integer,

        primary_key=True

    )



    product_name = db.Column(

        db.String(200),

        nullable=False

    )



    product_description = db.Column(

        db.Text,

        nullable=False

    )



    product_price = db.Column(

        db.Float,

        nullable=False

    )



    product_unit = db.Column(

        db.String(50),

        nullable=False

    )



    product_image = db.Column(

        db.String(300)

    )



    product_tags = db.Column(

        db.String(300)

    )



    product_category = db.Column(

        db.String(100),

        default="cakes"

    )
    
    # =====================================
    # PRODUCT MARKETING FLAGS
    # =====================================

    product_is_launching = db.Column(
        
        db.Boolean,

        default=False

    )

    product_is_seasonal = db.Column(

        db.Boolean,

        default=False

    )

    product_is_festive = db.Column(

        db.Boolean,

        default=False

    )


# ========================================
# FEATURED PRODUCTS
# ========================================

class FeaturedProduct(db.Model):

    __tablename__ = "featured_products"

    featured_id = db.Column(
        db.Integer,
        primary_key=True
    )

    slot_number = db.Column(
        db.Integer,
        unique=True,
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "products.product_id"
        ),
        nullable=True
    )

    featured_label = db.Column(

        db.String(100),

        default="👑 Signature Pick"

    )

    product = db.relationship(
        "Product",
        lazy=True
    )



# =========================================
# CART MODEL
# =========================================

class Cart(db.Model):

    __tablename__ = "cart"



    cart_id = db.Column(

        db.Integer,

        primary_key=True

    )



    user_id = db.Column(

        db.Integer,

        db.ForeignKey("users.user_id"),

        nullable=False

    )



    product_id = db.Column(

        db.Integer,

        db.ForeignKey("products.product_id"),

        nullable=False

    )



    product_quantity = db.Column(

        db.Integer,

        default=1

    )



    note = db.Column(

        db.Text

    )



    # =====================================
    # RELATIONSHIP
    # =====================================

    product = db.relationship(

        "Product",

        backref="cart_items",

        lazy=True

    )


class AdminNotification(db.Model):

    __tablename__ = "admin_notifications"



    notification_id = db.Column(

        db.Integer,

        primary_key=True

    )



    title = db.Column(

        db.String(200),

        nullable=False

    )



    message = db.Column(

        db.Text,

        nullable=False

    )



    notification_type = db.Column(

        db.String(50),

        nullable=False,

        default="info"

    )



    is_read = db.Column(

        db.Boolean,

        default=False

    )



    created_at = db.Column(

        db.DateTime,

        default=datetime.utcnow

    )
    
    
    
# =========================================
# HELPERS
# =========================================

# ========================================
# FEATURED PRODUCT SLOTS
# ========================================

def create_featured_product_slots():

    try:

        existing_slots = {

            slot.slot_number

            for slot in

            FeaturedProduct.query.all()

        }

        for slot_number in range(1,7):

            if slot_number not in existing_slots:

                db.session.add(

                    FeaturedProduct(

                        slot_number=slot_number

                    )

                )

        db.session.commit()

        print(
            "featured slots ready ✅"
        )

    except Exception as e:

        print(
            f"featured slot error: {e}"
        )


def get_featured_products():

    featured_slots = (

        FeaturedProduct.query

        .filter(
            FeaturedProduct.product_id.isnot(None)
        )

        .order_by(
            FeaturedProduct.slot_number
        )

        .all()

    )

    featured_products = []

    for slot in featured_slots:

        product = Product.query.get(
            slot.product_id
        )

        if product:

            featured_products.append(
                product
            )

    return featured_products


def get_products_by_category(category):

    return Product.query.filter_by(

        product_category=category

    ).all()



def search_products(query):

    return Product.query.filter(

        Product.product_name.ilike(
            f"%{query}%"
        )

    ).all()


# =========================================
# ACTIVE CAROUSELS
# =========================================

def get_active_carousels():

    return (

        Carousel.query

        .filter_by(
            carousel_is_active=True
        )

        .order_by(
            Carousel.carousel_priority.desc(),
            Carousel.carousel_created_at.desc()
        )

        .all()

    )
    
    
# =========================================
# USER NOTIFICATIONS
# =========================================

class UserNotification(db.Model):

    __tablename__ = "user_notifications"



    notification_id = db.Column(

        db.Integer,

        primary_key=True

    )



    user_id = db.Column(

        db.Integer,

        db.ForeignKey("users.user_id"),

        nullable=False

    )



    title = db.Column(

        db.String(200),

        nullable=False

    )



    message = db.Column(

        db.Text,

        nullable=False

    )



    notification_type = db.Column(

        db.String(50),

        nullable=False,

        default="info"

    )



    # =====================================
    # ORDER LINKING
    # =====================================

    order_id = db.Column(

        db.Integer,

        nullable=True

    )



    custom_order_id = db.Column(

        db.Integer,

        nullable=True

    )



    notification_category = db.Column(

        db.String(50),

        nullable=False,

        default="order"

    )



    is_read = db.Column(

        db.Boolean,

        default=False

    )



    is_cleared = db.Column(

        db.Boolean,

        default=False

    )



    created_at = db.Column(

        db.DateTime,

        default=datetime.utcnow

    )
    
    
    
    
    
# =========================================
# GLOBAL NOTIFICATIONS
# =========================================

class GlobalNotification(db.Model):

    __tablename__ = "global_notifications"

    notification_id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    banner_image = db.Column(
        db.String(300),
        nullable=False
    )

    # =====================================
    # FUTURE-PROOF FIELDS
    # =====================================

    notification_type = db.Column(
        db.String(50),
        default="announcement"
    )

    action_text = db.Column(
        db.String(100),
        nullable=True
    )

    action_link = db.Column(
        db.String(300),
        nullable=True
    )

    product_id = db.Column(
        db.Integer,
        nullable=True
    )

    coupon_code = db.Column(
        db.String(100),
        nullable=True
    )

    priority = db.Column(
        db.Integer,
        default=0
    )

    starts_at = db.Column(
        db.DateTime,
        nullable=True
    )

    expires_at = db.Column(
        db.DateTime,
        nullable=True
    )

    is_featured = db.Column(
        db.Boolean,
        default=False
    )

    is_active = db.Column(
        db.Boolean,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# =========================================
# HOMEPAGE CAROUSEL
# =========================================

class Carousel(db.Model):

    __tablename__ = "carousel"

    carousel_id = db.Column(
        db.Integer,
        primary_key=True
    )

    carousel_title = db.Column(
        db.String(200),
        nullable=False
    )

    carousel_description = db.Column(
        db.Text,
        nullable=True
    )

    carousel_banner_image = db.Column(
        db.String(500),
        nullable=False
    )

    carousel_category = db.Column(
        db.String(50),
        nullable=False,
        default="announcement"
    )

    carousel_visibility = db.Column(
        db.String(50),
        nullable=False,
        default="home_only"
    )

    carousel_action_text = db.Column(
        db.String(100),
        nullable=True
    )

    carousel_action_link = db.Column(
        db.String(500),
        nullable=True
    )

    carousel_priority = db.Column(
        db.Integer,
        default=0
    )

    carousel_starts_at = db.Column(
        db.DateTime,
        nullable=True
    )

    carousel_expires_at = db.Column(
        db.DateTime,
        nullable=True
    )

    carousel_is_active = db.Column(
        db.Boolean,
        default=True
    )

    carousel_created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
    
    
# =========================================
# FAVOURITES MODEL
# =========================================

class Favourite(db.Model):

    __tablename__ = "favourites"



    favourite_id = db.Column(

        db.Integer,

        primary_key=True

    )



    user_id = db.Column(

        db.Integer,

        db.ForeignKey("users.user_id"),

        nullable=False

    )



    product_id = db.Column(

        db.Integer,

        db.ForeignKey("products.product_id"),

        nullable=False

    )



    created_at = db.Column(

        db.DateTime,

        default=datetime.utcnow

    )


    # =====================================
    # RELATIONSHIP
    # =====================================

    product = db.relationship(

        "Product",

        backref="favourites",

        lazy=True

    )


# =========================================
# COUPON USAGE
# =========================================

class CouponUsage(db.Model):

    __tablename__ = "coupon_usage"

    usage_id = db.Column(

        db.Integer,

        primary_key=True

    )

    user_id = db.Column(

        db.Integer,

        db.ForeignKey(
            "users.user_id"
        ),

        nullable=False

    )

    coupon_code = db.Column(

        db.String(100),

        nullable=False

    )

    used_at = db.Column(

        db.DateTime,

        default=datetime.utcnow

    )
