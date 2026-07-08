import re

from flask import Blueprint
from flask import render_template
from flask import request
from flask import jsonify
from flask import redirect
from flask import url_for

from flask_login import login_required
from flask_login import current_user
from flask_login import logout_user

from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

from database import db
from database import User


profile_bp = Blueprint(
    "profile",
    __name__
)



# =========================================
# PROFILE SAVE — VALIDATION RULES
# =========================================

PHONE_REGEX = re.compile(r"^[6-9]\d{9}$")

PINCODE_REGEX = re.compile(r"^[1-9]\d{5}$")

PAYMENT_METHODS = (
    "Online",
    "Cash On Delivery"
)

# Max length is capped to comfortably fit the matching
# database.py column so a long paste never raises a DB error.
FIELD_MAX_LENGTHS = {

    "full_name": 120,

    "landmark": 200,

    "city": 100,

    "delivery_address": 1000,

    "google_maps_link": 500

}

FIELD_LABELS = {

    "full_name": "Full name",

    "phone_number": "Phone number",

    "delivery_address": "Delivery address",

    "landmark": "Landmark",

    "city": "City",

    "pincode": "Pincode",

    "google_maps_link": "Google Maps link"

}



# =========================================
# PROFILE PAGE
# =========================================

@profile_bp.route("/profile")
@login_required
def profile():

    return render_template(
        "profile.html",
        current_user=current_user
    )



# =========================================
# SAVE PROFILE DETAILS
# =========================================

@profile_bp.route(
    "/profile/save-details",
    methods=["POST"]
)
@login_required
def save_profile_details():

    data = request.get_json(silent=True)



    # =====================================
    # MALFORMED REQUEST
    # =====================================

    if data is None:

        return jsonify({

            "success": False,

            "message":
            "Invalid request — please refresh and try again 🔄"

        }), 400



    # =====================================
    # COLLECT TEXT FIELDS
    # Only a field that is actually present in the payload
    # gets touched. A blank/whitespace value is skipped rather
    # than saved, so an existing saved detail is never wiped
    # out by an empty field. (FIX #2)
    # =====================================

    text_fields = [
        "full_name",
        "phone_number",
        "delivery_address",
        "landmark",
        "city",
        "pincode",
        "google_maps_link"
    ]

    updates = {}

    for field in text_fields:

        if field in data:

            value = (data.get(field) or "").strip()

            if value:

                updates[field] = value



    # =====================================
    # PHONE NUMBER FORMAT
    # =====================================

    if (
        "phone_number" in updates and
        not PHONE_REGEX.match(updates["phone_number"])
    ):

        return jsonify({

            "success": False,

            "message":
            "Enter a valid 10-digit mobile number 📵"

        }), 400



    # =====================================
    # PINCODE FORMAT
    # =====================================

    if (
        "pincode" in updates and
        not PINCODE_REGEX.match(updates["pincode"])
    ):

        return jsonify({

            "success": False,

            "message":
            "Enter a valid 6-digit pincode 📍"

        }), 400



    # =====================================
    # GOOGLE MAPS LINK — ONLY ALLOW HTTP(S)
    # Anything else (e.g. a javascript: URI) could execute
    # when this link is later rendered as a clickable <a href>
    # on the checkout, order-details and admin pages.
    # =====================================

    if (
        "google_maps_link" in updates and
        not updates["google_maps_link"].lower().startswith(
            ("http://", "https://")
        )
    ):

        return jsonify({

            "success": False,

            "message":
            "Maps link must start with http:// or https:// 🔗"

        }), 400



    # =====================================
    # FIELD LENGTH LIMITS
    # =====================================

    for field, limit in FIELD_MAX_LENGTHS.items():

        if (
            field in updates and
            len(updates[field]) > limit
        ):

            return jsonify({

                "success": False,

                "message":
                f"{FIELD_LABELS[field]} is too long (max {limit} characters) 📏"

            }), 400



    # =====================================
    # PAYMENT METHOD
    # =====================================

    if "preferred_payment_method" in data:

        payment_method = (
            data.get("preferred_payment_method") or ""
        ).strip()

        if payment_method not in PAYMENT_METHODS:

            return jsonify({

                "success": False,

                "message":
                "Choose a valid payment method 💳"

            }), 400

        updates["preferred_payment_method"] = payment_method



    # =====================================
    # NOTHING TO SAVE
    # =====================================

    if not updates:

        return jsonify({

            "success": False,

            "message":
            "No changes to save 🤔"

        }), 400



    # =====================================
    # APPLY + COMMIT
    # =====================================

    try:

        for field, value in updates.items():

            setattr(current_user, field, value)


        db.session.commit()


        return jsonify({

            "success": True,

            "message":
            "Profile details saved successfully ✨"

        })


    except Exception as error:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message":
            "Failed to save profile details — please try again",

            "error": str(error)

        }), 500



