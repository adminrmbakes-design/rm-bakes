"""
AUTH ROUTES — RM Bakes
Login now merges guest session cart into the user DB cart.
Handles ?next= redirect after login (e.g. going to checkout while logged out).
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash

from flask_login import login_user, logout_user, login_required, current_user

from werkzeug.security import generate_password_hash, check_password_hash

from database import db, User

from utils.notification_utils import create_admin_notification

# Import guest cart merge helper
from routes.cart_routes import merge_guest_cart

import re

auth_bp = Blueprint("auth", __name__)


# ─────────────────────────────────────────────
# REGISTER
# ─────────────────────────────────────────────

@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        email    = request.form.get("email",    "").strip()
        password = request.form.get("password", "").strip()

        if not username or not email or not password:
            flash("Please fill all fields 😭", "error")
            return redirect(url_for("auth.register"))

        if username.isdigit():
            flash("Username cannot contain only numbers 😭", "error")
            return redirect(url_for("auth.register"))

        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
            flash("Enter a valid email address 📧", "error")
            return redirect(url_for("auth.register"))

        if len(password) < 6:
            flash("Password must contain at least 6 characters 🔐", "error")
            return redirect(url_for("auth.register"))

        if password.isdigit():
            flash("Password cannot contain only numbers 🔒", "error")
            return redirect(url_for("auth.register"))

        if not any(c.isalpha() for c in password):
            flash("Password must contain letters 🔤", "error")
            return redirect(url_for("auth.register"))

        if not any(c.isdigit() for c in password):
            flash("Password must contain at least one number 🔢", "error")
            return redirect(url_for("auth.register"))

        if not any(not c.isalnum() for c in password):
            flash("Password must contain at least one symbol ✨", "error")
            return redirect(url_for("auth.register"))

        if username.lower() == password.lower():
            flash("Username and password cannot be same 😭", "error")
            return redirect(url_for("auth.register"))

        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            flash("Username already taken 😭", "error")
            return redirect(url_for("auth.register"))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            if existing_user.is_deleted:
                flash("This account was deleted 😭 Recover account instead", "error")
                return redirect(url_for("auth.login"))
            flash("Email already registered 😭", "error")
            return redirect(url_for("auth.register"))

        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()

        create_admin_notification(
            title="New User Registered",
            message=f"\nUsername:\n{new_user.username}\n\nEmail:\n{new_user.email}\n\njoined RM Bakes.\n",
            notification_type="user"
        )

        flash("Registration successful ✨", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


# ─────────────────────────────────────────────
# LOGIN  — merges guest cart after login
# ─────────────────────────────────────────────

@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email    = request.form.get("email",    "").strip()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Please enter email and password 😭", "error")
            return redirect(url_for("auth.login"))

        user = User.query.filter_by(email=email).first()

        if not user:
            create_admin_notification(
                title="Failed User Login",
                message=f"\nLogin attempt failed.\nEmail:\n{email}\nReason:\nUser does not exist\n",
                notification_type="security"
            )
            flash("User doesn't exist 😭 Create a new account", "error")
            return redirect(url_for("auth.register"))

        if user.is_deleted:
            flash("This account was deleted 😭 Recover account instead", "error")
            return redirect(url_for("auth.login"))

        if not check_password_hash(user.password, password):
            create_admin_notification(
                title="Failed User Login",
                message=f"\nFailed login attempt for:\n{user.username}\nReason:\nIncorrect password\n",
                notification_type="security"
            )
            flash("Incorrect password 🔒", "error")
            return redirect(url_for("auth.login"))

        login_user(user)

        # ── Merge any guest cart into this user's DB cart ──
        merge_guest_cart(user.user_id)

        create_admin_notification(
            title="User Login",
            message=f"\nUser:\n{user.username}\n\nlogged into RM Bakes.\n",
            notification_type="user"
        )

        flash("Login successful ✨", "success")

        # ── Respect ?next= so guests going to checkout land there ──
        next_page = request.args.get("next") or request.form.get("next")
        if next_page and next_page.startswith("/"):
            return redirect(next_page)

        return redirect(url_for("main.home"))

    return render_template("login.html")


# ─────────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────────

@auth_bp.route("/logout")
@login_required
def logout():

    create_admin_notification(
        title="User Logout",
        message=f"\nUser:\n{current_user.username}\n\nlogged out from RM Bakes.\n",
        notification_type="user"
    )

    logout_user()

    flash("Logged out successfully 👋", "success")

    return redirect(url_for("auth.login"))
