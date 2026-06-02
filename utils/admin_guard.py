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