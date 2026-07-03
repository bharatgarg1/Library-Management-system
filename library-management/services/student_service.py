"""
services/student_service.py
────────────────────────────
All data logic for the student portal.
"""

from datetime import datetime, timezone
from models import db, User, Book, BorrowRecord, Wishlist, Notification, FinePayment


def get_student_dashboard_data(user: User) -> dict:
    """Return all data needed for student dashboard."""
    active_borrows = BorrowRecord.query.filter_by(
        user_id=user.id, status="borrowed"
    ).all()

    overdue_borrows = BorrowRecord.query.filter_by(
        user_id=user.id, status="overdue"
    ).all()

    total_borrowed = BorrowRecord.query.filter_by(
        user_id=user.id
    ).count()

    wishlist_count = Wishlist.query.filter_by(user_id=user.id).count()

    unpaid_fines = db.session.query(
        db.func.sum(BorrowRecord.fine_amount)
    ).filter_by(
        user_id=user.id,
        fine_paid=False
    ).filter(BorrowRecord.fine_amount > 0).scalar() or 0.0

    unread_notifications = Notification.query.filter_by(
        user_id=user.id,
        is_read=False
    ).count()

    recent_borrows = BorrowRecord.query.filter_by(
        user_id=user.id
    ).order_by(BorrowRecord.borrow_date.desc()).limit(5).all()

    return {
        "active_borrows":        active_borrows,
        "active_count":          len(active_borrows),
        "overdue_borrows":       overdue_borrows,
        "overdue_count":         len(overdue_borrows),
        "total_borrowed":        total_borrowed,
        "wishlist_count":        wishlist_count,
        "unpaid_fines":          round(unpaid_fines, 2),
        "unread_notifications":  unread_notifications,
        "recent_borrows":        recent_borrows,
    }


def get_student_borrows(user_id: int, page: int = 1, per_page: int = 10):
    """Paginated borrow history for a student."""
    return BorrowRecord.query.filter_by(
        user_id=user_id
    ).order_by(
        BorrowRecord.borrow_date.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)


def get_student_fines(user_id: int):
    """All borrow records with fines for a student."""
    return BorrowRecord.query.filter_by(
        user_id=user_id
    ).filter(
        BorrowRecord.fine_amount > 0
    ).order_by(BorrowRecord.borrow_date.desc()).all()


def get_wishlist(user_id: int):
    """All wishlist entries for a student."""
    return Wishlist.query.filter_by(
        user_id=user_id
    ).order_by(Wishlist.added_at.desc()).all()


def add_to_wishlist(user_id: int, book_id: int) -> tuple:
    """
    Add a book to wishlist.
    Returns (True, message) or (False, error)
    """
    existing = Wishlist.query.filter_by(
        user_id=user_id, book_id=book_id
    ).first()

    if existing:
        return False, "Book is already in your wishlist."

    entry = Wishlist(user_id=user_id, book_id=book_id)
    db.session.add(entry)
    db.session.commit()
    return True, "Book added to wishlist!"


def remove_from_wishlist(user_id: int, book_id: int) -> tuple:
    """Remove a book from wishlist."""
    entry = Wishlist.query.filter_by(
        user_id=user_id, book_id=book_id
    ).first()

    if not entry:
        return False, "Book not found in wishlist."

    db.session.delete(entry)
    db.session.commit()
    return True, "Book removed from wishlist."


def get_notifications(user_id: int, limit: int = 20):
    """Get notifications for a student."""
    return Notification.query.filter_by(
        user_id=user_id
    ).order_by(
        Notification.created_at.desc()
    ).limit(limit).all()


def mark_notifications_read(user_id: int) -> None:
    """Mark all notifications as read."""
    Notification.query.filter_by(
        user_id=user_id, is_read=False
    ).update({"is_read": True})
    db.session.commit()


def update_profile(user: User, data: dict) -> User:
    """Update student profile fields."""
    user.full_name  = data.get("full_name", user.full_name).strip()
    user.phone      = data.get("phone", user.phone)
    user.department = data.get("department", user.department)
    user.semester   = data.get("semester", user.semester)
    db.session.commit()
    return user


def get_available_books(page: int = 1, per_page: int = 12,
                        search: str = "", category_id: int = None):
    """Browse available books with search and filter."""
    from models import Category
    query = Book.query

    if search:
        query = query.filter(
            Book.title.ilike(f"%{search}%") |
            Book.description.ilike(f"%{search}%")
        )
    if category_id:
        query = query.filter_by(category_id=category_id)

    return query.order_by(Book.title.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )