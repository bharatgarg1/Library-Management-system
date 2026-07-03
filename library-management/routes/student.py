"""
routes/student.py
──────────────────
Student portal routes.
"""

from flask import (
    Blueprint, render_template, redirect,
    url_for, flash, request, abort
)
from flask_login import login_required, current_user
from models import db, Category, Book
from services.student_service import (
    get_student_dashboard_data,
    get_student_borrows,
    get_student_fines,
    get_wishlist,
    add_to_wishlist,
    remove_from_wishlist,
    get_notifications,
    mark_notifications_read,
    update_profile,
    get_available_books,
)

student_bp = Blueprint("student", __name__)


def student_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_student:
            abort(403)
        return f(*args, **kwargs)
    return decorated


# ── Dashboard ──────────────────────────────────────────────────────────────

@student_bp.route("/dashboard")
@login_required
@student_required
def dashboard():
    data = get_student_dashboard_data(current_user)
    return render_template("student/dashboard.html", **data)


# ── Browse Books ───────────────────────────────────────────────────────────

@student_bp.route("/books")
@login_required
@student_required
def books():
    page        = request.args.get("page", 1, type=int)
    search      = request.args.get("search", "")
    category_id = request.args.get("category", None, type=int)

    pagination  = get_available_books(
        page=page, per_page=12,
        search=search, category_id=category_id
    )
    categories  = Category.query.order_by(Category.name).all()

    # Check which books are in student's wishlist
    from models import Wishlist
    wishlist_book_ids = {
        w.book_id for w in
        Wishlist.query.filter_by(user_id=current_user.id).all()
    }

    return render_template(
        "student/books.html",
        pagination       = pagination,
        books            = pagination.items,
        categories       = categories,
        search           = search,
        category_id      = category_id,
        wishlist_book_ids= wishlist_book_ids,
    )


# ── Borrow History ─────────────────────────────────────────────────────────

@student_bp.route("/history")
@login_required
@student_required
def history():
    page       = request.args.get("page", 1, type=int)
    pagination = get_student_borrows(current_user.id, page=page)
    return render_template(
        "student/history.html",
        pagination = pagination,
        borrows    = pagination.items,
    )


# ── Wishlist ───────────────────────────────────────────────────────────────

@student_bp.route("/wishlist")
@login_required
@student_required
def wishlist():
    entries = get_wishlist(current_user.id)
    return render_template("student/wishlist.html", entries=entries)


@student_bp.route("/wishlist/add/<int:book_id>", methods=["POST"])
@login_required
@student_required
def wishlist_add(book_id):
    success, message = add_to_wishlist(current_user.id, book_id)
    flash(message, "success" if success else "warning")
    return redirect(request.referrer or url_for("student.books"))


@student_bp.route("/wishlist/remove/<int:book_id>", methods=["POST"])
@login_required
@student_required
def wishlist_remove(book_id):
    success, message = remove_from_wishlist(current_user.id, book_id)
    flash(message, "success" if success else "warning")
    return redirect(request.referrer or url_for("student.wishlist"))


# ── Fines ──────────────────────────────────────────────────────────────────

@student_bp.route("/fines")
@login_required
@student_required
def fines():
    fine_records = get_student_fines(current_user.id)
    total_unpaid = sum(
        r.fine_amount for r in fine_records if not r.fine_paid
    )
    total_paid = sum(
        r.fine_amount for r in fine_records if r.fine_paid
    )
    return render_template(
        "student/fines.html",
        fine_records = fine_records,
        total_unpaid = round(total_unpaid, 2),
        total_paid   = round(total_paid, 2),
    )


# ── Profile ────────────────────────────────────────────────────────────────

@student_bp.route("/profile", methods=["GET", "POST"])
@login_required
@student_required
def profile():
    if request.method == "POST":
        update_profile(current_user, {
            "full_name":  request.form.get("full_name"),
            "phone":      request.form.get("phone"),
            "department": request.form.get("department"),
            "semester":   request.form.get("semester", type=int),
        })
        flash("Profile updated successfully!", "success")
        return redirect(url_for("student.profile"))

    return render_template("student/profile.html")


# ── Notifications ──────────────────────────────────────────────────────────

@student_bp.route("/notifications")
@login_required
@student_required
def notifications():
    notifs = get_notifications(current_user.id)
    mark_notifications_read(current_user.id)
    return render_template(
        "student/notifications.html",
        notifications=notifs
    )