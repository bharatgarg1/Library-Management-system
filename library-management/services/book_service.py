"""
services/book_service.py
─────────────────────────
Business logic for book management.
"""

from models import db, Book, Author, Category
from utils.file_helper import save_cover_image, delete_file


def get_or_create_author(name: str) -> Author:
    """Find existing author or create a new one."""
    author = Author.query.filter_by(name=name.strip()).first()
    if not author:
        author = Author(name=name.strip())
        db.session.add(author)
        db.session.flush()
    return author


def create_book(form_data: dict, cover_file=None) -> Book:
    """Create a new book record."""
    author = get_or_create_author(form_data["author_name"])

    cover_filename = save_cover_image(cover_file) or "default_cover.png"

    book = Book(
        title          = form_data["title"].strip(),
        isbn           = form_data.get("isbn") or None,
        description    = form_data.get("description") or None,
        author_id      = author.id,
        category_id    = form_data["category_id"],
        publisher      = form_data.get("publisher") or None,
        published_year = form_data.get("published_year") or None,
        language       = form_data.get("language") or "English",
        pages          = form_data.get("pages") or None,
        edition        = form_data.get("edition") or None,
        location       = form_data.get("location") or None,
        total_copies   = form_data["total_copies"],
        available_copies = form_data["total_copies"],
        cover_image    = cover_filename,
    )
    db.session.add(book)
    db.session.commit()
    return book


def update_book(book: Book, form_data: dict, cover_file=None) -> Book:
    """Update an existing book."""
    author = get_or_create_author(form_data["author_name"])

    if cover_file and cover_file.filename:
        delete_file(book.cover_image)
        book.cover_image = save_cover_image(cover_file) or book.cover_image

    copies_diff = form_data["total_copies"] - book.total_copies
    book.title          = form_data["title"].strip()
    book.isbn           = form_data.get("isbn") or None
    book.description    = form_data.get("description") or None
    book.author_id      = author.id
    book.category_id    = form_data["category_id"]
    book.publisher      = form_data.get("publisher") or None
    book.published_year = form_data.get("published_year") or None
    book.language       = form_data.get("language") or "English"
    book.pages          = form_data.get("pages") or None
    book.edition        = form_data.get("edition") or None
    book.location       = form_data.get("location") or None
    book.total_copies   = form_data["total_copies"]
    book.available_copies = max(0, book.available_copies + copies_diff)

    db.session.commit()
    return book


def delete_book(book: Book) -> None:
    """Delete a book and its cover image."""
    delete_file(book.cover_image)
    db.session.delete(book)
    db.session.commit()


def get_books_paginated(page: int, per_page: int, search: str = "",
                        category_id: int = None):
    """Return paginated books with optional search and category filter."""
    query = Book.query

    if search:
        query = query.filter(
            Book.title.ilike(f"%{search}%")
        )
    if category_id:
        query = query.filter_by(category_id=category_id)

    return query.order_by(Book.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )