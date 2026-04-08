from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from functools import wraps
from app.admin import admin_bp
from app import db
from sqlalchemy import func
from app.models import User, Book, BorrowRequest, Notification

CATEGORIES = ['Academic', 'Fiction', 'Non-Fiction', 'Technology', 'Religion', 'Other']


# ── ADMIN GUARD DECORATOR ────────────────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated


def send_notification(user_id, message):
    notif = Notification(user_id=user_id, message=message)
    db.session.add(notif)


# ── DASHBOARD ────────────────────────────────────────────────────
@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    total_users   = User.query.filter_by(role='member').count()
    total_books   = Book.query.filter_by(is_deleted=False).count()
    active_borrows= BorrowRequest.query.filter_by(status='accepted').count()
    pending_reqs  = BorrowRequest.query.filter_by(status='pending').count()
    blocked_users = User.query.filter_by(is_blocked=True).count()
    digital_books = Book.query.filter_by(book_type='digital', is_deleted=False).count()
    physical_books= Book.query.filter_by(book_type='physical', is_deleted=False).count()

    # Recent activity: last 8 borrow requests
    recent_requests = BorrowRequest.query\
        .order_by(BorrowRequest.created_at.desc()).limit(8).all()

    # Recent users: last 6
    recent_users = User.query\
        .order_by(User.created_at.desc()).limit(6).all()

    # Books by category for chart
    category_data = []
    for cat in CATEGORIES:
        count = Book.query.filter_by(category=cat, is_deleted=False).count()
        if count > 0:
            category_data.append({'category': cat, 'count': count})

    # Request status breakdown
    req_status = {
        'pending'  : BorrowRequest.query.filter_by(status='pending').count(),
        'accepted' : BorrowRequest.query.filter_by(status='accepted').count(),
        'rejected' : BorrowRequest.query.filter_by(status='rejected').count(),
        'completed': BorrowRequest.query.filter_by(status='completed').count(),
    }

    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           total_books=total_books,
                           active_borrows=active_borrows,
                           pending_reqs=pending_reqs,
                           blocked_users=blocked_users,
                           digital_books=digital_books,
                           physical_books=physical_books,
                           recent_requests=recent_requests,
                           recent_users=recent_users,
                           category_data=category_data,
                           req_status=req_status)


# ── MANAGE ALL BOOKS ─────────────────────────────────────────────
@admin_bp.route('/books')
@login_required
@admin_required
def manage_books():
    search    = request.args.get('search', '').strip()
    category  = request.args.get('category', '')
    book_type = request.args.get('type', '')
    status    = request.args.get('status', '')
    page      = request.args.get('page', 1, type=int)

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
    if status:
        query = query.filter_by(status=status)

    pagination = query.order_by(Book.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False)

    return render_template('admin/manage_books.html',
                           books=pagination.items,
                           pagination=pagination,
                           categories=CATEGORIES,
                           search=search,
                           selected_category=category,
                           selected_type=book_type,
                           selected_status=status)


