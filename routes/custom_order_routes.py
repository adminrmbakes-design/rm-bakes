from flask import (

    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
    session

)

from flask_login import (

    login_required,
    current_user

)

from werkzeug.utils import secure_filename

from datetime import datetime

from database import db

from custom_orders_database import CustomOrder

from utils.admin_guard import admin_required

from utils.feature_manager import feature_gate

from utils.notification_utils import (

    create_admin_notification,
    create_user_notification

)

from utils.custom_order_timeline_utils import (

    create_timeline_event

)

from utils.custom_order_profile_utils import (

    validate_profile_before_custom_order,

    apply_profile_snapshot_to_custom_order

)

from utils.custom_order_constants import (

    CUSTOM_STATUS_PENDING,

    CUSTOMER_RESPONSE_PENDING

)

import os
import uuid
import cloudinary.uploader
import cloudinary_config



# =========================================
# BLUEPRINT
# =========================================

custom_order_bp = Blueprint(

    "custom_order",
    __name__

)



# =========================================
# UPLOAD FOLDER
# =========================================

UPLOAD_FOLDER = os.path.join(

    "static",
    "uploads",
    "custom_orders"

)



os.makedirs(

    UPLOAD_FOLDER,

    exist_ok=True

)



# =========================================
# ALLOWED IMAGE TYPES
# =========================================

ALLOWED_EXTENSIONS = {

    "png",
    "jpg",
    "jpeg",
    "webp"

}



# =========================================
# VALIDATE FILE
# =========================================

def allowed_file(filename):

    return (

        "." in filename

        and

        filename.rsplit(

            ".",

            1

        )[1].lower() in ALLOWED_EXTENSIONS

    )



# =========================================
# REQUEST CODE
# =========================================

def generate_request_code():

    return (

        "DS-"

        +

        str(uuid.uuid4())[:8].upper()

    )



# =========================================
# DESSERT STUDIO PAGE
# =========================================

@custom_order_bp.route(

    "/dessert-studio"

)

@login_required
@feature_gate("custom_orders")
def dessert_studio():

    return render_template(

        "custom_order.html"

    )



# =========================================
# SUBMIT CUSTOM ORDER
# =========================================

@custom_order_bp.route(

    "/submit-custom-order",

    methods=["POST"]

)

