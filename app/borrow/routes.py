from datetime import datetime, date, timedelta
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.borrow import borrow_bp
from app import db
from app.models import Book, BorrowRequest, Notification


def send_notification(user_id, message):
    notif = Notification(user_id=user_id, message=message)
    db.session.add(notif)


def check_auto_returns():
    """Check and process digital books past their 7-day return window."""
    overdue = BorrowRequest.query.filter(
        BorrowRequest.status == 'accepted',
        BorrowRequest.accepted_at.isnot(None)
    ).all()

    for req in overdue:
        if not req.book or req.book.book_type != 'digital':
            continue
        deadline = req.accepted_at + timedelta(days=7)
        if datetime.utcnow() > deadline:
            req.status = 'completed'
            req.book.status = 'available'
            send_notification(
                req.borrower_id,
                f'Your borrow of "{req.book.title}" has been automatically returned after 7 days.'
            )
            send_notification(
                req.book.owner_id,
                f'"{req.book.title}" has been automatically returned by the system.'
            )
    db.session.commit()


# ── REQUEST TO BORROW ────────────────────────────────────────────
@borrow_bp.route('/request/<int:book_id>', methods=['POST'])
@login_required
def request_borrow(book_id):
    book = Book.query.filter_by(id=book_id, is_deleted=False).first_or_404()

    if book.owner_id == current_user.id:
        flash('You cannot borrow your own book.', 'warning')
        return redirect(url_for('books.detail', book_id=book_id))

    if book.status != 'available':
        flash('This book is not available for borrowing right now.', 'warning')
        return redirect(url_for('books.detail', book_id=book_id))

    existing = BorrowRequest.query.filter_by(
        book_id=book_id,
        borrower_id=current_user.id,
        status='pending'
    ).first()
    if existing:
        flash('You already have a pending request for this book.', 'warning')
        return redirect(url_for('books.detail', book_id=book_id))

    proposed_date = None
    proposed_time = None
    location      = None

    if book.book_type == 'physical':
        date_str = request.form.get('proposed_date', '').strip()
        time_str = request.form.get('proposed_time', '').strip()
        location = request.form.get('location', '').strip()

        if not date_str or not time_str or not location:
            flash('Please fill in all scheduling details for a physical book.', 'danger')
            return redirect(url_for('books.detail', book_id=book_id))

        try:
            proposed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            if proposed_date < date.today():
                flash('Proposed date must be in the future.', 'danger')
                return redirect(url_for('books.detail', book_id=book_id))
        except ValueError:
            flash('Invalid date format.', 'danger')
            return redirect(url_for('books.detail', book_id=book_id))

        try:
            proposed_time = datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            flash('Invalid time format.', 'danger')
            return redirect(url_for('books.detail', book_id=book_id))

    borrow_req = BorrowRequest(
        book_id=book_id,
        borrower_id=current_user.id,
        proposed_date=proposed_date,
        proposed_time=proposed_time,
        location=location,
        status='pending'
    )
    book.status = 'pending'
    db.session.add(borrow_req)

    send_notification(
        book.owner_id,
        f'{current_user.name} has requested to borrow your book "{book.title}".'
    )

    db.session.commit()
    flash('Your request has been sent to the book owner!', 'success')
    return redirect(url_for('books.detail', book_id=book_id))


# ── ACCEPT REQUEST ───────────────────────────────────────────────
@borrow_bp.route('/accept/<int:req_id>', methods=['POST'])
@login_required
def accept_request(req_id):
    req = BorrowRequest.query.get_or_404(req_id)

    if req.book.owner_id != current_user.id:
        abort(403)

    if req.status != 'pending':
        flash('This request is no longer pending.', 'warning')
        return redirect(url_for('books.dashboard'))

    # Reject all other pending requests for this book
    other_requests = BorrowRequest.query.filter(
        BorrowRequest.book_id == req.book_id,
        BorrowRequest.id != req_id,
        BorrowRequest.status == 'pending'
    ).all()
    for other in other_requests:
        other.status = 'rejected'
        send_notification(
            other.borrower_id,
            f'Your request for "{req.book.title}" was not accepted as the owner chose another borrower.'
        )

    req.status      = 'accepted'
    req.accepted_at = datetime.utcnow()
    req.book.status = 'borrowed'

    send_notification(
        req.borrower_id,
        f'Great news! Your request to borrow "{req.book.title}" has been accepted by {current_user.name}.'
        + (f' Pick up on {req.proposed_date.strftime("%d %b %Y")} at {req.proposed_time.strftime("%I:%M %p")} from {req.location}.'
           if req.proposed_date else ' The digital book is now available for you.')
    )

    db.session.commit()
    flash(f'Request accepted! "{req.book.title}" is now marked as borrowed.', 'success')
    return redirect(url_for('books.dashboard'))


