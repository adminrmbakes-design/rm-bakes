from datetime import datetime

from database import db



# =========================================
# ORDER MODEL
# =========================================

class Order(db.Model):

    
    __tablename__ = "orders"



    # =====================================
    # PRIMARY KEY
    # =====================================

    order_id = db.Column(

        db.Integer,

        primary_key=True

    )



    # =====================================
    # USER INFO SNAPSHOT
    # =====================================

    user_id = db.Column(

        db.Integer,

        nullable=False

    )



    username = db.Column(

        db.String(120),

        nullable=False

    )



    email = db.Column(

        db.String(150),

        nullable=False

    )



    full_name = db.Column(

        db.String(150)

    )



    phone_number = db.Column(

        db.String(30)

    )



    # =====================================
    # DELIVERY DETAILS SNAPSHOT
    # =====================================

    delivery_address = db.Column(

        db.Text

    )



    landmark = db.Column(

        db.String(255)

    )



    city = db.Column(

        db.String(120)

    )



    pincode = db.Column(

        db.String(20)

    )



    google_maps_link = db.Column(

        db.Text

    )



    # =====================================
    # PAYMENT
    # =====================================

    payment_method = db.Column(

        db.String(50),

        default="Cash on Delivery"

    )



    payment_status = db.Column(

        db.String(50),

        default="pending"

    )



    # =====================================
    # ORDER DETAILS
    # =====================================

    order_number = db.Column(

        db.String(100),

        unique=True,

        nullable=False

    )



    order_status = db.Column(

        db.String(50),

        default="queued"

    )



    # =====================================
    # ORDER SOURCE
    # =====================================

    order_source = db.Column(

        db.String(50),

        nullable=False,

        default="menu_order"

    )



    # =====================================
    # CUSTOM ORDER LINKAGE
    # =====================================

    custom_order_id = db.Column(

        db.Integer,

        nullable=True

    )



    custom_request_code = db.Column(

        db.String(50),

        nullable=True

    )



    # =====================================
    # CUSTOM DESSERT DETAILS
    # =====================================

    custom_dessert_category = db.Column(

        db.String(120),

        nullable=True

    )



    custom_flavor = db.Column(

        db.String(120),

        nullable=True

    )



    custom_quantity = db.Column(

        db.String(120),

        nullable=True

    )



    custom_description = db.Column(

        db.Text,

        nullable=True

    )



    custom_message = db.Column(

        db.Text,

        nullable=True

    )



    custom_special_notes = db.Column(

        db.Text,

        nullable=True

    )



    custom_inspiration_image = db.Column(

        db.Text,

        nullable=True

    )



    # =====================================
    # CONVERSION METADATA
    # =====================================

    converted_from_dessert_studio = db.Column(

        db.Boolean,

        default=False

    )



    production_started_at = db.Column(

        db.DateTime,

        nullable=True

    )



    # =====================================
    # PRODUCTS JSON
    # =====================================

    products_json = db.Column(

        db.Text,

        nullable=False,

        default="[]"

    )



    # =====================================
    # TOTALS
    # =====================================

    subtotal = db.Column(

        db.Float,

        default=0

    )



    delivery_fee = db.Column(

        db.Float,

        default=40

    )

    discount_amount = db.Column(

        db.Float,
   
        default=0

    )
    
    coupon_code = db.Column(
   
        db.String(100),
    
        nullable=True

    )



    grand_total = db.Column(

        db.Float,

        default=0

    )



    total_amount = db.Column(

        db.Float,

        default=0

    )



    # =====================================
    # TIMESTAMPS
    # =====================================

    created_at = db.Column(

        db.DateTime,

        default=datetime.utcnow

    )



    ordered_at = db.Column(

        db.DateTime,

        default=datetime.utcnow

    )



    production_started_at = db.Column(

        db.DateTime,

        nullable=True

    )



    cancelled_at = db.Column(

        db.DateTime,

        nullable=True

    )



    delivered_at = db.Column(

        db.DateTime,

        nullable=True

    )



    # =====================================
    # ORDER FLAGS
    # =====================================

    is_cancelled = db.Column(

        db.Boolean,

        default=False

    )



    is_delivered = db.Column(

        db.Boolean,

        default=False

    )



    # =====================================
    # REVIEW REMINDER
    # =====================================

    review_reminder_sent = db.Column(

        db.Boolean,

        default=False

    )

    
    review_remind_at = db.Column(

        db.DateTime,

        nullable=True

    )



    # =====================================
    # OPTIONAL INTERNAL NOTES
    # =====================================

    admin_notes = db.Column(

        db.Text,

        nullable=True

    )

    # =========================================
    # PAYMENT INFORMATION
    # =========================================

    payment_status = db.Column(

        db.String(30),

        default="Pending"

    )

    payment_verified = db.Column(

        db.Boolean,

        default=False

    )


    payment_gateway = db.Column(

        db.String(30),

        default="None"

    )


    payment_mode = db.Column(

        db.String(50)

    )

    payment_completed_at = db.Column(

        db.DateTime

    )


    razorpay_order_id = db.Column(

        db.String(100)

    )


    razorpay_payment_id = db.Column(

        db.String(100)

    )


    transaction_reference = db.Column(

        db.String(100)

    )

    payment_failure_reason = db.Column(

        db.Text

    )

    # =====================================
    # HELPER PROPERTY
    # =====================================

    @property
    def is_custom_order(self):

        return (

            self.order_source == "custom_order"

            or

            self.converted_from_dessert_studio

        )


