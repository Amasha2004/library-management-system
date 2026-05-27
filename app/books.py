from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Book, Loan
import os
from werkzeug.utils import secure_filename

books = Blueprint('books', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def admin_or_librarian_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role not in ['admin', 'librarian']:
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.dashboard'))
        return f(*args, **kwargs)
    return decorated


@books.route('/librarian/dashboard')
@login_required
def librarian_dashboard():
    if current_user.role not in ['admin', 'librarian']:
        return redirect(url_for('auth.dashboard'))
    total_books = Book.query.count()
    available = Book.query.filter_by(status='available').count()
    borrowed = Book.query.filter_by(status='borrowed').count()
    recent_books = Book.query.order_by(Book.added_at.desc()).limit(5).all()
    active_loans = Loan.query.filter_by(status='borrowed').count()
    return render_template('books/librarian_dashboard.html',
                           total_books=total_books,
                           available=available,
                           borrowed=borrowed,
                           recent_books=recent_books,
                           active_loans=active_loans)


@books.route('/books')
@login_required
def book_list():
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    if query:
        books_list = Book.query.filter(
            (Book.title.ilike(f'%{query}%')) |
            (Book.author.ilike(f'%{query}%')) |
            (Book.isbn.ilike(f'%{query}%')) |
            (Book.category.ilike(f'%{query}%'))
        ).all()
    elif category:
        books_list = Book.query.filter_by(category=category).all()
    else:
        books_list = Book.query.order_by(Book.added_at.desc()).all()
    categories = db.session.query(Book.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    return render_template('books/book_list.html',
                           books=books_list, query=query,
                           categories=categories, selected_category=category)


@books.route('/books/add', methods=['GET', 'POST'])
@login_required
@admin_or_librarian_required
def add_book():
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        isbn = request.form.get('isbn')
        category = request.form.get('category')

        existing = Book.query.filter_by(isbn=isbn).first()
        if existing:
            flash('A book with this ISBN already exists.', 'danger')
            return redirect(url_for('books.add_book'))

        cover_filename = 'default_cover.png'
        file = request.files.get('cover_image')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            cover_filename = filename

        book = Book(title=title, author=author, isbn=isbn,
                    category=category, cover_image=cover_filename)
        db.session.add(book)
        db.session.commit()
        flash(f'Book "{title}" added successfully!', 'success')
        return redirect(url_for('books.book_list'))
    return render_template('books/add_book.html')


@books.route('/books/edit/<int:book_id>', methods=['GET', 'POST'])
@login_required
@admin_or_librarian_required
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    if request.method == 'POST':
        book.title = request.form.get('title')
        book.author = request.form.get('author')
        book.isbn = request.form.get('isbn')
        book.category = request.form.get('category')

        file = request.files.get('cover_image')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            book.cover_image = filename

        db.session.commit()
        flash(f'Book "{book.title}" updated successfully!', 'success')
        return redirect(url_for('books.book_list'))
    return render_template('books/edit_book.html', book=book)


@books.route('/books/delete/<int:book_id>', methods=['POST'])
@login_required
def delete_book(book_id):
    if current_user.role != 'admin':
        flash('Only admins can delete books.', 'danger')
        return redirect(url_for('books.book_list'))
    book = Book.query.get_or_404(book_id)
    if book.status == 'borrowed':
        flash('Cannot delete a book that is currently borrowed.', 'danger')
        return redirect(url_for('books.book_list'))
    db.session.delete(book)
    db.session.commit()
    flash(f'Book "{book.title}" deleted.', 'success')
    return redirect(url_for('books.book_list'))


@books.route('/books/<int:book_id>')
@login_required
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template('books/book_detail.html', book=book)