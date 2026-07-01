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

    try:

        data = request.get_json()


        current_user.full_name = data.get(
            "full_name",
            ""
        )

        current_user.phone_number = data.get(
            "phone_number",
            ""
        )

        current_user.delivery_address = data.get(
            "delivery_address",
            ""
        )

        current_user.landmark = data.get(
            "landmark",
            ""
        )

        current_user.city = data.get(
            "city",
            ""
        )

        current_user.pincode = data.get(
            "pincode",
            ""
        )

        current_user.google_maps_link = data.get(
            "google_maps_link",
            ""
        )

        current_user.preferred_payment_method = data.get(
            "preferred_payment_method",
            "Online"
        )


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
            "Failed to save profile details",

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
