from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()


class Role(db.Model):
    __tablename__ = "roles"
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    users       = db.relationship("User", back_populates="role", lazy="dynamic")

    def __repr__(self):
        return f"<Role {self.name}>"


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id             = db.Column(db.Integer, primary_key=True)
    full_name      = db.Column(db.String(120), nullable=False)
    email          = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash  = db.Column(db.String(256), nullable=False)
    phone          = db.Column(db.String(15))
    avatar         = db.Column(db.String(255), default="default_avatar.png")
    role_id        = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    role           = db.relationship("Role", back_populates="users")
    student_id     = db.Column(db.String(50), unique=True, nullable=True)
    department     = db.Column(db.String(100))
    semester       = db.Column(db.Integer)
    is_active      = db.Column(db.Boolean, default=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=False)
    reset_token        = db.Column(db.String(256), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    created_at     = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at     = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                               onupdate=lambda: datetime.now(timezone.utc))

    borrow_records = db.relationship("BorrowRecord", back_populates="user",
                                     foreign_keys="BorrowRecord.user_id", lazy="dynamic")
    reservations   = db.relationship("Reservation", back_populates="user",
                                     foreign_keys="Reservation.user_id", lazy="dynamic")
    wishlist       = db.relationship("Wishlist", back_populates="user",
                                     foreign_keys="Wishlist.user_id", lazy="dynamic")
    notifications  = db.relationship("Notification", back_populates="user",
                                     foreign_keys="Notification.user_id", lazy="dynamic")
    fine_payments  = db.relationship("FinePayment", back_populates="user",
                                     foreign_keys="FinePayment.user_id", lazy="dynamic")
    activity_logs  = db.relationship("ActivityLog", back_populates="user",
                                     foreign_keys="ActivityLog.user_id", lazy="dynamic")

    def set_password(self, plain_text):
        self.password_hash = bcrypt.generate_password_hash(plain_text).decode("utf-8")

    def check_password(self, plain_text):
        return bcrypt.check_password_hash(self.password_hash, plain_text)

    @property
    def is_super_admin(self):
        return self.role.name == "super_admin"

    @property
    def is_librarian(self):
        return self.role.name == "librarian"

    @property
    def is_student(self):
        return self.role.name == "student"

    def __repr__(self):
        return f"<User {self.email}>"


class Category(db.Model):
    __tablename__ = "categories"
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    icon        = db.Column(db.String(50), default="bi-book")
    books       = db.relationship("Book", back_populates="category", lazy="dynamic")


class Author(db.Model):
    __tablename__ = "authors"
    id    = db.Column(db.Integer, primary_key=True)
    name  = db.Column(db.String(150), nullable=False, index=True)
    bio   = db.Column(db.Text)
    books = db.relationship("Book", back_populates="author", lazy="dynamic")


class Book(db.Model):
    __tablename__ = "books"
    id               = db.Column(db.Integer, primary_key=True)
    title            = db.Column(db.String(255), nullable=False, index=True)
    isbn             = db.Column(db.String(20), unique=True, nullable=True)
    description      = db.Column(db.Text)
    cover_image      = db.Column(db.String(255), default="default_cover.png")
    qr_code          = db.Column(db.String(255))
    total_copies     = db.Column(db.Integer, default=1, nullable=False)
    available_copies = db.Column(db.Integer, default=1, nullable=False)
    publisher        = db.Column(db.String(150))
    published_year   = db.Column(db.Integer)
    language         = db.Column(db.String(50), default="English")
    pages            = db.Column(db.Integer)
    edition          = db.Column(db.String(50))
    location         = db.Column(db.String(100))
    category_id      = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    author_id        = db.Column(db.Integer, db.ForeignKey("authors.id"), nullable=False)
    category         = db.relationship("Category", back_populates="books")
    author           = db.relationship("Author", back_populates="books")
    borrow_records   = db.relationship("BorrowRecord", back_populates="book", lazy="dynamic")
    reservations     = db.relationship("Reservation", back_populates="book", lazy="dynamic")
    wishlist_entries = db.relationship("Wishlist", back_populates="book", lazy="dynamic")
    created_at       = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    @property
    def is_available(self):
        return self.available_copies > 0

    @property
    def is_low_stock(self):
        if self.total_copies == 0:
            return True
        return (self.available_copies / self.total_copies) < 0.2


class BorrowRecord(db.Model):
    __tablename__ = "borrow_records"
    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    book_id      = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    issued_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    borrow_date  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    due_date     = db.Column(db.DateTime, nullable=False)
    return_date  = db.Column(db.DateTime, nullable=True)
    status       = db.Column(db.String(20), default="borrowed", nullable=False)
    fine_amount  = db.Column(db.Float, default=0.0)
    fine_paid    = db.Column(db.Boolean, default=False)
    notes        = db.Column(db.Text)
    user         = db.relationship("User", foreign_keys=[user_id], back_populates="borrow_records")
    book         = db.relationship("Book", back_populates="borrow_records")
    issued_by    = db.relationship("User", foreign_keys=[issued_by_id])

    @property
    def is_overdue(self):
        if self.return_date:
            return False
        return datetime.now(timezone.utc) > self.due_date.replace(tzinfo=timezone.utc)

    @property
    def days_overdue(self):
        if not self.is_overdue:
            return 0
        return (datetime.now(timezone.utc) - self.due_date.replace(tzinfo=timezone.utc)).days


class Reservation(db.Model):
    __tablename__ = "reservations"
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    book_id     = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    reserved_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at  = db.Column(db.DateTime, nullable=False)
    status      = db.Column(db.String(20), default="active")
    user        = db.relationship("User", back_populates="reservations")
    book        = db.relationship("Book", back_populates="reservations")


class Wishlist(db.Model):
    __tablename__ = "wishlist"
    id       = db.Column(db.Integer, primary_key=True)
    user_id  = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    book_id  = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    added_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user     = db.relationship("User", back_populates="wishlist")
    book     = db.relationship("Book", back_populates="wishlist_entries")
    __table_args__ = (db.UniqueConstraint("user_id", "book_id", name="uq_user_book_wishlist"),)


class Notification(db.Model):
    __tablename__ = "notifications"
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title      = db.Column(db.String(150), nullable=False)
    message    = db.Column(db.Text, nullable=False)
    type       = db.Column(db.String(30), default="info")
    is_read    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user       = db.relationship("User", back_populates="notifications")


class FinePayment(db.Model):
    __tablename__ = "fine_payments"
    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    borrow_record_id = db.Column(db.Integer, db.ForeignKey("borrow_records.id"), nullable=False)
    amount           = db.Column(db.Float, nullable=False)
    paid_at          = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    collected_by_id  = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    method           = db.Column(db.String(30), default="cash")
    user             = db.relationship("User", foreign_keys=[user_id], back_populates="fine_payments")
    collected_by     = db.relationship("User", foreign_keys=[collected_by_id])
    borrow_record    = db.relationship("BorrowRecord")


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action      = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    ip_address  = db.Column(db.String(45))
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user        = db.relationship("User", back_populates="activity_logs")