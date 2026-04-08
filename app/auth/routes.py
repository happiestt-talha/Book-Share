from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.auth import auth_bp
from app import db
from app.models import User


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('books.browse'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        errors = {}

        if not name or len(name) < 2:
            errors['name'] = 'Name must be at least 2 characters.'
        if not email or '@' not in email:
            errors['email'] = 'Enter a valid email address.'
        if User.query.filter_by(email=email).first():
            errors['email'] = 'This email is already registered.'
        if not password or len(password) < 8:
            errors['password'] = 'Password must be at least 8 characters.'
        if password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match.'

        if errors:
            return render_template('auth/register.html', errors=errors,
                                   form_data={'name': name, 'email': email})

        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role='member'
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash(f'Welcome to BookShare, {user.name}!', 'success')
        return redirect(url_for('books.browse'))

    return render_template('auth/register.html', errors={}, form_data={})


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('books.browse'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash('Invalid email or password.', 'danger')
            return render_template('auth/login.html', form_data={'email': email})

        if user.is_blocked:
            flash('Your account has been suspended. Please contact support.', 'danger')
            return render_template('auth/login.html', form_data={'email': email})

        login_user(user, remember=remember)
        next_page = request.args.get('next')
        flash(f'Welcome back, {user.name}!', 'success')
        return redirect(next_page or url_for('books.browse'))

    return render_template('auth/login.html', form_data={})


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    errors = {}
    if request.method == 'POST':
        name  = request.form.get('name',  '').strip()
        phone = request.form.get('phone', '').strip()
        city  = request.form.get('city',  '').strip()

        if not name or len(name) < 2:
            errors['name'] = 'Name must be at least 2 characters.'

        if not errors:
            current_user.name  = name
            current_user.phone = phone or None
            current_user.city  = city  or None
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html', errors=errors)


@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    errors = {}
    current_pw  = request.form.get('current_password', '')
    new_pw      = request.form.get('new_password', '')
    confirm_new = request.form.get('confirm_new', '')

    if not check_password_hash(current_user.password, current_pw):
        errors['current_password'] = 'Current password is incorrect.'
    if len(new_pw) < 8:
        errors['new_password'] = 'New password must be at least 8 characters.'
    if new_pw != confirm_new:
        errors['confirm_new'] = 'Passwords do not match.'

    if errors:
        flash('Please fix the errors below.', 'danger')
        return render_template('auth/profile.html', errors=errors)

    current_user.password = generate_password_hash(new_pw)
    db.session.commit()
    flash('Password changed successfully!', 'success')
    return redirect(url_for('auth.profile'))