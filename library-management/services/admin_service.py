"""
services/admin_service.py
─────────────────────────
All data-fetching logic for the admin dashboard.
Kept separate from routes so it can be tested and reused.
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy import func
from models import db, User, Book, BorrowRecord, FinePayment, Role, ActivityLog


def get_dashboard_stats() -> dict:
    """
    Returns all statistics needed for the admin dashboard cards.
    """
    total_books       = Book.query.count()
    total_users       = User.query.count()
    total_students    = User.query.join(Role).filter(Role.name == "student").count()
    total_librarians  = User.query.join(Role).filter(Role.name == "librarian").count()

    active_borrows    = BorrowRecord.query.filter_by(status="borrowed").count()
    overdue_count     = _get_overdue_count()
    total_fines       = _get_total_fines()
    collected_fines   = _get_collected_fines()

    available_books   = db.session.query(
        func.sum(Book.available_copies)
    ).scalar() or 0

    return {
        "total_books":      total_books,
        "total_users":      total_users,
        "total_students":   total_students,
        "total_librarians": total_librarians,
        "active_borrows":   active_borrows,
        "overdue_count":    overdue_count,
        "total_fines":      round(total_fines, 2),
        "collected_fines":  round(collected_fines, 2),
        "available_books":  int(available_books),
    }


def get_recent_borrows(limit: int = 8):
    """Latest borrow records for the dashboard table."""
    return (
        BorrowRecord.query
        .order_by(BorrowRecord.borrow_date.desc())
        .limit(limit)
        .all()
    )


def get_recent_activity(limit: int = 10):
    """Latest activity logs."""
    return (
        ActivityLog.query
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
        .all()
    )


def get_low_stock_books(limit: int = 5):
    """Books with less than 20% copies available."""
    books = Book.query.all()
    low = [b for b in books if b.is_low_stock]
    return low[:limit]


def get_monthly_borrows_chart() -> dict:
    """
    Returns borrow counts for last 6 months.
    Used to draw the Chart.js line chart.
    """
    labels = []
    data   = []
    now    = datetime.now(timezone.utc)

    for i in range(5, -1, -1):
        month_start = (now - timedelta(days=i * 30)).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        month_end = (month_start + timedelta(days=32)).replace(day=1)

        count = BorrowRecord.query.filter(
            BorrowRecord.borrow_date >= month_start,
            BorrowRecord.borrow_date < month_end,
        ).count()

        labels.append(month_start.strftime("%b %Y"))
        data.append(count)

    return {"labels": labels, "data": data}


def get_category_chart() -> dict:
    """
    Returns book count per category for the pie chart.
    """
    from models import Category
    categories = Category.query.all()
    labels = [c.name for c in categories]
    data   = [c.books.count() for c in categories]
    return {"labels": labels, "data": data}


def get_top_borrowed_books(limit: int = 5):
    """Most borrowed books of all time."""
    results = (
        db.session.query(Book, func.count(BorrowRecord.id).label("borrow_count"))
        .join(BorrowRecord, Book.id == BorrowRecord.book_id)
        .group_by(Book.id)
        .order_by(func.count(BorrowRecord.id).desc())
        .limit(limit)
        .all()
    )
    return results


# ── Private helpers ────────────────────────────────────────────────────────

def _get_overdue_count() -> int:
    now = datetime.now(timezone.utc)
    records = BorrowRecord.query.filter_by(status="borrowed").all()
    return sum(1 for r in records if r.due_date and
               r.due_date.replace(tzinfo=timezone.utc) < now)


def _get_total_fines() -> float:
    result = db.session.query(
        func.sum(BorrowRecord.fine_amount)
    ).scalar()
    return result or 0.0


def _get_collected_fines() -> float:
    result = db.session.query(
        func.sum(FinePayment.amount)
    ).scalar()
    return result or 0.0