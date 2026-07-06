from flask import (

    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash

)

from datetime import (

    datetime,
    timedelta

)

from werkzeug.security import (

    check_password_hash

)

from database import (

    db,
    User,
    SiteFeature

)

from utils.admin_guard import (

    site_settings_required,
    clear_site_settings_session

)

from utils.email_sender import (

    send_email

)

from utils.otp_generator import (

    generate_otp,
    generate_otp_expiry,
    is_otp_expired

)

from utils.feature_manager import (

    VALID_STATUSES,
    TWO_STATE_FEATURE_KEYS

)


# =========================================
# CONFIG
# =========================================
# Where the Platform Settings OTP is sent, and how long a verified
# session lasts. Named constants so both are easy to change later
# without touching the login flow itself.

SITE_SETTINGS_OTP_EMAIL = "admin.rmbakes@gmail.com"

SITE_SETTINGS_SESSION_MINUTES = 20


# =========================================
# BLUEPRINT
# =========================================
# Intentionally not linked from anywhere in the Admin Dashboard.
# Reachable only by someone who already knows this URL.

site_settings_bp = Blueprint(

    "site_settings",
    __name__

)


# =========================================
# LOGIN
# =========================================

@site_settings_bp.route(

    "/site-settings",

    methods=["GET", "POST"]

)
def site_settings_login():

    if request.method == "POST":

        username = request.form.get(
            "username"
        )

        password = request.form.get(
            "password"
        )



        owner_user = User.query.filter_by(

            username=username,
            is_admin=True

        ).first()



        if not owner_user:

            flash(

                "Account not found",

                "danger"

            )

            return redirect(

                url_for(
                    "site_settings.site_settings_login"
                )

            )



        password_correct = check_password_hash(

            owner_user.password,
            password

        )



        if not password_correct:

            flash(

                "Incorrect password",

                "danger"

            )

            return redirect(

                url_for(
                    "site_settings.site_settings_login"
                )

            )



        session[
            "pending_site_id"
        ] = owner_user.user_id



        generated_otp = generate_otp()

        otp_expiry = generate_otp_expiry(5)



        session[
            "temp_site_otp"
        ] = generated_otp



        session[
            "temp_site_otp_expiry"
        ] = otp_expiry.isoformat()



        email_sent = send_email(

            receiver_email=SITE_SETTINGS_OTP_EMAIL,

            subject="RM Bakes Platform Settings OTP",

            body=f"""

RM Bakes Platform Settings

Your OTP is:

{generated_otp}

This OTP expires in 5 minutes.

"""

        )



        if not email_sent:

            flash(

                "Failed to send OTP email",

                "danger"

            )

            return redirect(

                url_for(
                    "site_settings.site_settings_login"
                )

            )



        flash(

            "OTP sent successfully 📩",

            "success"

        )



        return redirect(

            url_for(
                "site_settings.verify_site_otp"
            )

        )


    return render_template(

        "site_settings/login.html"

    )


# =========================================
# VERIFY OTP
# =========================================

@site_settings_bp.route(

    "/site-settings/verify-otp",

    methods=["GET", "POST"]

)
def verify_site_otp():

    pending_site_id = session.get(

        "pending_site_id"

    )



    if not pending_site_id:

        return redirect(

            url_for(
                "site_settings.site_settings_login"
            )

        )



    if request.method == "POST":

        entered_otp = request.form.get(
            "otp"
        )



        stored_otp = session.get(
            "temp_site_otp"
        )



        stored_expiry = session.get(
            "temp_site_otp_expiry"
        )



        if stored_expiry:

            expiry_datetime = datetime.fromisoformat(

                stored_expiry

            )



            if is_otp_expired(

                expiry_datetime

            ):

                flash(

                    "OTP expired",

                    "danger"

                )

                clear_site_settings_session()

                return redirect(

                    url_for(
                        "site_settings.site_settings_login"
                    )

                )



        if entered_otp != stored_otp:

            flash(

                "Invalid OTP",

                "danger"

            )

            return redirect(

                url_for(
                    "site_settings.verify_site_otp"
                )

            )



        owner_user = User.query.get(

            pending_site_id

        )



        if not owner_user:

            clear_site_settings_session()

            return redirect(

                url_for(
                    "site_settings.site_settings_login"
                )

            )



        expiry_time = datetime.utcnow() + timedelta(

            minutes=SITE_SETTINGS_SESSION_MINUTES

        )



        session.pop(
            "pending_site_id",
            None
        )



        session.pop(
            "temp_site_otp",
            None
        )



        session.pop(
            "temp_site_otp_expiry",
            None
        )



        session[
            "is_admin"
        ] = True



        session[
            "site_settings_username"
        ] = owner_user.username



        session[
            "site_settings_expiry"
        ] = expiry_time.isoformat()



        flash(

            "Access verified 🔥",

            "success"

        )



        return redirect(

            url_for(
                "site_settings.site_settings_dashboard"
            )

        )


    return render_template(

        "site_settings/otp.html"

    )


# =========================================
# DASHBOARD
# =========================================

@site_settings_bp.route(

    "/site-settings/dashboard"

)
@site_settings_required
def site_settings_dashboard():

    all_features = SiteFeature.query.order_by(

        SiteFeature.feature_name

    ).all()

    # "Full Webpage" is the master site-wide switch — surfaced as its
    # own danger-zone card, separate from the routine per-module table,
    # so it isn't accidentally toggled alongside everything else.
    full_webpage_feature = next(
        (f for f in all_features if f.feature_key == "full_webpage"),
        None
    )

    features = [
        f for f in all_features if f.feature_key != "full_webpage"
    ]



    return render_template(

        "site_settings/dashboard.html",

        features=features,

        full_webpage_feature=full_webpage_feature,

        two_state_keys=TWO_STATE_FEATURE_KEYS,

        expiry_time=session.get(
            "site_settings_expiry"
        ),

        site_settings_username=session.get(
            "site_settings_username"
        )

    )


# =========================================
# UPDATE FEATURE STATUS
# =========================================

@site_settings_bp.route(

    "/site-settings/update-feature/<int:feature_id>",

    methods=["POST"]

)
@site_settings_required
def update_feature_status(feature_id):

    feature = SiteFeature.query.get_or_404(

        feature_id

    )



    new_status = request.form.get(
        "status"
    )



    if new_status not in VALID_STATUSES:

        flash(

            "Invalid status selected",

            "danger"

        )

        return redirect(

            url_for(
                "site_settings.site_settings_dashboard"
            )

        )



    if (

        feature.feature_key in TWO_STATE_FEATURE_KEYS
        and new_status == "COMING_SOON"

    ):

        flash(

            f"{feature.feature_name} only supports Live or Disabled",

            "danger"

        )

        return redirect(

            url_for(
                "site_settings.site_settings_dashboard"
            )

        )



    feature.status = new_status

    feature.updated_at = datetime.utcnow()

    feature.updated_by = session.get(
        "site_settings_username"
    )



    db.session.commit()



    flash(

        f"{feature.feature_name} set to {new_status.replace('_', ' ').title()} ✅",

        "success"

    )



    return redirect(

        url_for(
            "site_settings.site_settings_dashboard"
        )

    )


# =========================================
# LOGOUT
# =========================================

@site_settings_bp.route(

    "/site-settings/logout"

)
def site_settings_logout():

    clear_site_settings_session()

    flash(

        "Logged out 🔒",

        "success"

    )

    return redirect(

        url_for(
            "site_settings.site_settings_login"
        )

    )
