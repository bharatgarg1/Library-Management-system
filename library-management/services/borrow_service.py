"""
services/borrow_service.py
───────────────────────────
Business logic for borrowing, returning, and fine calculation.
"""

from datetime import datetime, timezone, timedelta
from flask import current_app
from models import db, User, Book, BorrowRecord, Notification


def get_student_by_email(email: str):
    """Find a student user by email."""
    return User.query.filter_by(
        email=email.lower().strip()
    ).first()


def can_student_borrow(user: User) -> tuple:
    """
    Check if student is eligible to borrow.
    Returns (True, "") or (False, "reason")
    """
    max_books = current_app.config.get("MAX_BOOKS_PER_STUDENT", 3)

    active_borrows = BorrowRecord.query.filter_by(
        user_id=user.id, status="borrowed"
    ).count()

    if active_borrows >= max_books:
        return False, f"Student already has {active_borrows} books borrowed (max {max_books})."

    unpaid_fines = BorrowRecord.query.filter_by(
        user_id=user.id, fine_paid=False
    ).filter(BorrowRecord.fine_amount > 0).count()

    if unpaid_fines > 0:
        return False, "Student has unpaid fines. Please clear fines before borrowing."

    return True, ""


def issue_book(book: Book, student: User, issued_by: User) -> BorrowRecord:
    """
    Issue a book to a student.
    Decrements available_copies and creates a BorrowRecord.
    """
    max_days = current_app.config.get("MAX_BORROW_DAYS", 14)
    due_date = datetime.now(timezone.utc) + timedelta(days=max_days)

    record = BorrowRecord(
        user_id      = student.id,
        book_id      = book.id,
        issued_by_id = issued_by.id,
        due_date     = due_date,
        status       = "borrowed",
    )
    db.session.add(record)

    book.available_copies -= 1

    _notify(
        user    = student,
        title   = f"Book Issued: {book.title}",
        message = f'You have borrowed "{book.title}". '
                  f'Due date: {due_date.strftime("%d %b %Y")}.',
        type_   = "info",
    )

    db.session.commit()
    return record


def return_book(record: BorrowRecord, collected_by: User) -> BorrowRecord:
    """
    Process a book return.
    Calculates fine if overdue and updates availability.
    """
    now = datetime.now(timezone.utc)
    record.return_date = now
    record.status      = "returned"

    fine = _calculate_fine(record)
    record.fine_amount = fine

    record.book.available_copies += 1

    if fine > 0:
        record.fine_paid = False
        _notify(
            user    = record.user,
            title   = "Fine Issued",
            message = f'You returned "{record.book.title}" late. '
                      f'Fine: ₹{fine:.2f}.',
            type_   = "warning",
        )
    else:
        _notify(
            user    = record.user,
            title   = "Book Returned",
            message = f'You have successfully returned "{record.book.title}". Thank you!',
            type_   = "success",
        )

    db.session.commit()
    return record


def get_active_borrows(page: int = 1, per_page: int = 15, search: str = ""):
    """Get all currently borrowed books with optional search."""
    query = BorrowRecord.query.filter_by(status="borrowed")

    if search:
        query = query.join(User).filter(
            User.email.ilike(f"%{search}%") |
            User.full_name.ilike(f"%{search}%")
        )

    return query.order_by(
        BorrowRecord.due_date.asc()
    ).paginate(page=page, per_page=per_page, error_out=False)


def get_borrow_history(page: int = 1, per_page: int = 15):
    """Get all borrow records for history view."""
    return BorrowRecord.query.order_by(
        BorrowRecord.borrow_date.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)


def update_overdue_records() -> int:
    """
    Mark overdue records.
    Returns count of newly marked overdue records.
    """
    now = datetime.now(timezone.utc)
    records = BorrowRecord.query.filter_by(status="borrowed").all()
    count = 0
    for r in records:
        due = r.due_date.replace(tzinfo=timezone.utc)
        if due < now:
            r.status = "overdue"
            r.fine_amount = _calculate_fine(r)
            count += 1
    db.session.commit()
    return count


# ── Private Helpers ────────────────────────────────────────────────────────

def _calculate_fine(record: BorrowRecord) -> float:
    """Calculate fine based on days overdue."""
    fine_per_day = current_app.config.get("FINE_PER_DAY", 2.0)
    if not record.is_overdue and record.status != "overdue":
        return 0.0
    days = record.days_overdue
    return round(days * fine_per_day, 2)


def _notify(user: User, title: str, message: str, type_: str = "info") -> None:
    """Create an in-app notification for a user."""
    notif = Notification(
        user_id = user.id,
        title   = title,
        message = message,
        type    = type_,
    )
    db.session.add(notif)