"""
AUTH ROUTES — RM Bakes
Login now merges guest session cart into the user DB cart.
Handles ?next= redirect after login (e.g. going to checkout while logged out).
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash

from flask_login import login_user, logout_user, login_required, current_user

from werkzeug.security import generate_password_hash, check_password_hash

from database import db, User

from datetime import datetime

from utils.notification_utils import create_admin_notification

# Import guest cart merge helper
from routes.cart_routes import merge_guest_cart

import re

auth_bp = Blueprint("auth", __name__)


# ─────────────────────────────────────────────
# SHARED VALIDATION — FIX 2
# Used by both /register (form) and /quick-create-account (AJAX)
# so the SAME rules apply everywhere.
# ─────────────────────────────────────────────

def validate_registration_fields(username, email, password):
    """
    Returns an error message string if invalid, or None if all checks pass.

    Rules:
      - All fields required
      - Username cannot be only numbers
      - Email MUST end with @gmail.com
      - Password >= 6 chars, contains letters, AND contains a number or symbol
      - Username / Email / Password cannot equal one another (case-insensitive)
    """

    if not username or not email or not password:
        return "Please fill all fields 😭"

    if username.isdigit():
        return "Username cannot contain only numbers 😭"

    # FIX 2: Email must end with @gmail.com specifically
    if not re.match(r"^[^@\s]+@gmail\.com$", email, re.IGNORECASE):
        return "Email address must end with @gmail.com 📧"

    if len(password) < 6:
        return "Password must contain at least 6 characters 🔐"

    if not any(c.isalpha() for c in password):
        return "Password must contain letters 🔤"

    # FIX 2: number OR special character (not strictly both required)
    has_number = any(c.isdigit() for c in password)
    has_symbol = any(not c.isalnum() for c in password)
    if not has_number and not has_symbol:
        return "Password must contain a number or special character 🔢"

    u, e, p = username.lower(), email.lower(), password.lower()

    # FIX 2: cross-field duplicate checks (all 3 pairs)
    if u == e:
        return "Username and email cannot be the same 😅"
    if u == p:
        return "Username and password cannot be the same 🔒"
    if e == p:
        return "Email and password cannot be the same 🔒"

    return None


# ─────────────────────────────────────────────
# REGISTER
# ─────────────────────────────────────────────

@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        email    = request.form.get("email",    "").strip()
        password = request.form.get("password", "").strip()

        # ── FIX 2: All registration validation rules ──
        validation_error = validate_registration_fields(username, email, password)
        if validation_error:
            flash(validation_error, "error")
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

        # Auto-login straight away (no-JS fallback path — the JS-enabled
        # flow uses /quick-create-account via fetch instead, with an
        # animated overlay; this covers the same outcome without JS).
        login_user(new_user, remember=True)
        merge_guest_cart(new_user.user_id)

        # ── Track last login for the admin Customer Network module ──
        new_user.last_login = datetime.utcnow()
        db.session.commit()

        flash("Welcome to RM Bakes! 🎉", "success")
        return redirect(url_for("main.home"))

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

        login_user(user, remember=True)

        # ── Track last login for the admin Customer Network module ──
        user.last_login = datetime.utcnow()
        db.session.commit()

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


# ─────────────────────────────────────────────
# QUICK LOGIN CHECK  (AJAX — returns JSON)
# Used by login.html for the smart account-creation flow
# ─────────────────────────────────────────────

@auth_bp.route("/quick-login-check", methods=["POST"])
def quick_login_check():

    from flask import jsonify
    from werkzeug.security import check_password_hash

    data     = request.get_json(silent=True) or {}
    email    = data.get("email",    "").strip()
    password = data.get("password", "").strip()
    next_url = data.get("next", "").strip()   # FIX 5: optional redirect target

    if not email or not password:
        return jsonify({"success": False, "error": "missing_fields",
                        "message": "Email and password are required"})

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"success": False, "error": "user_not_found",
                        "message": "No account found for this email"})

    if user.is_deleted:
        return jsonify({"success": False, "error": "deleted",
                        "message": "This account was deleted"})

    if not check_password_hash(user.password, password):
        return jsonify({"success": False, "error": "wrong_password",
                        "message": "Incorrect password"})

    login_user(user, remember=True)

    # ── Track last login for the admin Customer Network module ──
    user.last_login = datetime.utcnow()
    db.session.commit()

    merge_guest_cart(user.user_id)

    create_admin_notification(
        title="User Login",
        message=f"\nUser:\n{user.username}\n\nlogged into RM Bakes (AJAX).\n",
        notification_type="user"
    )

    # FIX 5: only trust internal relative paths (prevents open-redirect)
    safe_redirect = next_url if (next_url and next_url.startswith("/")) else "/"

    return jsonify({"success": True, "redirect": safe_redirect})


# ─────────────────────────────────────────────
# CHECK USERNAME AVAILABILITY  (AJAX)
# ─────────────────────────────────────────────

@auth_bp.route("/check-username", methods=["POST"])
def check_username():

    from flask import jsonify

    data     = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()

    if not username:
        return jsonify({"available": False, "message": "Username is required"})

    if username.isdigit():
        return jsonify({"available": False, "message": "Username cannot be only numbers"})

    exists = User.query.filter_by(username=username).first()

    if exists:
        return jsonify({"available": False, "message": "Username already taken"})

    return jsonify({"available": True, "message": "Username is available ✓"})


# ─────────────────────────────────────────────
# QUICK CREATE ACCOUNT + AUTO-LOGIN  (AJAX)
# Used by the smart create-account overlay in login.html
# ─────────────────────────────────────────────

@auth_bp.route("/quick-create-account", methods=["POST"])
def quick_create_account():

    from flask import jsonify
    from werkzeug.security import generate_password_hash

    data     = request.get_json(silent=True) or {}
    email    = data.get("email",    "").strip()
    password = data.get("password", "").strip()
    username = data.get("username", "").strip()
    next_url = data.get("next", "").strip()   # FIX 5: optional redirect target

    # FIX 2: SAME validation rules as /register (shared function)
    validation_error = validate_registration_fields(username, email, password)
    if validation_error:
        return jsonify({"success": False, "message": validation_error})

    # Check uniqueness
    if User.query.filter_by(username=username).first():
        return jsonify({"success": False,
                        "error": "username_taken",
                        "message": "Username already taken — choose another"})

    existing = User.query.filter_by(email=email).first()
    if existing:
        if existing.is_deleted:
            return jsonify({"success": False,
                            "message": "This email belongs to a deleted account"})
        return jsonify({"success": False,
                        "message": "An account already exists for this email"})

    # Create account
    new_user = User(
        username=username,
        email=email,
        password=generate_password_hash(password)
    )
    db.session.add(new_user)
    db.session.commit()

    # Auto-login
    login_user(new_user, remember=True)

    # ── Track last login for the admin Customer Network module ──
    new_user.last_login = datetime.utcnow()
    db.session.commit()

    merge_guest_cart(new_user.user_id)

    create_admin_notification(
        title="New Quick-Signup User",
        message=f"\nUsername:\n{new_user.username}\n\nEmail:\n{new_user.email}\n\njoined via quick-signup.\n",
        notification_type="user"
    )

    # FIX 5: only trust internal relative paths (prevents open-redirect)
    safe_redirect = next_url if (next_url and next_url.startswith("/")) else "/"

    return jsonify({"success": True, "redirect": safe_redirect})
