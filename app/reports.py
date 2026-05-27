from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from app import db
from app.models import Loan, Book, User, Fine
from datetime import date, datetime, timedelta
import csv
import io

reports = Blueprint('reports', __name__)


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role != 'admin':
            flash('Access denied. Admins only.', 'danger')
            return redirect(url_for('auth.dashboard'))
        return f(*args, **kwargs)
    return decorated


@reports.route('/reports')
@login_required
@admin_required
def reports_home():
    return render_template('reports/reports_home.html')


@reports.route('/reports/most-borrowed')
@login_required
@admin_required
def most_borrowed():
    results = db.session.query(
        Book.title, Book.author, Book.category,
        db.func.count(Loan.id).label('borrow_count')
    ).join(Loan, Book.id == Loan.book_id)\
     .group_by(Book.id)\
     .order_by(db.func.count(Loan.id).desc())\
     .limit(20).all()
    return render_template('reports/most_borrowed.html', results=results)


@reports.route('/reports/overdue-members')
@login_required
@admin_required
def overdue_members():
    overdue = db.session.query(User, Loan, Book).join(
        Loan, User.id == Loan.user_id
    ).join(
        Book, Book.id == Loan.book_id
    ).filter(
        Loan.status.in_(['borrowed', 'overdue']),
        Loan.due_date < date.today()
    ).order_by(Loan.due_date.asc()).all()
    return render_template('reports/overdue_members.html',
                           overdue=overdue, today=date.today())


@reports.route('/reports/daily-transactions')
@login_required
@admin_required
def daily_transactions():
    selected_date = request.args.get('date', date.today().isoformat())
    try:
        report_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except ValueError:
        report_date = date.today()

    borrowed_today = Loan.query.filter_by(borrow_date=report_date).all()
    returned_today = Loan.query.filter_by(return_date=report_date).all()
    fines_today = Fine.query.filter(
        db.func.date(Fine.created_at) == report_date
    ).all()
    total_fines = sum(f.amount for f in fines_today)

    return render_template('reports/daily_transactions.html',
                           borrowed=borrowed_today,
                           returned=returned_today,
                           fines=fines_today,
                           total_fines=total_fines,
                           report_date=report_date)


@reports.route('/reports/export/most-borrowed')
@login_required
@admin_required
def export_most_borrowed():
    results = db.session.query(
        Book.title, Book.author, Book.category,
        db.func.count(Loan.id).label('borrow_count')
    ).join(Loan, Book.id == Loan.book_id)\
     .group_by(Book.id)\
     .order_by(db.func.count(Loan.id).desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Title', 'Author', 'Category', 'Borrow Count'])
    for r in results:
        writer.writerow([r.title, r.author, r.category, r.borrow_count])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=most_borrowed.csv'}
    )


@reports.route('/reports/export/overdue')
@login_required
@admin_required
def export_overdue():
    overdue = db.session.query(User, Loan, Book).join(
        Loan, User.id == Loan.user_id
    ).join(
        Book, Book.id == Loan.book_id
    ).filter(
        Loan.status.in_(['borrowed', 'overdue']),
        Loan.due_date < date.today()
    ).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Member Name', 'Email', 'Book Title', 'Due Date', 'Days Overdue', 'Fine (¥)'])
    for user, loan, book in overdue:
        days = (date.today() - loan.due_date).days
        fine = loan.calculate_fine()
        writer.writerow([user.name, user.email, book.title,
                         loan.due_date, days, fine])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=overdue_members.csv'}
    )


@reports.route('/reports/export/daily')
@login_required
@admin_required
def export_daily():
    selected_date = request.args.get('date', date.today().isoformat())
    try:
        report_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except ValueError:
        report_date = date.today()

    borrowed_today = Loan.query.filter_by(borrow_date=report_date).all()
    returned_today = Loan.query.filter_by(return_date=report_date).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([f'Daily Transaction Report - {report_date}'])
    writer.writerow([])
    writer.writerow(['--- BORROWED ---'])
    writer.writerow(['Member', 'Book Title', 'Borrow Date', 'Due Date'])
    for loan in borrowed_today:
        writer.writerow([loan.member.name, loan.book.title,
                         loan.borrow_date, loan.due_date])
    writer.writerow([])
    writer.writerow(['--- RETURNED ---'])
    writer.writerow(['Member', 'Book Title', 'Return Date', 'Fine (¥)'])
    for loan in returned_today:
        writer.writerow([loan.member.name, loan.book.title,
                         loan.return_date, loan.fine_amount])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=daily_{report_date}.csv'}
    )