from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash

from flask_login import login_user
from flask_login import logout_user
from flask_login import login_required
from flask_login import current_user

from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

from database import db
from database import User

from utils.notification_utils import (

    create_admin_notification

)

import re



# =========================================
# BLUEPRINT
# =========================================

auth_bp = Blueprint(
    "auth",
    __name__
)



# =========================================
# REGISTER
# =========================================

@auth_bp.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()



        if not username or not email or not password:

            flash(
                "Please fill all fields 😭",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )



        if username.isdigit():

            flash(
                "Username cannot contain only numbers 😭",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )



        email_pattern = r"^[^@]+@[^@]+\.[^@]+$"

        if not re.match(
            email_pattern,
            email
        ):

            flash(
                "Enter a valid email address 📧",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )



        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters 🔐",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )



        if password.isdigit():

            flash(
                "Password cannot contain only numbers 🔒",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )



        if not any(
            char.isalpha()
            for char in password
        ):

            flash(
                "Password must contain letters 🔤",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )



        if not any(
            char.isdigit()
            for char in password
        ):

            flash(
                "Password must contain at least one number 🔢",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )



        if not any(
            not char.isalnum()
            for char in password
        ):

            flash(
                "Password must contain at least one symbol ✨",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )



        if username.lower() == password.lower():

            flash(
                "Username and password cannot be same 😭",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )



        existing_user = User.query.filter_by(
            email=email
        ).first()



        existing_username = User.query.filter_by(
            username=username
        ).first()



        if existing_username:

            flash(
                "Username already taken 😭",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )



        if existing_user:

            if existing_user.is_deleted:

                flash(
                    "This account was deleted 😭 Recover account instead",
                    "error"
                )

                return redirect(
                    url_for("auth.login")
                )



            flash(
                "Email already registered 😭",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )



        hashed_password = generate_password_hash(
            password
        )



        new_user = User(

            username=username,

            email=email,

            password=hashed_password

        )



        db.session.add(new_user)

        db.session.commit()



        create_admin_notification(

            title="New User Registered",

            message=f"""

Username:
{new_user.username}

Email:
{new_user.email}

joined RM Bakes.

""",

            notification_type="user"

        )



        flash(
            "Registration successful ✨",
            "success"
        )



        return redirect(
            url_for("auth.login")
        )



    return render_template(
        "register.html"
    )



# =========================================
# LOGIN
# =========================================

@auth_bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()



        if not email or not password:

            flash(
                "Please enter email and password 😭",
                "error"
            )

            return redirect(
                url_for("auth.login")
            )



        user = User.query.filter_by(
            email=email
        ).first()



        if not user:

            create_admin_notification(

                title="Failed User Login",

                message=f"""

Login attempt failed.

Email:
{email}

Reason:
User does not exist

""",

                notification_type="security"

            )



            flash(
                "User doesn't exist 😭 Create a new account",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )



        if user.is_deleted:

            flash(
                "This account was deleted 😭 Recover account instead",
                "error"
            )

            return redirect(
                url_for("auth.login")
            )



        if not check_password_hash(
            user.password,
            password
        ):

            create_admin_notification(

                title="Failed User Login",

                message=f"""

Failed login attempt for:

{user.username}

Reason:
Incorrect password

""",

                notification_type="security"

            )



            flash(
                "Incorrect password 🔒",
                "error"
            )

            return redirect(
                url_for("auth.login")
            )



        login_user(user)



        create_admin_notification(

            title="User Login",

            message=f"""

User:
{user.username}

logged into RM Bakes.

""",

            notification_type="user"

        )



        flash(
            "Login successful ✨",
            "success"
        )



        return redirect(
            url_for("main.home")
        )



    return render_template(
        "login.html"
    )



# =========================================
# LOGOUT
# =========================================

@auth_bp.route("/logout")
@login_required
def logout():

    create_admin_notification(

        title="User Logout",

        message=f"""

User:
{current_user.username}

logged out from RM Bakes.

""",

        notification_type="user"

    )



    logout_user()



    flash(
        "Logged out successfully 👋",
        "success"
    )



    return redirect(
        url_for("auth.login")
    )