@login_required
@feature_gate("custom_orders")
def submit_custom_order():



    dessert_category = request.form.get(

        "dessert_category"

    )



    flavor = request.form.get(

        "flavor"

    )



    quantity = request.form.get(

        "quantity"

    )



    occasion = request.form.get(

        "occasion"

    )



    description = request.form.get(

        "description"

    )



    custom_message = request.form.get(

        "custom_message"

    )



    special_notes = request.form.get(

        "special_notes"

    )



    budget = request.form.get(

        "budget"

    )



    delivery_date = request.form.get(

        "delivery_date"

    )



    # =====================================
    # BASIC VALIDATION
    # =====================================

    if not dessert_category:



        flash(

            "Select dessert category 😭",

            "danger"

        )



        return redirect(

            url_for(

                "custom_order.dessert_studio"

            )

        )



    if not flavor:



        flash(

            "Flavor is required 😭",

            "danger"

        )



        return redirect(

            url_for(

                "custom_order.dessert_studio"

            )

        )



    if not quantity:



        flash(

            "Quantity is required 😭",

            "danger"

        )



        return redirect(

            url_for(

                "custom_order.dessert_studio"

            )

        )



    if not description:



        flash(

            "Describe your dream dessert 😭",

            "danger"

        )



        return redirect(

            url_for(

                "custom_order.dessert_studio"

            )

        )



    # =====================================
    # PROFILE VALIDATION
    # =====================================

    profile_validation = (

        validate_profile_before_custom_order(

            current_user

        )

    )



    if not profile_validation["success"]:



        flash(

            (

                "Please complete your profile "
                "before submitting a Dessert "
                "Studio request ✨"

            ),

            "warning"

        )



        return redirect(

            url_for(

                "profile.profile"

            )

        )



    # =====================================
    # IMAGE
    # =====================================

    uploaded_image_path = None



    image = request.files.get(

        "inspiration_image"

    )



    if image and image.filename != "":



        if allowed_file(image.filename):



            upload_result = cloudinary.uploader.upload(

                    image, folder="rm_bakes/custom_orders"

                    )

            uploaded_image_path = (

                    upload_result["secure_url"]

                    )



        else:



            flash(

                "Only PNG/JPG/JPEG/WEBP allowed 😭",

                "danger"

            )



            return redirect(

                url_for(

                    "custom_order.dessert_studio"

                )

            )



    # =====================================
    # DELIVERY DATE
    # =====================================

    parsed_delivery_date = None



    if delivery_date:



        try:



            parsed_delivery_date = datetime.strptime(

                delivery_date,

                "%Y-%m-%d"

            ).date()



        except Exception:



            flash(

                "Invalid delivery date 😭",

                "danger"

            )



            return redirect(

                url_for(

                    "custom_order.dessert_studio"

                )

            )
            
            
            # =====================================
    # BUDGET
    # =====================================

    parsed_budget = None



    if budget:



        try:



            parsed_budget = float(

                budget

            )



        except Exception:



            flash(

                "Invalid budget 😭",

                "danger"

            )



            return redirect(

                url_for(

                    "custom_order.dessert_studio"

                )

            )



    # =====================================
    # CREATE ORDER
    # =====================================

    new_custom_order = CustomOrder(

        user_id=current_user.user_id,

        username=current_user.username,

        email=current_user.email,

        request_code=generate_request_code(),

        dessert_category=dessert_category,

        flavor=flavor,

        quantity=quantity,

        occasion=occasion,

        description=description,

        custom_message=custom_message,

        special_notes=special_notes,

        inspiration_image=uploaded_image_path,

        budget=parsed_budget,

        delivery_date=parsed_delivery_date,



        # =================================
        # LEGACY STATUS
        # =================================

        status="pending",

        customer_response=CUSTOMER_RESPONSE_PENDING,



        # =================================
        # NEW MASTER STATUS
        # =================================

        custom_status=CUSTOM_STATUS_PENDING,



        created_at=datetime.utcnow()

    )



    # =====================================
    # APPLY PROFILE SNAPSHOT
    # =====================================

    apply_profile_snapshot_to_custom_order(

        new_custom_order,

        current_user

    )



    try:



        db.session.add(

            new_custom_order

        )



        db.session.commit()



        # =================================
        # TIMELINE
        # =================================

        create_timeline_event(

            custom_order_id=new_custom_order.custom_order_id,

            event_type="submitted",

            title="Dessert Request Submitted ✨",

            description=(

                "Your Dessert Studio request "
                "has been submitted successfully."

            ),

            triggered_by="customer"

        )



        # =================================
        # USER NOTIFICATION
        # =================================

        create_user_notification(

    user_id=current_user.user_id,

    title="Dessert Studio Request Submitted ✨",

    message=(

        "Your custom dessert request "
        "has been submitted successfully."

    ),

    notification_type="success",



    # =================================
    # CUSTOM ORDER LINKING
    # =================================

    custom_order_id=

        new_custom_order.custom_order_id,



    notification_category=

        "custom_order"

)



        # =================================
        # ADMIN NOTIFICATION
        # =================================

        create_admin_notification(

            title="New Dessert Studio Request 😭🔥",

            message=(

                f"{current_user.username} "
                f"submitted a Dessert Studio request."

            ),

            notification_type="info"

        )



        flash(

            "Dessert request submitted 😭🔥",

            "success"

        )



        return redirect(

            url_for(

                "custom_order.my_custom_orders"

            )

        )



    except Exception as error:



        db.session.rollback()



        print(

            "CUSTOM ORDER ERROR:",

            error

        )



        flash(

            "Couldn't submit request 😭",

            "danger"

        )



        return redirect(

            url_for(

                "custom_order.dessert_studio"

            )

        )



