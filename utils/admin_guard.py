from functools import wraps

from flask import (
    session,
    redirect,
    url_for,
    flash
)

from datetime import datetime



# =========================================
# ADMIN REQUIRED DECORATOR
# =========================================

def admin_required(route_function):

    @wraps(route_function)
    def wrapper(*args, **kwargs):

        # =================================
        # CHECK ADMIN LOGIN
        # =================================

        if not session.get(
            "admin_verified"
        ):

            flash(
                "Admin access required 🔒",
                "danger"
            )

            return redirect(
                url_for(
                    "admin.admin_login"
                )
            )



        # =================================
        # CHECK SESSION EXPIRY
        # =================================

        expiry_time = session.get(
            "admin_expiry"
        )



        if not expiry_time:

            session.clear()

            flash(
                "Admin session expired 🔒",
                "danger"
            )

            return redirect(
                url_for(
                    "admin.admin_login"
                )
            )



        # =================================
        # CONVERT STRING TO DATETIME
        # =================================

        expiry_datetime = datetime.fromisoformat(
            expiry_time
        )



        # =================================
        # CHECK CURRENT TIME
        # =================================

        if datetime.utcnow() > expiry_datetime:

            session.clear()

            flash(
                "Admin session expired 🔒",
                "danger"
            )

            return redirect(
                url_for(
                    "admin.admin_login"
                )
            )



        # =================================
        # VALID SESSION
        # =================================

        return route_function(
            *args,
            **kwargs
        )



    return wrapper



# =========================================
# SITE SETTINGS SESSION KEYS
# =========================================
# Kept entirely separate from the admin_* keys above so that logging
# into /site-settings can never grant access to /admin, and vice versa.

SITE_SETTINGS_SESSION_KEYS = [

    "pending_site_id",
    "temp_site_otp",
    "temp_site_otp_expiry",
    "is_admin",
    "site_settings_username",
    "site_settings_expiry"

]


def clear_site_settings_session():
    """Remove only the site-settings session keys, leaving any other
    active session state (e.g. a concurrent admin login) untouched."""

    for key in SITE_SETTINGS_SESSION_KEYS:

        session.pop(
            key,
            None
        )



# =========================================
# SITE SETTINGS REQUIRED DECORATOR
# =========================================

def site_settings_required(route_function):

    @wraps(route_function)
    def wrapper(*args, **kwargs):

        # =================================
        # CHECK SITE SETTINGS LOGIN
        # =================================

        if not session.get(
            "is_admin"
        ):

            flash(
                "Site settings access required 🔒",
                "danger"
            )

            return redirect(
                url_for(
                    "site_settings.site_settings_login"
                )
            )



        # =================================
        # CHECK SESSION EXPIRY
        # =================================

        expiry_time = session.get(
            "site_settings_expiry"
        )



        if not expiry_time:

            clear_site_settings_session()

            flash(
                "Site settings session expired 🔒",
                "danger"
            )

            return redirect(
                url_for(
                    "site_settings.site_settings_login"
                )
            )



        # =================================
        # CONVERT STRING TO DATETIME
        # =================================

        expiry_datetime = datetime.fromisoformat(
            expiry_time
        )



        # =================================
        # CHECK CURRENT TIME
        # =================================

        if datetime.utcnow() > expiry_datetime:

            clear_site_settings_session()

            flash(
                "Site settings session expired 🔒",
                "danger"
            )

            return redirect(
                url_for(
                    "site_settings.site_settings_login"
                )
            )



        # =================================
        # VALID SESSION
        # =================================

        return route_function(
            *args,
            **kwargs
        )


    return wrapper