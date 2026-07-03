"""
routes/librarian.py
────────────────────
Librarian routes — Dashboard, Issue Book, Return Book, History.
"""

from flask import (
    Blueprint, render_template, redirect,
    url_for, flash, request, abort
)
from flask_login import login_required, current_user
from models import db, Book, User, BorrowRecord, Role
from forms.borrow_forms import IssueBookForm, ReturnBookForm
from services.borrow_service import (
    get_student_by_email, can_student_borrow,
    issue_book, return_book,
    get_active_borrows, get_borrow_history,
    update_overdue_records,
)

librarian_bp = Blueprint("librarian", __name__)


def librarian_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or (
            not current_user.is_librarian and
            not current_user.is_super_admin
        ):
            abort(403)
        return f(*args, **kwargs)
    return decorated


# ── Dashboard ──────────────────────────────────────────────────────────────

@librarian_bp.route("/dashboard")
@login_required
@librarian_required
def dashboard():
    update_overdue_records()

    total_books     = Book.query.count()
    active_borrows  = BorrowRecord.query.filter_by(status="borrowed").count()
    overdue_count   = BorrowRecord.query.filter_by(status="overdue").count()
    returned_today  = BorrowRecord.query.filter(
        BorrowRecord.status == "returned",
        db.func.date(BorrowRecord.return_date) == db.func.current_date()
    ).count()

    recent_borrows = (
        BorrowRecord.query
        .filter(BorrowRecord.status.in_(["borrowed", "overdue"]))
        .order_by(BorrowRecord.due_date.asc())
        .limit(8).all()
    )

    return render_template(
        "librarian/dashboard.html",
        total_books    = total_books,
        active_borrows = active_borrows,
        overdue_count  = overdue_count,
        returned_today = returned_today,
        recent_borrows = recent_borrows,
    )


# ── Issue Book ─────────────────────────────────────────────────────────────

@librarian_bp.route("/issue", methods=["GET", "POST"])
@login_required
@librarian_required
def issue():
    form = IssueBookForm()

    if form.validate_on_submit():
        student = get_student_by_email(form.student_email.data)
        if not student or not student.is_student:
            flash("No student found with that email.", "danger")
            return render_template("librarian/issue_book.html", form=form)

        book = db.session.get(Book, form.book_id.data)
        if not book:
            flash("Book not found. Check the Book ID.", "danger")
            return render_template("librarian/issue_book.html", form=form)

        if not book.is_available:
            flash(f'"{book.title}" has no available copies.', "danger")
            return render_template("librarian/issue_book.html", form=form)

        can_borrow, reason = can_student_borrow(student)
        if not can_borrow:
            flash(reason, "warning")
            return render_template("librarian/issue_book.html", form=form)

        record = issue_book(book, student, issued_by=current_user)
        flash(
            f'✅ "{book.title}" issued to {student.full_name}. '
            f'Due: {record.due_date.strftime("%d %b %Y")}.',
            "success"
        )
        return redirect(url_for("librarian.active_borrows"))

    return render_template("librarian/issue_book.html", form=form)


# ── Return Book ────────────────────────────────────────────────────────────

@librarian_bp.route("/return", methods=["GET", "POST"])
@login_required
@librarian_required
def accept_return():
    form = ReturnBookForm()

    if form.validate_on_submit():
        record = db.session.get(BorrowRecord, form.borrow_id.data)

        if not record:
            flash("Borrow record not found.", "danger")
            return render_template("librarian/return_book.html", form=form)

        if record.status == "returned":
            flash("This book has already been returned.", "warning")
            return render_template("librarian/return_book.html", form=form)

        record = return_book(record, collected_by=current_user)

        if record.fine_amount > 0:
            flash(
                f'✅ "{record.book.title}" returned by {record.user.full_name}. '
                f'Fine: ₹{record.fine_amount:.2f} (overdue by {record.days_overdue} days).',
                "warning"
            )
        else:
            flash(
                f'✅ "{record.book.title}" returned successfully by {record.user.full_name}.',
                "success"
            )
        return redirect(url_for("librarian.active_borrows"))

    return render_template("librarian/return_book.html", form=form)


# ── Active Borrows ─────────────────────────────────────────────────────────

@librarian_bp.route("/borrows")
@login_required
@librarian_required
def active_borrows():
    update_overdue_records()
    page       = request.args.get("page", 1, type=int)
    search     = request.args.get("search", "")
    pagination = get_active_borrows(page=page, per_page=15, search=search)

    return render_template(
        "librarian/active_borrows.html",
        pagination = pagination,
        borrows    = pagination.items,
        search     = search,
    )


# ── Borrow History ─────────────────────────────────────────────────────────

@librarian_bp.route("/history")
@login_required
@librarian_required
def history():
    page       = request.args.get("page", 1, type=int)
    pagination = get_borrow_history(page=page, per_page=15)

    return render_template(
        "librarian/history.html",
        pagination = pagination,
        borrows    = pagination.items,
    )