# =========================================
# USER CUSTOM ORDERS
# =========================================

@custom_order_bp.route(

    "/my-custom-orders"

)

@login_required
def my_custom_orders():



    custom_orders = (

        CustomOrder.query.filter_by(

            user_id=current_user.user_id

        )

        .order_by(

            CustomOrder.created_at.desc()

        )

        .all()

    )



    return render_template(

        "my_custom_orders.html",

        custom_orders=custom_orders

    )



# =========================================
# ADMIN CUSTOM ORDERS
# =========================================

@custom_order_bp.route(

    "/admin/custom-orders"

)

@admin_required
def admin_custom_orders():



    status_filter = request.args.get(

        "status",

        "all"

    )



    if status_filter == "all":



        custom_orders = (

            CustomOrder.query

            .order_by(

                CustomOrder.created_at.desc()

            )

            .all()

        )



    else:



        custom_orders = (

            CustomOrder.query.filter_by(

                status=status_filter

            )

            .order_by(

                CustomOrder.created_at.desc()

            )

            .all()

        )



    return render_template(

        "admin/admin_custom_orders.html",

        custom_orders=custom_orders,

        status_filter=status_filter,

        admin_username=session.get(

            "admin_username"

        )

    )
    
    
    # =========================================
# ACCEPT QUOTE
# =========================================

@custom_order_bp.route(

    "/accept-custom-quote/<int:custom_order_id>",

    methods=["POST"]

)

@login_required
def accept_custom_quote(

    custom_order_id

):



    custom_order = CustomOrder.query.get_or_404(

        custom_order_id

    )



    # =====================================
    # SECURITY
    # =====================================

    if custom_order.user_id != current_user.user_id:

        abort(403)



    if custom_order.status != "quoted":

        abort(403)



    if custom_order.customer_response != "pending":

        abort(403)



    # =====================================
    # UPDATE
    # =====================================

    custom_order.customer_response = "accepted"



    custom_order.is_customer_approved = True



    custom_order.quote_responded_at = (

        datetime.utcnow()

    )



    # =====================================
    # LEGACY STATUS
    # =====================================

    custom_order.status = "approved"



    # =====================================
    # NEW MASTER STATUS
    # =====================================

    custom_order.custom_status = (

        "quotation_accepted"

    )



    try:



        db.session.commit()



        # =================================
        # TIMELINE
        # =================================

        create_timeline_event(

            custom_order_id=custom_order.custom_order_id,

            event_type="customer_accepted",

            title="Quotation Accepted 😭🔥",

            description=(

                "Customer accepted the quotation."

            ),

            triggered_by="customer"

        )



        # =================================
        # ADMIN NOTIFICATION
        # =================================

        create_admin_notification(

            title="Quotation Accepted 😭🔥",

            message=(

                f"{current_user.username} accepted "
                f"the Dessert Studio quotation."

            ),

            notification_type="success"

        )



        # =================================
        # USER NOTIFICATION
        # =================================

        create_user_notification(

    user_id=current_user.user_id,

    title="Quotation Accepted ✨",

    message=(

        "You accepted the Dessert Studio quotation."

    ),

    notification_type="success",



    custom_order_id=

        custom_order.custom_order_id,



    notification_category=

        "custom_order"

)



        flash(

            "Quotation accepted 😭🔥",

            "success"

        )



    except Exception as error:



        db.session.rollback()



        print(

            "QUOTE ACCEPT ERROR:",

            error

        )



        flash(

            "Couldn't accept quotation 😭",

            "danger"

        )



    return redirect(

        url_for(

            "custom_order.my_custom_orders"

        )

    )



# =========================================
# REJECT QUOTE
# =========================================

@custom_order_bp.route(

    "/reject-custom-quote/<int:custom_order_id>",

    methods=["POST"]

)