# ── REJECT REQUEST ───────────────────────────────────────────────
@borrow_bp.route('/reject/<int:req_id>', methods=['POST'])
@login_required
def reject_request(req_id):
    req = BorrowRequest.query.get_or_404(req_id)

    if req.book.owner_id != current_user.id:
        abort(403)

    if req.status != 'pending':
        flash('This request is no longer pending.', 'warning')
        return redirect(url_for('books.dashboard'))

    req.status = 'rejected'

    # Only revert book to available if no other pending requests exist
    other_pending = BorrowRequest.query.filter(
        BorrowRequest.book_id == req.book_id,
        BorrowRequest.id != req_id,
        BorrowRequest.status == 'pending'
    ).first()
    if not other_pending:
        req.book.status = 'available'

    send_notification(
        req.borrower_id,
        f'Your request to borrow "{req.book.title}" was not accepted this time. The book may be available again soon.'
    )

    db.session.commit()
    flash('Request rejected. The book is available again.', 'info')
    return redirect(url_for('books.dashboard'))


# ── MARK RETURNED (physical — by owner) ─────────────────────────
@borrow_bp.route('/return/<int:req_id>', methods=['POST'])
@login_required
def mark_returned(req_id):
    req = BorrowRequest.query.get_or_404(req_id)

    is_owner    = req.book.owner_id == current_user.id
    is_borrower = req.borrower_id == current_user.id

    if not (is_owner or is_borrower):
        abort(403)

    if req.status != 'accepted':
        flash('This borrow is not currently active.', 'warning')
        return redirect(url_for('books.dashboard'))

    # Physical: only owner marks returned
    if req.book.book_type == 'physical' and not is_owner:
        flash('Only the book owner can mark a physical book as returned.', 'warning')
        return redirect(url_for('books.dashboard'))

    # Digital: borrower marks returned
    if req.book.book_type == 'digital' and not is_borrower:
        flash('Only the borrower can mark a digital book as returned.', 'warning')
        return redirect(url_for('books.dashboard'))

    req.status      = 'completed'
    req.book.status = 'available'

    if is_owner:
        send_notification(
            req.borrower_id,
            f'"{req.book.title}" has been marked as returned. Thanks for borrowing!'
        )
    else:
        send_notification(
            req.book.owner_id,
            f'{current_user.name} has returned your digital book "{req.book.title}".'
        )

    db.session.commit()
    flash(f'"{req.book.title}" has been marked as returned and is now available again.', 'success')
    return redirect(url_for('books.dashboard'))


# ── PENDING REQUESTS (owner's incoming) ─────────────────────────
@borrow_bp.route('/pending')
@login_required
def pending_requests():
    check_auto_returns()
    reqs = BorrowRequest.query.join(Book).filter(
        Book.owner_id == current_user.id,
        BorrowRequest.status == 'pending'
    ).order_by(BorrowRequest.created_at.desc()).all()
    return render_template('borrow/pending.html', requests=reqs)


# ── MY BORROWS (borrower's active borrows) ───────────────────────
@borrow_bp.route('/my-borrows')
@login_required
def my_borrows():
    check_auto_returns()
    reqs = BorrowRequest.query.filter(
        BorrowRequest.borrower_id == current_user.id,
        BorrowRequest.status == 'accepted'
    ).order_by(BorrowRequest.accepted_at.desc()).all()

    # Attach deadline info
    borrow_data = []
    for req in reqs:
        deadline = None
        days_left = None
        if req.book.book_type == 'digital' and req.accepted_at:
            deadline  = req.accepted_at + timedelta(days=7)
            days_left = (deadline - datetime.utcnow()).days
        borrow_data.append({'req': req, 'deadline': deadline, 'days_left': days_left})

    return render_template('borrow/my_borrows.html', borrow_data=borrow_data)


# ── NOTIFICATIONS ────────────────────────────────────────────────
@borrow_bp.route('/notifications')
@login_required
def notifications():
    notifs = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).all()

    # Mark all as read
    for n in notifs:
        n.is_read = True
    db.session.commit()

    return render_template('borrow/notifications.html', notifications=notifs)