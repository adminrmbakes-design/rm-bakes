from datetime import datetime

import random
import string



# =========================================
# DATABASE
# =========================================

from database import db



# =========================================
# REQUEST CODE GENERATOR
# =========================================

def generate_request_code():

    random_part = ''.join(

        random.choices(

            string.ascii_uppercase + string.digits,

            k=6

        )

    )



    return f"RMCS-{random_part}"



# =========================================
# CUSTOM ORDER MODEL
# =========================================

class CustomOrder(db.Model):

    

    __tablename__ = "custom_orders"



    # =====================================
    # PRIMARY KEY
    # =====================================

    custom_order_id = db.Column(

        db.Integer,

        primary_key=True

    )



    # =====================================
    # USER INFO
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



    # =====================================
    # TRACKING
    # =====================================

    request_code = db.Column(

        db.String(20),

        unique=True,

        nullable=False,

        default=generate_request_code

    )



    # =====================================
    # DESSERT DETAILS
    # =====================================

    dessert_category = db.Column(

        db.String(100),

        nullable=False

    )



    flavor = db.Column(

        db.String(120),

        nullable=False

    )



    quantity = db.Column(

        db.String(80),

        nullable=False

    )



    occasion = db.Column(

        db.String(120),

        nullable=True

    )



    # =====================================
    # CUSTOMER REQUEST
    # =====================================

    description = db.Column(

        db.Text,

        nullable=False

    )



    custom_message = db.Column(

        db.String(300),

        nullable=True

    )



    special_notes = db.Column(

        db.Text,

        nullable=True

    )



    # =====================================
    # IMAGE
    # =====================================

    inspiration_image = db.Column(

        db.String(300),

        nullable=True

    )



    # =====================================
    # DELIVERY & BUDGET
    # =====================================

    budget = db.Column(

        db.Float,

        nullable=True

    )



    delivery_date = db.Column(

        db.Date,

        nullable=True

    )



    # =====================================
    # ADMIN REVIEW
    # =====================================

    status = db.Column(

        db.String(50),

        nullable=False,

        default="pending"

    )
    
    
    # =====================================
    # NEW MASTER WORKFLOW STATE
    # =====================================

    custom_status = db.Column(

        db.String(80),

        nullable=False,

        default="pending"

    )



    # =====================================
    # PROFILE SNAPSHOT
    # =====================================

    full_name = db.Column(

        db.String(150),

        nullable=True

    )



    phone_number = db.Column(

        db.String(30),

        nullable=True

    )



    delivery_address = db.Column(

        db.Text,

        nullable=True

    )



    landmark = db.Column(

        db.String(255),

        nullable=True

    )



    city = db.Column(

        db.String(120),

        nullable=True

    )



    pincode = db.Column(

        db.String(20),

        nullable=True

    )



    google_maps_link = db.Column(

        db.Text,

        nullable=True

    )



    # =====================================
    # PROFILE SNAPSHOT TRACKING
    # =====================================

    profile_snapshot_updated_at = db.Column(

        db.DateTime,

        nullable=True

    )



    # =====================================
    # CANCELLATION SYSTEM
    # =====================================

    cancel_requested = db.Column(

        db.Boolean,

        default=False

    )



    cancel_reason = db.Column(

        db.Text,

        nullable=True

    )



    cancel_requested_at = db.Column(

        db.DateTime,

        nullable=True

    )



    cancel_reviewed_at = db.Column(

        db.DateTime,

        nullable=True

    )



    cancel_reviewed_by = db.Column(

        db.String(120),

        nullable=True

    )



    # =====================================
    # PRODUCTION CONVERSION
    # =====================================

    converted_main_order_id = db.Column(

        db.Integer,

        nullable=True

    )



    converted_at = db.Column(

        db.DateTime,

        nullable=True

    )



    admin_price = db.Column(

        db.Float,

        nullable=True

    )



    admin_notes = db.Column(

        db.Text,

        nullable=True

    )



    # =====================================
    # CUSTOMER QUOTE RESPONSE
    # =====================================

    customer_response = db.Column(

        db.String(50),

        nullable=False,

        default="pending"

    )



    customer_response_note = db.Column(

        db.Text,

        nullable=True

    )



    quote_responded_at = db.Column(

        db.DateTime,

        nullable=True

    )



    # =====================================
    # CONVERSION TRACKING
    # =====================================

    converted_to_main_order = db.Column(

        db.Boolean,

        default=False

    )



    main_order_id = db.Column(

        db.Integer,

        nullable=True

    )



    # =====================================
    # CUSTOMER APPROVAL
    # =====================================

    is_customer_approved = db.Column(

        db.Boolean,

        default=False

    )



    # =====================================
    # CONVERTED TO REAL ORDER
    # =====================================

    converted_to_order = db.Column(

        db.Boolean,

        default=False

    )



    # =====================================
    # TIMESTAMPS
    # =====================================

    created_at = db.Column(

        db.DateTime,

        default=datetime.utcnow

    )



    updated_at = db.Column(

        db.DateTime,

        default=datetime.utcnow,

        onupdate=datetime.utcnow

    )



    # =====================================
    # TIMELINE RELATIONSHIP
    # =====================================

    timeline_events = db.relationship(

        "CustomOrderTimeline",

        backref="custom_order",

        lazy=True,

        cascade="all, delete-orphan",

        order_by="CustomOrderTimeline.created_at.asc()"

    )



    # =====================================
    # REPRESENTATION
    # =====================================

    def __repr__(self):

        return (

            f"<CustomOrder "

            f"{self.request_code}>"

        )



# =========================================
# CUSTOM ORDER TIMELINE
# =========================================

class CustomOrderTimeline(db.Model):



    __tablename__ = "custom_order_timeline"



    # =====================================
    # PRIMARY KEY
    # =====================================

    timeline_id = db.Column(

        db.Integer,

        primary_key=True

    )



    # =====================================
    # RELATIONSHIP
    # =====================================

    custom_order_id = db.Column(

        db.Integer,

        db.ForeignKey(

            "custom_orders.custom_order_id"

        ),

        nullable=False

    )



    # =====================================
    # EVENT INFO
    # =====================================

    event_type = db.Column(

        db.String(100),

        nullable=False

    )



    title = db.Column(

        db.String(200),

        nullable=False

    )



    description = db.Column(

        db.Text,

        nullable=True

    )



    # =====================================
    # EVENT SOURCE
    # =====================================

    triggered_by = db.Column(

        db.String(50),

        nullable=False

    )



    # =====================================
    # TIMESTAMP
    # =====================================

    created_at = db.Column(

        db.DateTime,

        default=datetime.utcnow

    )



    # =====================================
    # REPRESENTATION
    # =====================================

    def __repr__(self):

        return (

            f"<TimelineEvent "

            f"{self.event_type}>"

        )