@login_required
def reject_custom_quote(

    custom_order_id

):



    custom_order = CustomOrder.query.get_or_404(

        custom_order_id

    )



    # =====================================
    # SECURITY
    # =====================================

    if custom_order.user_id != current_user.user_id:

        abort(403)



    if custom_order.status != "quoted":

        abort(403)



    if custom_order.customer_response != "pending":

        abort(403)



    rejection_note = request.form.get(

        "rejection_note"

    )



    # =====================================
    # UPDATE
    # =====================================

    custom_order.customer_response = "rejected"



    custom_order.customer_response_note = (

        rejection_note

    )



    custom_order.quote_responded_at = (

        datetime.utcnow()

    )



    # =====================================
    # LEGACY STATUS
    # =====================================

    custom_order.status = "rejected"



    # =====================================
    # NEW MASTER STATUS
    # =====================================

    custom_order.custom_status = (

        "quotation_rejected"

    )



    try:



        db.session.commit()



        # =================================
        # TIMELINE
        # =================================

        create_timeline_event(

            custom_order_id=custom_order.custom_order_id,

            event_type="customer_rejected",

            title="Quotation Rejected",

            description=(

                "Customer rejected the quotation."

            ),

            triggered_by="customer"

        )



        # =================================
        # ADMIN NOTIFICATION
        # =================================

        create_admin_notification(

            title="Quotation Rejected",

            message=(

                f"{current_user.username} rejected "
                f"the Dessert Studio quotation."

            ),

            notification_type="warning"

        )



        # =================================
        # USER NOTIFICATION
        # =================================

        create_user_notification(

    user_id=current_user.user_id,

    title="Quotation Rejected",

    message=(

        "You rejected the Dessert Studio quotation."

    ),

    notification_type="warning",



    custom_order_id=

        custom_order.custom_order_id,



    notification_category=

        "custom_order"

)



        flash(

            "Quotation rejected.",

            "warning"

        )



    except Exception as error:



        db.session.rollback()



        print(

            "QUOTE REJECT ERROR:",

            error

        )



        flash(

            "Couldn't reject quotation 😭",

            "danger"

        )



    return redirect(

        url_for(

            "custom_order.my_custom_orders"

        )

    )



# =========================================
# UPDATE CUSTOM ORDER
# =========================================

@custom_order_bp.route(

    "/admin/update-custom-order/<int:custom_order_id>",

    methods=["POST"]

)

