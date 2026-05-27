from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import User, Loan

members = Blueprint('members', __name__)


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role != 'admin':
            flash('Access denied. Admins only.', 'danger')
            return redirect(url_for('auth.dashboard'))
        return f(*args, **kwargs)
    return decorated


@members.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    total_members = User.query.filter_by(role='member').count()
    pending = User.query.filter_by(role='member', status='pending').count()
    active = User.query.filter_by(role='member', status='active').count()
    total_users = User.query.count()
    recent_members = User.query.filter_by(role='member').order_by(User.created_at.desc()).limit(5).all()
    return render_template('members/admin_dashboard.html',
                           total_members=total_members,
                           pending=pending,
                           active=active,
                           total_users=total_users,
                           recent_members=recent_members)


@members.route('/admin/members')
@login_required
@admin_required
def member_list():
    status_filter = request.args.get('status', '')
    query = request.args.get('q', '')
    if status_filter:
        members_list = User.query.filter_by(role='member', status=status_filter).all()
    elif query:
        members_list = User.query.filter(
            User.role == 'member',
            (User.name.ilike(f'%{query}%')) | (User.email.ilike(f'%{query}%'))
        ).all()
    else:
        members_list = User.query.filter_by(role='member').order_by(User.created_at.desc()).all()
    return render_template('members/member_list.html',
                           members=members_list,
                           status_filter=status_filter,
                           query=query)


@members.route('/admin/members/pending')
@login_required
@admin_required
def pending_members():
    pending_list = User.query.filter_by(role='member', status='pending').all()
    return render_template('members/pending_members.html', members=pending_list)


@members.route('/admin/members/approve/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def approve_member(user_id):
    user = User.query.get_or_404(user_id)
    user.status = 'active'
    db.session.commit()
    flash(f'Member "{user.name}" has been approved.', 'success')
    return redirect(url_for('members.pending_members'))


@members.route('/admin/members/reject/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reject_member(user_id):
    user = User.query.get_or_404(user_id)
    user.status = 'rejected'
    db.session.commit()
    flash(f'Member "{user.name}" has been rejected.', 'warning')
    return redirect(url_for('members.pending_members'))


@members.route('/admin/members/<int:user_id>')
@login_required
@admin_required
def member_detail(user_id):
    user = User.query.get_or_404(user_id)
    loans = Loan.query.filter_by(user_id=user_id).order_by(Loan.borrow_date.desc()).all()
    return render_template('members/member_detail.html', user=user, loans=loans)


@members.route('/admin/members/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_member(user_id):
    user = User.query.get_or_404(user_id)
    active_loans = Loan.query.filter_by(user_id=user_id, status='borrowed').count()
    if active_loans > 0:
        flash('Cannot delete member with active loans.', 'danger')
        return redirect(url_for('members.member_list'))
    db.session.delete(user)
    db.session.commit()
    flash(f'Member "{user.name}" deleted.', 'success')
    return redirect(url_for('members.member_list'))


@members.route('/admin/librarians/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_librarian():
    from app import bcrypt
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('Email already registered.', 'danger')
            return redirect(url_for('members.add_librarian'))
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        librarian = User(name=name, email=email, password=hashed_pw,
                         role='librarian', status='active')
        db.session.add(librarian)
        db.session.commit()
        flash(f'Librarian "{name}" added successfully!', 'success')
        return redirect(url_for('members.admin_dashboard'))
    return render_template('members/add_librarian.html')