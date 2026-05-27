from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime, date

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(255))
    role = db.Column(db.String(20), nullable=False, default='member')
    # role: 'admin', 'librarian', 'member'
    status = db.Column(db.String(20), nullable=False, default='pending')
    # status: 'pending', 'active', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    loans = db.relationship('Loan', backref='member', lazy=True)

    def __repr__(self):
        return f"User('{self.name}', '{self.email}', '{self.role}')"


class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    category = db.Column(db.String(100))
    cover_image = db.Column(db.String(255), default='default_cover.png')
    status = db.Column(db.String(20), nullable=False, default='available')
    # status: 'available', 'borrowed', 'reserved'
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    loans = db.relationship('Loan', backref='book', lazy=True)

    def __repr__(self):
        return f"Book('{self.title}', '{self.author}', '{self.status}')"


class Loan(db.Model):
    __tablename__ = 'loans'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    borrow_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='borrowed')
    # status: 'borrowed', 'returned', 'overdue'
    fine_amount = db.Column(db.Float, default=0.0)
    fine_paid = db.Column(db.Boolean, default=False)

    def calculate_fine(self):
        if self.return_date and self.return_date > self.due_date:
            overdue_days = (self.return_date - self.due_date).days
            return round(overdue_days * 0.50, 2)
        elif not self.return_date and date.today() > self.due_date:
            overdue_days = (date.today() - self.due_date).days
            return round(overdue_days * 0.50, 2)
        return 0.0

    def __repr__(self):
        return f"Loan(user={self.user_id}, book={self.book_id}, due={self.due_date})"


class Fine(db.Model):
    __tablename__ = 'fines'
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    is_paid = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    loan = db.relationship('Loan', backref='fine_record', lazy=True)

    def __repr__(self):
        return f"Fine(loan={self.loan_id}, amount={self.amount}, paid={self.is_paid})"