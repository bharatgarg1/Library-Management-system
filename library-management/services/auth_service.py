"""
services/auth_service.py
─────────────────────────
Business logic for authentication.
Kept separate from routes so logic can be tested independently.
"""

import secrets
from datetime import datetime, timezone, timedelta
from flask import url_for
from flask_mail import Message
from models import db, User, Role, ActivityLog


def register_user(form_data: dict) -> User:
    """
    Create a new user from registration form data.
    Returns the created User object.
    """
    role = Role.query.filter_by(name=form_data["role"]).first()

    user = User(
        full_name=form_data["full_name"],
        email=form_data["email"].lower(),
        role_id=role.id,
        student_id=form_data.get("student_id") or None,
        department=form_data.get("department") or None,
        is_active=True,
        email_verified=True,
    )
    user.set_password(form_data["password"])
    db.session.add(user)

    log = ActivityLog(
        action="user_registered",
        description=f"New user registered: {user.email} as {form_data['role']}",
    )
    db.session.add(log)
    db.session.commit()

    return user


def generate_reset_token(user: User) -> str:
    """
    Generate a secure random token for password reset.
    Token expires in 1 hour.
    """
    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
    db.session.commit()
    return token


def verify_reset_token(token: str):
    """
    Find user by token and check it hasn't expired.
    Returns User if valid, None otherwise.
    """
    user = User.query.filter_by(reset_token=token).first()
    if not user:
        return None
    if not user.reset_token_expiry:
        return None
    expiry = user.reset_token_expiry.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expiry:
        return None
    return user


def reset_user_password(user: User, new_password: str) -> None:
    """Reset password and clear the token."""
    user.set_password(new_password)
    user.reset_token = None
    user.reset_token_expiry = None
    db.session.commit()


def send_reset_email(mail, user: User, token: str) -> None:
    """Send password reset email."""
    reset_url = url_for("auth.reset_password", token=token, _external=True)
    msg = Message(
        subject="LibraryOS — Password Reset Request",
        recipients=[user.email],
        html=f"""
        <div style="font-family:Inter,sans-serif;max-width:500px;margin:auto">
          <h2 style="color:#4f46e5">LibraryOS</h2>
          <p>Hi <strong>{user.full_name}</strong>,</p>
          <p>You requested a password reset. Click the button below:</p>
          <a href="{reset_url}"
             style="display:inline-block;background:#4f46e5;color:#fff;
                    padding:12px 24px;border-radius:8px;text-decoration:none;
                    font-weight:600;margin:16px 0">
            Reset Password
          </a>
          <p style="color:#64748b;font-size:0.875rem">
            This link expires in <strong>1 hour</strong>.<br/>
            If you did not request this, ignore this email.
          </p>
        </div>
        """
    )
    mail.send(msg)


def log_activity(user_id: int, action: str, description: str, ip: str = None) -> None:
    """Helper to log any user activity."""
    log = ActivityLog(
        user_id=user_id,
        action=action,
        description=description,
        ip_address=ip,
    )
    db.session.add(log)
    db.session.commit()