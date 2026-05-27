from flask_mail import Message
from app import mail
from flask import current_app
from datetime import date


def send_due_reminder(user, loan):
    """Send email reminder for books due tomorrow."""
    try:
        msg = Message(
            subject='Library Reminder: Book Due Tomorrow',
            recipients=[user.email]
        )
        msg.body = f"""
Dear {user.name},

This is a reminder that the following book is due tomorrow:

  Title:     {loan.book.title}
  Author:    {loan.book.author}
  Due Date:  {loan.due_date.strftime('%Y-%m-%d')}

Please return it on time to avoid a fine of ¥0.50 per day.

Thank you,
Library Management System
        """
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f'Email error: {e}')
        return False


def send_overdue_notice(user, loan):
    """Send email notice for overdue books."""
    try:
        overdue_days = (date.today() - loan.due_date).days
        fine = loan.calculate_fine()
        msg = Message(
            subject='Library Notice: Overdue Book',
            recipients=[user.email]
        )
        msg.body = f"""
Dear {user.name},

The following book is OVERDUE:

  Title:        {loan.book.title}
  Author:       {loan.book.author}
  Due Date:     {loan.due_date.strftime('%Y-%m-%d')}
  Days Overdue: {overdue_days}
  Current Fine: ¥{fine:.2f}

Please return it as soon as possible.

Thank you,
Library Management System
        """
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f'Email error: {e}')
        return False


def check_and_send_reminders(app):
    """Check all active loans and send reminders. Call this daily."""
    with app.app_context():
        from app.models import Loan, User
        from datetime import timedelta
        tomorrow = date.today() + timedelta(days=1)

        # Due tomorrow reminders
        due_tomorrow = Loan.query.filter_by(
            status='borrowed', due_date=tomorrow).all()
        for loan in due_tomorrow:
            send_due_reminder(loan.member, loan)

        # Overdue notices
        overdue = Loan.query.filter(
            Loan.status.in_(['borrowed', 'overdue']),
            Loan.due_date < date.today()
        ).all()
        for loan in overdue:
            send_overdue_notice(loan.member, loan)


def get_dashboard_stats():
    """Return general stats for admin dashboard."""
    from app.models import Book, Loan, User, Fine
    return {
        'total_books': Book.query.count(),
        'available_books': Book.query.filter_by(status='available').count(),
        'borrowed_books': Book.query.filter_by(status='borrowed').count(),
        'total_members': User.query.filter_by(role='member').count(),
        'active_members': User.query.filter_by(role='member', status='active').count(),
        'pending_members': User.query.filter_by(role='member', status='pending').count(),
        'active_loans': Loan.query.filter_by(status='borrowed').count(),
        'overdue_loans': Loan.query.filter(
            Loan.status.in_(['borrowed', 'overdue']),
            Loan.due_date < date.today()
        ).count(),
        'unpaid_fines': Fine.query.filter_by(is_paid=False).count(),
    }