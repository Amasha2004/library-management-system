from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Loan, Book, User, Fine
from datetime import date, timedelta

loans = Blueprint('loans', __name__)


@loans.route('/member/dashboard')
@login_required
def member_dashboard():
    if current_user.role != 'member':
        return redirect(url_for('auth.dashboard'))
    active_loans = Loan.query.filter_by(
        user_id=current_user.id, status='borrowed').all()
    loan_history = Loan.query.filter_by(
        user_id=current_user.id, status='returned').order_by(Loan.return_date.desc()).limit(5).all()
    overdue = [l for l in active_loans if l.due_date < date.today()]
    return render_template('loans/member_dashboard.html',
                           active_loans=active_loans,
                           loan_history=loan_history,
                           overdue=overdue,
                           today=date.today())


@loans.route('/loans/borrow/<int:book_id>', methods=['POST'])
@login_required
def borrow_book(book_id):
    if current_user.role != 'member':
        flash('Only members can borrow books.', 'danger')
        return redirect(url_for('books.book_list'))

    # Check borrow limit
    active_count = Loan.query.filter_by(
        user_id=current_user.id, status='borrowed').count()
    if active_count >= 5:
        flash('You have reached the maximum borrow limit of 5 books.', 'danger')
        return redirect(url_for('books.book_list'))

    book = Book.query.get_or_404(book_id)
    if book.status != 'available':
        flash('This book is not available for borrowing.', 'danger')
        return redirect(url_for('books.book_list'))

    loan = Loan(
        user_id=current_user.id,
        book_id=book.id,
        borrow_date=date.today(),
        due_date=date.today() + timedelta(days=14),
        status='borrowed'
    )
    book.status = 'borrowed'
    db.session.add(loan)
    db.session.commit()
    flash(f'You borrowed "{book.title}". Due date: {loan.due_date.strftime("%Y-%m-%d")}', 'success')
    return redirect(url_for('loans.member_dashboard'))


@loans.route('/loans/return/<int:loan_id>', methods=['POST'])
@login_required
def return_book(loan_id):
    if current_user.role not in ['admin', 'librarian']:
        flash('Only librarians or admins can process returns.', 'danger')
        return redirect(url_for('auth.dashboard'))

    loan = Loan.query.get_or_404(loan_id)
    if loan.status == 'returned':
        flash('This book has already been returned.', 'warning')
        return redirect(url_for('loans.all_loans'))

    loan.return_date = date.today()
    loan.status = 'returned'
    loan.book.status = 'available'

    # Calculate fine
    fine_amount = loan.calculate_fine()
    loan.fine_amount = fine_amount
    if fine_amount > 0:
        fine = Fine(loan_id=loan.id, amount=fine_amount)
        db.session.add(fine)
        flash(f'Book returned. Overdue fine: ¥{fine_amount:.2f}', 'warning')
    else:
        flash(f'Book "{loan.book.title}" returned successfully. No fine.', 'success')

    db.session.commit()
    return redirect(url_for('loans.all_loans'))


@loans.route('/loans/all')
@login_required
def all_loans():
    if current_user.role not in ['admin', 'librarian']:
        return redirect(url_for('auth.dashboard'))
    status_filter = request.args.get('status', '')
    query = request.args.get('q', '')
    loans_query = Loan.query.join(User).join(Book)
    if status_filter:
        loans_query = loans_query.filter(Loan.status == status_filter)
    if query:
        loans_query = loans_query.filter(
            User.name.ilike(f'%{query}%') | Book.title.ilike(f'%{query}%')
        )
    all_loans_list = loans_query.order_by(Loan.borrow_date.desc()).all()
    return render_template('loans/all_loans.html',
                           loans=all_loans_list,
                           status_filter=status_filter,
                           query=query,
                           today=date.today())


@loans.route('/loans/history')
@login_required
def loan_history():
    if current_user.role == 'member':
        history = Loan.query.filter_by(user_id=current_user.id).order_by(
            Loan.borrow_date.desc()).all()
    else:
        history = Loan.query.order_by(Loan.borrow_date.desc()).all()
    return render_template('loans/loan_history.html',
                           loans=history, today=date.today())


@loans.route('/loans/overdue')
@login_required
def overdue_loans():
    if current_user.role not in ['admin', 'librarian']:
        return redirect(url_for('auth.dashboard'))
    overdue_list = Loan.query.filter(
        Loan.status == 'borrowed',
        Loan.due_date < date.today()
    ).all()
    # Update status to overdue
    for loan in overdue_list:
        loan.status = 'overdue'
    db.session.commit()
    return render_template('loans/overdue_loans.html',
                           loans=overdue_list, today=date.today())


@loans.route('/loans/fines')
@login_required
def fines_list():
    if current_user.role not in ['admin', 'librarian']:
        return redirect(url_for('auth.dashboard'))
    fines = Fine.query.filter_by(is_paid=False).all()
    return render_template('loans/fines_list.html', fines=fines)


@loans.route('/loans/fines/pay/<int:fine_id>', methods=['POST'])
@login_required
def pay_fine(fine_id):
    if current_user.role not in ['admin', 'librarian']:
        return redirect(url_for('auth.dashboard'))
    fine = Fine.query.get_or_404(fine_id)
    fine.is_paid = True
    fine.loan.fine_paid = True
    db.session.commit()
    flash(f'Fine of ¥{fine.amount:.2f} marked as paid.', 'success')
    return redirect(url_for('loans.fines_list'))