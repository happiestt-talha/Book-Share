import os
import uuid
from flask import render_template, redirect, url_for, flash, request, current_app, send_from_directory, abort
from flask_login import login_required, current_user
from app.books import books_bp
from app import db
from app.models import Book, BorrowRequest, Notification

CATEGORIES = ['Academic', 'Fiction', 'Non-Fiction', 'Technology', 'Religion', 'Other']
BOOK_TYPES = ['physical', 'digital']


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def save_uploaded_file(file):
    ext = file.filename.rsplit('.', 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    file.save(os.path.join(upload_folder, unique_name))
    return unique_name


# ── HOME / BROWSE ────────────────────────────────────────────────
@books_bp.route('/')
def browse():
    search   = request.args.get('search', '').strip()
    category = request.args.get('category', '')
    book_type= request.args.get('type', '')
    avail    = request.args.get('availability', '')
    page     = request.args.get('page', 1, type=int)

    query = Book.query.filter_by(is_deleted=False)

    if search:
        query = query.filter(
            db.or_(
                Book.title.ilike(f'%{search}%'),
                Book.author.ilike(f'%{search}%')
            )
        )
    if category:
        query = query.filter_by(category=category)
    if book_type:
        query = query.filter_by(book_type=book_type)
    if avail:
        query = query.filter_by(status=avail)

    pagination = query.order_by(Book.created_at.desc()).paginate(page=page, per_page=12, error_out=False)
    books = pagination.items

    return render_template('books/browse.html',
                           books=books,
                           pagination=pagination,
                           categories=CATEGORIES,
                           search=search,
                           selected_category=category,
                           selected_type=book_type,
                           selected_avail=avail)


# ── BOOK DETAIL ──────────────────────────────────────────────────
@books_bp.route('/book/<int:book_id>')
def detail(book_id):
    book = Book.query.filter_by(id=book_id, is_deleted=False).first_or_404()
    already_requested = False
    if current_user.is_authenticated:
        already_requested = BorrowRequest.query.filter_by(
            book_id=book_id,
            borrower_id=current_user.id,
            status='pending'
        ).first() is not None
    return render_template('books/detail.html', book=book,
                           already_requested=already_requested)


# ── ADD BOOK ─────────────────────────────────────────────────────
@books_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_book():
    errors = {}
    form_data = {}

    if request.method == 'POST':
        title     = request.form.get('title', '').strip()
        author    = request.form.get('author', '').strip()
        category  = request.form.get('category', '').strip()
        book_type = request.form.get('book_type', '').strip()
        location  = request.form.get('location', '').strip()
        file_link = request.form.get('file_link', '').strip()

        form_data = {'title': title, 'author': author, 'category': category,
                     'book_type': book_type, 'location': location, 'file_link': file_link}

        if not title:       errors['title']    = 'Title is required.'
        if not author:      errors['author']   = 'Author is required.'
        if category not in CATEGORIES: errors['category'] = 'Select a valid category.'
        if book_type not in BOOK_TYPES: errors['book_type'] = 'Select Physical or Digital.'

        if book_type == 'physical' and not location:
            errors['location'] = 'Location is required for physical books.'

        saved_filename = None
        if book_type == 'digital':
            uploaded = request.files.get('file_upload')
            if uploaded and uploaded.filename:
                if not allowed_file(uploaded.filename):
                    errors['file_upload'] = 'Only PDF files are allowed.'
                else:
                    saved_filename = save_uploaded_file(uploaded)
            elif not file_link:
                errors['file_link'] = 'Provide a PDF upload or a download link.'

        if not errors:
            book = Book(
                title=title,
                author=author,
                category=category,
                book_type=book_type,
                location=location if book_type == 'physical' else None,
                file_link=saved_filename or file_link if book_type == 'digital' else None,
                owner_id=current_user.id,
                status='available'
            )
            db.session.add(book)
            db.session.commit()
            flash(f'"{title}" has been listed successfully!', 'success')
            return redirect(url_for('books.my_books'))

    return render_template('books/add_book.html', errors=errors,
                           form_data=form_data, categories=CATEGORIES)


# ── EDIT BOOK ────────────────────────────────────────────────────
@books_bp.route('/edit/<int:book_id>', methods=['GET', 'POST'])
@login_required
def edit_book(book_id):
    book = Book.query.filter_by(id=book_id, is_deleted=False).first_or_404()

    if book.owner_id != current_user.id and not current_user.is_admin():
        abort(403)

    errors = {}

    if request.method == 'POST':
        title    = request.form.get('title', '').strip()
        author   = request.form.get('author', '').strip()
        category = request.form.get('category', '').strip()
        location = request.form.get('location', '').strip()
        file_link= request.form.get('file_link', '').strip()

        if not title:   errors['title']  = 'Title is required.'
        if not author:  errors['author'] = 'Author is required.'
        if category not in CATEGORIES: errors['category'] = 'Select a valid category.'

        if book.book_type == 'physical' and not location:
            errors['location'] = 'Location is required for physical books.'

        if book.book_type == 'digital':
            uploaded = request.files.get('file_upload')
            if uploaded and uploaded.filename:
                if not allowed_file(uploaded.filename):
                    errors['file_upload'] = 'Only PDF files are allowed.'
                else:
                    # delete old file if it was an upload (not an external link)
                    if book.file_link and not book.file_link.startswith('http'):
                        old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], book.file_link)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    book.file_link = save_uploaded_file(uploaded)
            elif file_link:
                book.file_link = file_link

        if not errors:
            book.title    = title
            book.author   = author
            book.category = category
            if book.book_type == 'physical':
                book.location = location
            db.session.commit()
            flash('Book updated successfully!', 'success')
            return redirect(url_for('books.my_books'))

    return render_template('books/edit_book.html', book=book,
                           errors=errors, categories=CATEGORIES)


# ── DELETE BOOK ──────────────────────────────────────────────────
@books_bp.route('/delete/<int:book_id>', methods=['POST'])
@login_required
def delete_book(book_id):
    book = Book.query.filter_by(id=book_id, is_deleted=False).first_or_404()

    if book.owner_id != current_user.id and not current_user.is_admin():
        abort(403)

    active = BorrowRequest.query.filter(
        BorrowRequest.book_id == book_id,
        BorrowRequest.status.in_(['pending', 'accepted'])
    ).first()

    if active:
        flash('Cannot delete a book with active borrow requests. Resolve them first.', 'warning')
        return redirect(url_for('books.my_books'))

    book.is_deleted = True
    db.session.commit()
    flash(f'"{book.title}" has been removed.', 'info')
    return redirect(url_for('books.my_books'))


# ── MY BOOKS ─────────────────────────────────────────────────────
@books_bp.route('/my')
@login_required
def my_books():
    books = Book.query.filter_by(owner_id=current_user.id, is_deleted=False)\
                      .order_by(Book.created_at.desc()).all()
    return render_template('books/my_books.html', books=books)


# ── DASHBOARD (placeholder, built fully in Phase 5) ──────────────
@books_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('books/dashboard.html')


# ── SERVE UPLOADED FILE (only for accepted borrower / owner) ─────
@books_bp.route('/file/<path:filename>')
@login_required
def serve_file(filename):
    # security: only owner or accepted borrower can download
    book = Book.query.filter_by(file_link=filename, is_deleted=False).first_or_404()
    is_owner    = book.owner_id == current_user.id
    is_borrower = BorrowRequest.query.filter_by(
        book_id=book.id,
        borrower_id=current_user.id,
        status='accepted'
    ).first() is not None
    if not (is_owner or is_borrower or current_user.is_admin()):
        abort(403)
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)