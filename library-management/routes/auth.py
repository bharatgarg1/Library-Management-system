"""
routes/auth.py
──────────────
Authentication routes — Login, Register, Logout,
Forgot Password, Reset Password.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import mail
from models import db, User
from forms.auth_forms import (
    LoginForm, RegisterForm, ForgotPasswordForm, ResetPasswordForm
)
from services.auth_service import (
    register_user, generate_reset_token, verify_reset_token,
    reset_user_password, send_reset_email, log_activity
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()

        if not user or not user.check_password(form.password.data):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", form=form)

        if not user.is_active:
            flash("Your account has been deactivated. Contact admin.", "warning")
            return render_template("auth/login.html", form=form)

        login_user(user, remember=form.remember_me.data)
        log_activity(user.id, "login", f"{user.email} logged in",
                     ip=request.remote_addr)

        flash(f"Welcome back, {user.full_name}!", "success")

        next_page = request.args.get("next")
        if next_page:
            return redirect(next_page)
        return _redirect_by_role(user)

    return render_template("auth/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    form = RegisterForm()
    if form.validate_on_submit():
        user = register_user({
            "full_name":  form.full_name.data,
            "email":      form.email.data,
            "role":       form.role.data,
            "student_id": form.student_id.data,
            "department": form.department.data,
            "password":   form.password.data,
        })
        flash("Account created successfully! Please sign in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    log_activity(current_user.id, "logout", f"{current_user.email} logged out",
                 ip=request.remote_addr)
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            token = generate_reset_token(user)
            try:
                send_reset_email(mail, user, token)
                flash("Password reset link sent to your email!", "success")
            except Exception:
                flash("Could not send email. Check mail settings.", "warning")
        else:
            # Show same message to prevent email enumeration
            flash("If that email exists, a reset link has been sent.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html", form=form)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = verify_reset_token(token)
    if not user:
        flash("Invalid or expired reset link.", "danger")
        return redirect(url_for("auth.forgot_password"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        reset_user_password(user, form.password.data)
        flash("Password reset successful! Please sign in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", form=form)


# ── Helper ────────────────────────────────────────────────────────────────────

def _redirect_by_role(user):
    """Send user to their role-specific dashboard."""
    if user.is_super_admin:
        return redirect(url_for("admin.dashboard"))
    if user.is_librarian:
        return redirect(url_for("librarian.dashboard"))
    return redirect(url_for("student.dashboard"))