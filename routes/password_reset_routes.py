from flask import (

    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session

)

from werkzeug.security import (

    generate_password_hash,
    check_password_hash

)

from datetime import datetime

from database import (

    db,
    User

)

from utils.email_sender import (

    send_email

)

from utils.otp_generator import (

    generate_otp,
    generate_otp_expiry,
    is_otp_expired

)

import re



# =========================================
# BLUEPRINT
# =========================================

password_reset_bp = Blueprint(

    "password_reset",
    __name__

)



# =========================================
# PASSWORD VALIDATION
# =========================================

def validate_password(password):

    """
    Password Rules:

    - Minimum 8 characters
    - One uppercase
    - One lowercase
    - One number
    - One special character
    """

    if len(password) < 8:

        return (

            False,

            "Password must contain at least 8 characters"

        )



    if not re.search(r"[A-Z]", password):

        return (

            False,

            "Password must contain at least one uppercase letter"

        )



    if not re.search(r"[a-z]", password):

        return (

            False,

            "Password must contain at least one lowercase letter"

        )



    if not re.search(r"[0-9]", password):

        return (

            False,

            "Password must contain at least one number"

        )



    if not re.search(

        r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]",

        password

    ):

        return (

            False,

            "Password must contain at least one special character"

        )



    return (

        True,

        "Valid password"

    )



# =========================================
# FORGOT PASSWORD
# =========================================

@password_reset_bp.route(

    "/forgot-password",

    methods=["GET", "POST"]

)
def forgot_password():

    if request.method == "POST":

        email = request.form.get(
            "email"
        )



        if not email:

            flash(

                "Email is required",

                "danger"

            )



            return redirect(

                url_for(
                    "password_reset.forgot_password"
                )

            )



        user = User.query.filter_by(

            email=email

        ).first()



        # =================================
        # SECURITY FRIENDLY RESPONSE
        # =================================

        if not user:

            flash(

                "If the email exists, an OTP has been sent ✨",

                "info"

            )



            return redirect(

                url_for(
                    "password_reset.forgot_password"
                )

            )



        # =================================
        # GENERATE OTP
        # =================================

        generated_otp = generate_otp()



        otp_expiry = generate_otp_expiry(

            5

        )



        # =================================
        # STORE SESSION
        # =================================

        session[
            "reset_email"
        ] = email



        session[
            "reset_otp"
        ] = generated_otp



        session[
            "reset_otp_expiry"
        ] = otp_expiry.isoformat()



        session[
            "reset_verified"
        ] = False



        # =================================
        # SEND EMAIL
        # =================================

        email_sent = send_email(

            receiver_email=email,

            subject="RM Bakes Password Reset OTP",

            body=f"""

RM Bakes Password Recovery

Your OTP is:

{generated_otp}

This OTP expires in 5 minutes.

If you did not request this,
please ignore this email.

"""

        )



        if not email_sent:

            flash(

                "Failed to send OTP email",

                "danger"

            )



            return redirect(

                url_for(
                    "password_reset.forgot_password"
                )

            )



        flash(

            "OTP sent successfully 📩",

            "success"

        )



        return redirect(

            url_for(
                "password_reset.verify_reset_otp"
            )

        )



    return render_template(

        "forgot_password.html"

    )



# =========================================
# VERIFY RESET OTP
# =========================================

@password_reset_bp.route(

    "/verify-reset-otp",

    methods=["GET", "POST"]

)
def verify_reset_otp():

    reset_email = session.get(
        "reset_email"
    )



    if not reset_email:

        return redirect(

            url_for(
                "password_reset.forgot_password"
            )

        )



    if request.method == "POST":

        entered_otp = request.form.get(
            "otp"
        )



        stored_otp = session.get(
            "reset_otp"
        )



        stored_expiry = session.get(
            "reset_otp_expiry"
        )



        if not stored_expiry:

            flash(

                "OTP session expired",

                "danger"

            )



            return redirect(

                url_for(
                    "password_reset.forgot_password"
                )

            )



        expiry_datetime = datetime.fromisoformat(

            stored_expiry

        )



        # =================================
        # OTP EXPIRED
        # =================================

        if is_otp_expired(

            expiry_datetime

        ):

            session.pop(
                "reset_otp",
                None
            )



            session.pop(
                "reset_otp_expiry",
                None
            )



            flash(

                "OTP expired",

                "danger"

            )



            return redirect(

                url_for(
                    "password_reset.forgot_password"
                )

            )



        # =================================
        # INVALID OTP
        # =================================

        if entered_otp != stored_otp:

            flash(

                "Invalid OTP",

                "danger"

            )



            return redirect(

                url_for(
                    "password_reset.verify_reset_otp"
                )

            )



        # =================================
        # VERIFIED
        # =================================

        session[
            "reset_verified"
        ] = True



        flash(

            "OTP verified successfully ✨",

            "success"

        )



        return redirect(

            url_for(
                "password_reset.reset_password"
            )

        )



    return render_template(

        "verify_reset_otp.html"

    )