@admin_required
def update_custom_order(

    custom_order_id

):



    custom_order = CustomOrder.query.get_or_404(

        custom_order_id

    )



    status = request.form.get(

        "status"

    )



    admin_price = request.form.get(

        "admin_price"

    )



    admin_notes = request.form.get(

        "admin_notes"

    )



    allowed_statuses = [

        "pending",

        "reviewing",

        "quoted",

        "approved",

        "rejected"

    ]



    if status not in allowed_statuses:

        abort(403)



    # =====================================
    # LEGACY STATUS
    # =====================================

    custom_order.status = status



    # =====================================
    # NEW MASTER STATUS
    # =====================================

    if status == "pending":

        custom_order.custom_status = "pending"



    if status == "reviewing":

        custom_order.custom_status = "reviewing"



    if status == "quoted":

        custom_order.custom_status = "quoted"



    if status == "approved":

        custom_order.custom_status = (

            "quotation_accepted"

        )



    if status == "rejected":

        custom_order.custom_status = (

            "quotation_rejected"

        )



    # =====================================
    # PRICE
    # =====================================

    if admin_price:



        try:



            custom_order.admin_price = float(

                admin_price

            )



        except Exception:



            flash(

                "Invalid quotation 😭",

                "danger"

            )



            return redirect(

                url_for(

                    "custom_order.admin_custom_orders"

                )

            )



    else:

        custom_order.admin_price = None



    # =====================================
    # NOTES
    # =====================================

    custom_order.admin_notes = admin_notes



    custom_order.updated_at = datetime.utcnow()



    try:



        db.session.commit()



        # =================================
        # TIMELINE EVENTS
        # =================================

        if status == "reviewing":

            create_timeline_event(

                custom_order_id=custom_order.custom_order_id,

                event_type="reviewing",

                title="Dessert Request Under Review 👨‍🍳",

                description=(

                    "RM Bakes is reviewing your "
                    "custom dessert request."

                ),

                triggered_by="admin"

            )



        if status == "quoted":

            create_timeline_event(

                custom_order_id=custom_order.custom_order_id,

                event_type="quoted",

                title="Quotation Sent ✨",

                description=(

                    f"A quotation of ₹{custom_order.admin_price} "
                    f"has been provided."

                ),

                triggered_by="admin"

            )



        if status == "approved":

            create_timeline_event(

                custom_order_id=custom_order.custom_order_id,

                event_type="approved",

                title="Dessert Request Approved 🎂",

                description=(

                    "Your dessert request has "
                    "been approved successfully."

                ),

                triggered_by="admin"

            )



        if status == "rejected":

            create_timeline_event(

                custom_order_id=custom_order.custom_order_id,

                event_type="rejected",

                title="Dessert Request Rejected",

                description=(

                    "Your Dessert Studio request "
                    "was rejected."

                ),

                triggered_by="admin"

            )



        # =================================
        # USER NOTIFICATIONS
        # =================================

        if status == "reviewing":

            create_user_notification(

    user_id=custom_order.user_id,

    title="Dessert Request Under Review 👨‍🍳",

    message=(

        "Your Dessert Studio request "
        "is currently under review."

    ),

    notification_type="info",



    custom_order_id=

        custom_order.custom_order_id,



    notification_category=

        "custom_order"

)



        if status == "quoted":

            create_user_notification(

    user_id=custom_order.user_id,

    title="Quotation Received ✨",

    message=(

        f"Quotation for ₹{custom_order.admin_price} "
        f"is now available."

    ),

    notification_type="success",



    custom_order_id=

        custom_order.custom_order_id,



    notification_category=

        "custom_order"

)



        if status == "approved":

            create_user_notification(

    user_id=custom_order.user_id,

    title="Dessert Request Approved 🎂",

    message=(

        "Your Dessert Studio request "
        "has been approved."

    ),

    notification_type="success",



    custom_order_id=

        custom_order.custom_order_id,



    notification_category=

        "custom_order"

)



        if status == "rejected":

            create_user_notification(

    user_id=custom_order.user_id,

    title="Dessert Request Rejected",

    message=(

        "Your Dessert Studio request "
        "was rejected."

    ),

    notification_type="warning",



    custom_order_id=

        custom_order.custom_order_id,



    notification_category=

        "custom_order"

)



        flash(

            "Dessert request updated 😭🔥",

            "success"

        )



    except Exception as error:



        db.session.rollback()



        print(

            "CUSTOM ORDER UPDATE ERROR:",

            error

        )



        flash(

            "Couldn't update request 😭",

            "danger"

        )



    return redirect(

        url_for(

            "custom_order.admin_custom_orders"

        )

    )
    
    
# =========================================
# CUSTOM ORDER DETAILS
# =========================================

@custom_order_bp.route(

    "/custom-order/<int:custom_order_id>"

)

@login_required
def custom_order_details(

    custom_order_id

):



    # =====================================
    # FETCH ORDER
    # =====================================

    custom_order = CustomOrder.query.get_or_404(

        custom_order_id

    )



    # =====================================
    # SECURITY
    # =====================================

    if (

        custom_order.user_id != current_user.user_id

        and

        not current_user.is_admin

    ):

        abort(403)



    # =====================================
    # FETCH TIMELINE
    # =====================================

    timeline_events = (

        custom_order.timeline_events

        if hasattr(

            custom_order,

            "timeline_events"

        )

        else []

    )



    # =====================================
    # RENDER
    # =====================================

    return render_template(

        "custom_order_details.html",

        custom_order=custom_order,

        timeline_events=timeline_events

    )
