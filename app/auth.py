from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt
from app.models import User
from datetime import datetime

auth = Blueprint('auth', __name__)


@auth.route('/', methods=['GET', 'POST'])
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            if user.status == 'pending':
                flash('Your account is pending approval by an admin.', 'warning')
                return redirect(url_for('auth.login'))
            if user.status == 'rejected':
                flash('Your account has been rejected. Contact the library.', 'danger')
                return redirect(url_for('auth.login'))
            login_user(user)
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('auth.dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.register'))

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('Email already registered. Please login.', 'danger')
            return redirect(url_for('auth.register'))

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(
            name=name, email=email, phone=phone,
            address=address, password=hashed_pw,
            role='member', status='pending'
        )
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please wait for admin approval.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('members.admin_dashboard'))
    elif current_user.role == 'librarian':
        return redirect(url_for('books.librarian_dashboard'))
    else:
        return redirect(url_for('loans.member_dashboard'))


@auth.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html', user=current_user)


def create_admin():
    """Run once to create the default admin account."""
    admin = User.query.filter_by(email='admin@library.com').first()
    if not admin:
        hashed_pw = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin = User(
            name='Administrator',
            email='admin@library.com',
            password=hashed_pw,
            role='admin',
            status='active'
        )
        db.session.add(admin)
        db.session.commit()
        print('Admin account created: admin@library.com / admin123')

@auth.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Update basic info
        current_user.name = name
        current_user.phone = phone
        current_user.address = address

        # Update password if provided
        if current_password and new_password:
            if not bcrypt.check_password_hash(current_user.password, current_password):
                flash('Current password is incorrect.', 'danger')
                return redirect(url_for('auth.edit_profile'))
            if new_password != confirm_password:
                flash('New passwords do not match.', 'danger')
                return redirect(url_for('auth.edit_profile'))
            current_user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            flash('Password updated successfully!', 'success')

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/edit_profile.html', user=current_user)