# =========================================
# RESET PASSWORD
# =========================================

@password_reset_bp.route(

    "/reset-password",

    methods=["GET", "POST"]

)
def reset_password():

    reset_verified = session.get(
        "reset_verified"
    )



    reset_email = session.get(
        "reset_email"
    )



    if not reset_verified or not reset_email:

        return redirect(

            url_for(
                "password_reset.forgot_password"
            )

        )



    if request.method == "POST":

        password = request.form.get(
            "password"
        )



        confirm_password = request.form.get(
            "confirm_password"
        )



        # =================================
        # REQUIRED
        # =================================

        if not password or not confirm_password:

            flash(

                "All fields are required",

                "danger"

            )



            return redirect(

                url_for(
                    "password_reset.reset_password"
                )

            )



        # =================================
        # MATCH CHECK
        # =================================

        if password != confirm_password:

            flash(

                "Passwords do not match",

                "danger"

            )



            return redirect(

                url_for(
                    "password_reset.reset_password"
                )

            )



        # =================================
        # PASSWORD RULES
        # =================================

        valid_password, validation_message = validate_password(

            password

        )



        if not valid_password:

            flash(

                validation_message,

                "danger"

            )



            return redirect(

                url_for(
                    "password_reset.reset_password"
                )

            )



        user = User.query.filter_by(

            email=reset_email

        ).first()



        if not user:

            flash(

                "User not found",

                "danger"

            )



            return redirect(

                url_for(
                    "password_reset.forgot_password"
                )

            )



        # =================================
        # PREVENT SAME PASSWORD REUSE
        # =================================

        same_password = check_password_hash(

            user.password,
            password

        )



        if same_password:

            flash(

                "New password cannot be same as old password",

                "danger"

            )



            return redirect(

                url_for(
                    "password_reset.reset_password"
                )

            )



        # =================================
        # UPDATE PASSWORD
        # =================================

        hashed_password = generate_password_hash(

            password

        )



        user.password = hashed_password



        db.session.commit()



        # =================================
        # CLEAR SESSION
        # =================================

        session.pop(
            "reset_email",
            None
        )



        session.pop(
            "reset_otp",
            None
        )



        session.pop(
            "reset_otp_expiry",
            None
        )



        session.pop(
            "reset_verified",
            None
        )



        # =================================
        # SUCCESS
        # =================================

        flash(

            "Password reset successful 🎉",

            "success"

        )



        return redirect(

            url_for(
                "auth.login"
            )

        )



    return render_template(

        "reset_password.html"

    )



# =========================================
# RESEND RESET OTP
# =========================================

@password_reset_bp.route(

    "/resend-reset-otp"

)
def resend_reset_otp():

    reset_email = session.get(
        "reset_email"
    )



    if not reset_email:

        return redirect(

            url_for(
                "password_reset.forgot_password"
            )

        )



    # =====================================
    # GENERATE NEW OTP
    # =====================================

    generated_otp = generate_otp()



    otp_expiry = generate_otp_expiry(

        5

    )



    session[
        "reset_otp"
    ] = generated_otp



    session[
        "reset_otp_expiry"
    ] = otp_expiry.isoformat()



    # =====================================
    # SEND EMAIL
    # =====================================

    email_sent = send_email(

        receiver_email=reset_email,

        subject="RM Bakes Password Reset OTP",

        body=f"""

RM Bakes Password Recovery

Your new OTP is:

{generated_otp}

This OTP expires in 5 minutes.

"""

    )



    if not email_sent:

        flash(

            "Failed to resend OTP",

            "danger"

        )



        return redirect(

            url_for(
                "password_reset.verify_reset_otp"
            )

        )



    flash(

        "New OTP sent successfully 📩",

        "success"

    )



    return redirect(

        url_for(
            "password_reset.verify_reset_otp"
        )

    )