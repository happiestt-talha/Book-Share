from app import db
from flask_login import UserMixin
from datetime import datetime


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(150), nullable=False)
    email      = db.Column(db.String(150), unique=True, nullable=False)
    password   = db.Column(db.String(256), nullable=False)
    role       = db.Column(db.String(20), nullable=False, default='member')
    is_blocked = db.Column(db.Boolean, default=False)
    phone      = db.Column(db.String(50),  nullable=True)
    city       = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    books = db.relationship(
        'Book', backref='owner', lazy=True, foreign_keys='Book.owner_id')
    borrow_requests = db.relationship(
        'BorrowRequest', backref='borrower', lazy=True,
        foreign_keys='BorrowRequest.borrower_id')

    def is_admin(self):
        return self.role == 'admin'


class Book(db.Model):
    __tablename__ = 'books'

    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(200), nullable=False)
    author     = db.Column(db.String(200), nullable=False)
    category   = db.Column(db.String(100), nullable=False)
    book_type  = db.Column(db.String(20),  nullable=False)
    location   = db.Column(db.String(200), nullable=True)
    file_link  = db.Column(db.String(500), nullable=True)
    status     = db.Column(db.String(20),  nullable=False, default='available')
    owner_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    borrow_requests = db.relationship('BorrowRequest', backref='book', lazy=True)

    def is_available(self):
        return self.status == 'available' and not self.is_deleted


class BorrowRequest(db.Model):
    __tablename__ = 'borrow_requests'

    id            = db.Column(db.Integer, primary_key=True)
    book_id       = db.Column(db.Integer, db.ForeignKey('books.id'),  nullable=False)
    borrower_id   = db.Column(db.Integer, db.ForeignKey('users.id'),  nullable=False)
    proposed_date = db.Column(db.Date,     nullable=True)
    proposed_time = db.Column(db.Time,     nullable=True)
    location      = db.Column(db.String(200), nullable=True)
    status        = db.Column(db.String(20), nullable=False, default='pending')
    accepted_at   = db.Column(db.DateTime, nullable=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    __tablename__ = 'notifications'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message    = db.Column(db.String(500), nullable=False)
    is_read    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='notifications')