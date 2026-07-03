"""
routes/admin.py
───────────────
Super Admin routes — Dashboard + Book Management.
"""

import json
from flask import (
    Blueprint, render_template, abort, redirect,
    url_for, flash, request
)
from flask_login import login_required, current_user
from models import db, Book, Category
from forms.book_forms import BookForm
from services.admin_service import (
    get_dashboard_stats, get_recent_borrows,
    get_recent_activity, get_low_stock_books,
    get_monthly_borrows_chart, get_category_chart,
)
from services.book_service import (
    create_book, update_book, delete_book,
    get_books_paginated
)

admin_bp = Blueprint("admin", __name__)


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_super_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


# ── Dashboard ──────────────────────────────────────────────────────────────

@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    stats           = get_dashboard_stats()
    recent_borrows  = get_recent_borrows()
    recent_activity = get_recent_activity()
    low_stock       = get_low_stock_books()
    monthly_chart   = get_monthly_borrows_chart()
    category_chart  = get_category_chart()

    return render_template(
        "admin/dashboard.html",
        stats           = stats,
        recent_borrows  = recent_borrows,
        recent_activity = recent_activity,
        low_stock       = low_stock,
        monthly_labels  = json.dumps(monthly_chart["labels"]),
        monthly_data    = json.dumps(monthly_chart["data"]),
        category_labels = json.dumps(category_chart["labels"]),
        category_data   = json.dumps(category_chart["data"]),
    )


# ── Books ──────────────────────────────────────────────────────────────────

@admin_bp.route("/books")
@login_required
@admin_required
def books():
    page        = request.args.get("page", 1, type=int)
    search      = request.args.get("search", "")
    category_id = request.args.get("category", None, type=int)
    per_page    = 10

    pagination  = get_books_paginated(page, per_page, search, category_id)
    categories  = Category.query.order_by(Category.name).all()

    return render_template(
        "admin/books.html",
        pagination  = pagination,
        books       = pagination.items,
        categories  = categories,
        search      = search,
        category_id = category_id,
    )


@admin_bp.route("/books/add", methods=["GET", "POST"])
@login_required
@admin_required
def book_add():
    form = BookForm()
    form.category_id.choices = [
        (c.id, c.name)
        for c in Category.query.order_by(Category.name).all()
    ]

    if form.validate_on_submit():
        create_book(
            form_data  = form.data,
            cover_file = request.files.get("cover_image"),
        )
        flash("Book added successfully!", "success")
        return redirect(url_for("admin.books"))

    return render_template("admin/book_add.html", form=form)


@admin_bp.route("/books/edit/<int:book_id>", methods=["GET", "POST"])
@login_required
@admin_required
def book_edit(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        abort(404)

    form = BookForm(obj=book)
    form.category_id.choices = [
        (c.id, c.name)
        for c in Category.query.order_by(Category.name).all()
    ]

    if request.method == "GET":
        form.author_name.data = book.author.name

    if form.validate_on_submit():
        update_book(
            book       = book,
            form_data  = form.data,
            cover_file = request.files.get("cover_image"),
        )
        flash("Book updated successfully!", "success")
        return redirect(url_for("admin.books"))

    return render_template("admin/book_edit.html", form=form, book=book)


@admin_bp.route("/books/delete/<int:book_id>", methods=["POST"])
@login_required
@admin_required
def book_delete(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        abort(404)
    title = book.title
    delete_book(book)
    flash(f'"{title}" deleted successfully.', "success")
    return redirect(url_for("admin.books"))