# =========================================
# ORDER EXPERIENCE FEEDBACK
# =========================================

class OrderFeedback(db.Model):

    __tablename__ = "order_feedbacks"

    feedback_id = db.Column(

        db.Integer,

        primary_key=True

    )

    # =====================================
    # ORDER
    # =====================================

    order_id = db.Column(

        db.Integer,

        nullable=False

    )

    order_number = db.Column(

        db.String(100),

        nullable=False

    )

    is_custom_order = db.Column(

        db.Boolean,

        default=False

    )

    # =====================================
    # CUSTOMER
    # =====================================

    customer_id = db.Column(

        db.Integer,

        nullable=False

    )

    customer_name = db.Column(

        db.String(150),

        nullable=False

    )

    # =====================================
    # EXPERIENCE
    # =====================================

    overall_rating = db.Column(

        db.Integer,

        nullable=False

    )

    # =====================================
    # TIMESTAMP
    # =====================================

    created_at = db.Column(

        db.DateTime,

        default=datetime.utcnow

    )


# =========================================
# PRODUCT REVIEWS
# =========================================

class ProductReview(db.Model):

    __tablename__ = "product_reviews"

    review_id = db.Column(

        db.Integer,

        primary_key=True

    )

    # =====================================
    # ORDER
    # =====================================

    order_id = db.Column(

        db.Integer,

        nullable=False

    )

    order_number = db.Column(

        db.String(100),

        nullable=False

    )

    is_custom_order = db.Column(

        db.Boolean,

        default=False

    )

    # =====================================
    # PRODUCT
    # =====================================

    product_id = db.Column(

        db.Integer,

        nullable=True

    )

    product_name = db.Column(

        db.String(200),

        nullable=False

    )

    # =====================================
    # CUSTOMER
    # =====================================

    customer_id = db.Column(

        db.Integer,

        nullable=False

    )

    customer_name = db.Column(

        db.String(150),

        nullable=False

    )

    # =====================================
    # REVIEW
    # =====================================

    rating = db.Column(

        db.Integer,

        nullable=False

    )

    review_text = db.Column(

        db.Text

    )

    review_image = db.Column(

        db.String(500)

    )


    # =====================================
    # ADMIN REPLY
    # =====================================

    admin_reply = db.Column(

        db.Text,

        nullable=True

    )
    
    reply_by = db.Column(

        db.String(100),

        nullable=True

    )

    reply_date = db.Column(

        db.DateTime,

        nullable=True

    )

    # =====================================
    # MODERATION
    # =====================================

    is_visible = db.Column(

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