# =========================================
# ACCOUNT SETTINGS PAGE
# =========================================

@profile_bp.route("/account-settings")
@login_required
def account_settings():

    return render_template(
        "account_settings.html"
    )



# =========================================
# CHANGE PASSWORD
# =========================================

@profile_bp.route(
    "/profile/change-password",
    methods=["POST"]
)
@login_required
def change_password():

    try:

        data = request.get_json()

        current_password = data.get(
            "current_password",
            ""
        )

        new_password = data.get(
            "new_password",
            ""
        )

        confirm_password = data.get(
            "confirm_password",
            ""
        )



        # =====================================
        # EMPTY CHECK
        # =====================================

        if (
            not current_password or
            not new_password or
            not confirm_password
        ):

            return jsonify({

                "success": False,

                "message":
                "Please fill all fields 😭"

            }), 400



        # =====================================
        # VERIFY OLD PASSWORD
        # =====================================

        if not check_password_hash(
            current_user.password,
            current_password
        ):

            return jsonify({

                "success": False,

                "message":
                "Current password is incorrect 🔐"

            }), 400



        # =====================================
        # CONFIRM PASSWORD
        # =====================================

        if new_password != confirm_password:

            return jsonify({

                "success": False,

                "message":
                "Passwords do not match 😭"

            }), 400



        # =====================================
        # PASSWORD LENGTH
        # =====================================

        if len(new_password) < 6:

            return jsonify({

                "success": False,

                "message":
                "Password must contain at least 6 characters"

            }), 400



        # =====================================
        # PREVENT SAME PASSWORD
        # =====================================

        if check_password_hash(
            current_user.password,
            new_password
        ):

            return jsonify({

                "success": False,

                "message":
                "New password cannot be same as old password 😭"

            }), 400



        # =====================================
        # UPDATE PASSWORD
        # =====================================

        current_user.password = generate_password_hash(
            new_password
        )



        db.session.commit()



        return jsonify({

            "success": True,

            "message":
            "Password updated successfully 🔐"

        })



    except Exception as error:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message":
            "Failed to update password",

            "error": str(error)

        }), 500



# =========================================
# FORGOT PASSWORD PLACEHOLDER
# =========================================

@profile_bp.route(
    "/profile/forgot-password",
    methods=["POST"]
)
def forgot_password():

    return jsonify({

        "success": True,

        "message":
        "Gmail OTP verification system coming soon 📧"

    })



# =========================================
# DELETE ACCOUNT (SOFT DELETE)
# =========================================

@profile_bp.route(
    "/profile/delete-account",
    methods=["POST"]
)
@login_required
def delete_account():

    try:

        data = request.get_json()

        password = data.get(
            "password",
            ""
        )



        # =====================================
        # VERIFY PASSWORD
        # =====================================

        if not check_password_hash(
            current_user.password,
            password
        ):

            return jsonify({

                "success": False,

                "message":
                "Incorrect password 😭"

            }), 400



        # =====================================
        # SOFT DELETE
        # =====================================

        current_user.is_deleted = True



        db.session.commit()



        logout_user()



        return jsonify({

            "success": True,

            "redirect":
            url_for("main.home"),

            "message":
            "Account deleted successfully 😭"

        })



    except Exception as error:

        db.session.rollback()

        return jsonify({

            "success": False,

            "message":
            "Failed to delete account",

            "error": str(error)

        }), 500
        
        
        
# =========================================
# VIEW ORDERS PLACEHOLDER
# =========================================
