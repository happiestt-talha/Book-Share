from flask import render_template
from flask_login import login_required
from app.books import books_bp


@books_bp.route('/')
def browse():
    return render_template('books/browse.html')


@books_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('books/dashboard.html')


@books_bp.route('/my')
@login_required
def my_books():
    return render_template('books/my_books.html')