# ── EDIT BOOK (admin) ────────────────────────────────────────────
@admin_bp.route('/books/edit/<int:book_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_book(book_id):
    book   = Book.query.filter_by(id=book_id, is_deleted=False).first_or_404()
    errors = {}

    if request.method == 'POST':
        title    = request.form.get('title',    '').strip()
        author   = request.form.get('author',   '').strip()
        category = request.form.get('category', '').strip()
        location = request.form.get('location', '').strip()

        if not title:   errors['title']    = 'Title is required.'
        if not author:  errors['author']   = 'Author is required.'
        if category not in CATEGORIES:
            errors['category'] = 'Select a valid category.'
        if book.book_type == 'physical' and not location:
            errors['location'] = 'Location is required.'

        if not errors:
            book.title    = title
            book.author   = author
            book.category = category
            if book.book_type == 'physical':
                book.location = location
            db.session.commit()
            flash(f'"{book.title}" updated successfully.', 'success')
            return redirect(url_for('admin.manage_books'))

    return render_template('admin/edit_book.html',
                           book=book, errors=errors, categories=CATEGORIES)


# ── DELETE BOOK (admin / soft delete) ────────────────────────────
@admin_bp.route('/books/delete/<int:book_id>', methods=['POST'])
@login_required
@admin_required
def delete_book(book_id):
    book = Book.query.filter_by(id=book_id, is_deleted=False).first_or_404()
    book.is_deleted = True

    # Cancel any pending/accepted requests
    active_reqs = BorrowRequest.query.filter(
        BorrowRequest.book_id == book_id,
        BorrowRequest.status.in_(['pending', 'accepted'])
    ).all()
    for req in active_reqs:
        req.status = 'rejected'
        send_notification(
            req.borrower_id,
            f'The book "{book.title}" you requested has been removed by an administrator.'
        )

    send_notification(
        book.owner_id,
        f'Your book "{book.title}" has been removed by an administrator for violating platform guidelines.'
    )

    db.session.commit()
    flash(f'"{book.title}" has been removed and the owner notified.', 'success')
    return redirect(url_for('admin.manage_books'))


# ── MANAGE USERS ─────────────────────────────────────────────────
@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    search = request.args.get('search', '').strip()
    role   = request.args.get('role', '')
    status = request.args.get('status', '')
    page   = request.args.get('page', 1, type=int)

    # Base query with pre‑calculated counts
    query = db.session.query(
        User,
        func.count(Book.id.distinct()).label('book_count'),
        func.count(BorrowRequest.id.distinct()).label('borrow_count')
    ).outerjoin(Book, (Book.owner_id == User.id) & (Book.is_deleted == False))\
     .outerjoin(BorrowRequest, BorrowRequest.borrower_id == User.id)\
     .group_by(User.id)

    # Apply filters (same as before)
    if search:
        query = query.filter(
            db.or_(
                User.name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )
    if role:
        query = query.filter(User.role == role)
    if status == 'blocked':
        query = query.filter(User.is_blocked == True)
    elif status == 'active':
        query = query.filter(User.is_blocked == False)

    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False)

    # Extract User objects from the result tuples
    users_with_counts = pagination.items  # list of (User, book_count, borrow_count)
    users = [item[0] for item in users_with_counts]

    # Optionally attach counts as attributes for template access
    for (user, book_count, borrow_count) in users_with_counts:
        user.book_count = book_count
        user.borrow_count = borrow_count

    return render_template('admin/manage_users.html',
                           users=users,
                           pagination=pagination,
                           search=search,
                           selected_role=role,
                           selected_status=status)


# ── BLOCK / UNBLOCK USER ─────────────────────────────────────────
@admin_bp.route('/users/block/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_block(user_id):
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash('You cannot block your own account.', 'warning')
        return redirect(url_for('admin.manage_users'))

    if user.is_admin():
        flash('Admin accounts cannot be blocked.', 'warning')
        return redirect(url_for('admin.manage_users'))

    user.is_blocked = not user.is_blocked
    action = 'blocked' if user.is_blocked else 'unblocked'
    db.session.commit()
    flash(f'{user.name} has been {action}.', 'success')
    return redirect(url_for('admin.manage_users'))


# ── REPORTS ──────────────────────────────────────────────────────
@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    from datetime import datetime, timedelta
    from sqlalchemy import func, extract

    # Summary stats
    total_users = User.query.filter_by(role='member').count()
    total_books = Book.query.filter_by(is_deleted=False).count()
    active_borrows = BorrowRequest.query.filter_by(status='accepted').count()
    completed = BorrowRequest.query.filter_by(status='completed').count()

    # Monthly new users (last 6 months)
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    monthly_users = db.session.query(
        func.strftime('%Y-%m', User.created_at).label('month'),
        func.count(User.id).label('count')
    ).filter(User.created_at >= six_months_ago)\
     .group_by('month')\
     .order_by('month').all()
    monthly_users = [{'month': m, 'count': c} for m, c in monthly_users]

    # Monthly new books (last 6 months)
    monthly_books = db.session.query(
        func.strftime('%Y-%m', Book.created_at).label('month'),
        func.count(Book.id).label('count')
    ).filter(Book.created_at >= six_months_ago, Book.is_deleted == False)\
     .group_by('month')\
     .order_by('month').all()
    monthly_books = [{'month': m, 'count': c} for m, c in monthly_books]

    # Request status breakdown (template expects lowercase keys)
    status_data = {
        'pending': BorrowRequest.query.filter_by(status='pending').count(),
        'accepted': BorrowRequest.query.filter_by(status='accepted').count(),
        'rejected': BorrowRequest.query.filter_by(status='rejected').count(),
        'completed': BorrowRequest.query.filter_by(status='completed').count(),
    }

    # Book type data
    physical_count = Book.query.filter_by(book_type='physical', is_deleted=False).count()
    digital_count = Book.query.filter_by(book_type='digital', is_deleted=False).count()
    type_data = {
        'physical': physical_count,
        'digital': digital_count
    }

    # Top borrowers (full User objects)
    top_borrowers = db.session.query(
        User, func.count(BorrowRequest.id).label('count')
    ).join(BorrowRequest, BorrowRequest.borrower_id == User.id)\
     .group_by(User.id)\
     .order_by(func.count(BorrowRequest.id).desc())\
     .limit(10).all()

    # Top owners (full User objects)
    top_owners = db.session.query(
        User, func.count(Book.id).label('count')
    ).join(Book, Book.owner_id == User.id)\
     .filter(Book.is_deleted == False)\
     .group_by(User.id)\
     .order_by(func.count(Book.id).desc())\
     .limit(10).all()

    return render_template('admin/reports.html',
                           total_users=total_users,
                           total_books=total_books,
                           active_borrows=active_borrows,
                           completed=completed,           # matches template
                           monthly_users=monthly_users,
                           monthly_books=monthly_books,
                           status_data=status_data,
                           type_data=type_data,
                           top_borrowers=top_borrowers,
                           top_owners=top_owners)

@admin_bp.route('/users/promote/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def promote_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot promote yourself.", "warning")
        return redirect(url_for('admin.manage_users'))
    user.role = 'admin'
    db.session.commit()
    flash(f"{user.name} promoted to admin.", "success")
    return redirect(url_for('admin.manage_users'))