from flask import redirect, url_for, flash
from flask_login import login_required
from app.borrow import borrow_bp


@borrow_bp.route('/request/<int:book_id>', methods=['POST'])
@login_required
def request_borrow(book_id):
    flash('Borrow request feature coming soon!', 'info')
    return redirect(url_for('books.detail', book_id=book_id))