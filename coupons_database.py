from datetime import datetime

from database import db


# =========================================
# COUPONS
# =========================================

class Coupon(db.Model):

    __tablename__ = "coupons"

    # =====================================
    # PRIMARY KEY
    # =====================================

    coupon_id = db.Column(

        db.Integer,

        primary_key=True

    )

    # =====================================
    # BASIC INFO
    # =====================================

    coupon_code = db.Column(

        db.String(100),

        unique=True,

        nullable=False

    )

    coupon_title = db.Column(

        db.String(200),

        nullable=False

    )

    coupon_description = db.Column(

        db.Text,

        nullable=True

    )

    # =====================================
    # DISCOUNT
    # =====================================

    discount_type = db.Column(

        db.String(50),

        nullable=False

    )
    # fixed_amount
    # percentage

    discount_value = db.Column(

        db.Float,

        nullable=False

    )

    # =====================================
    # SCOPE
    # =====================================

    scope = db.Column(

        db.String(50),

        default="cart"

    )
    # cart
    # product
    # category

    target_product = db.Column(

        db.String(200),

        nullable=True

    )

    target_category = db.Column(

        db.String(200),

        nullable=True

    )

    # =====================================
    # LIMITS
    # =====================================

    minimum_order_amount = db.Column(

        db.Float,

        default=0

    )

    maximum_discount = db.Column(

        db.Float,

        nullable=True

    )

    usage_limit = db.Column(

        db.Integer,

        nullable=True

    )

    times_used = db.Column(

        db.Integer,

        default=0

    )

    # =====================================
    # STATUS
    # =====================================

    expiry_date = db.Column(

        db.DateTime,

        nullable=True

    )

    is_active = db.Column(

        db.Boolean,

        default=True

    )

    # =====================================
    # TIMESTAMP
    # =====================================

    created_at = db.Column(

        db.DateTime,

        default=datetime.utcnow

    )


    # ====================================
    # Optimal text 
    # ====================================

  
    popularity_text = db.Column(
        
        db.String(255),

        nullable=True

    )

    # ========================
    # BANNER IMAGE
    # ========================
    
    coupon_banner = db.Column(
        
        db.String(500),

        nullable=False

    )


# =========================================
# COUPON USAGE HISTORY
# =========================================

class CouponUsage(db.Model):

    __tablename__ = "coupon_usages"

    # =====================================
    # PRIMARY KEY
    # =====================================

    usage_id = db.Column(

        db.Integer,

        primary_key=True

    )

    # =====================================
    # COUPON
    # =====================================

    coupon_id = db.Column(

        db.Integer,

        nullable=False

    )

    coupon_code = db.Column(

        db.String(100),

        nullable=False

    )

    # =====================================
    # USER
    # =====================================

    user_id = db.Column(

        db.Integer,

        nullable=False

    )

    # =====================================
    # ORDER
    # =====================================

    order_id = db.Column(

        db.Integer,

        nullable=False

    )

    # =====================================
    # DISCOUNT SNAPSHOT
    # =====================================

    discount_amount = db.Column(

        db.Float,

        default=0

    )

    # =====================================
    # TIMESTAMP
    # =====================================

    used_at = db.Column(

        db.DateTime,

        default=datetime.utcnow

    )
