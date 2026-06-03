from app import create_app, db
from app.models import Book, User
from app import bcrypt
from app.auth import create_admin

app = create_app()
with app.app_context():
    db.create_all()
    create_admin()

    books = [
        Book(title='The Great Gatsby', author='F. Scott Fitzgerald', isbn='978-0743273565', category='Fiction'),
        Book(title='To Kill a Mockingbird', author='Harper Lee', isbn='978-0061935466', category='Fiction'),
        Book(title='1984', author='George Orwell', isbn='978-0451524935', category='Dystopian'),
        Book(title='Clean Code', author='Robert C. Martin', isbn='978-0132350884', category='Technology'),
        Book(title='The Pragmatic Programmer', author='David Thomas', isbn='978-0201616224', category='Technology'),
        Book(title='A Brief History of Time', author='Stephen Hawking', isbn='978-0553380163', category='Science'),
        Book(title='Sapiens', author='Yuval Noah Harari', isbn='978-0062316097', category='History'),
        Book(title='The Art of War', author='Sun Tzu', isbn='978-1599869773', category='Philosophy'),
    ]
    for b in books:
        db.session.add(b)

    hashed = bcrypt.generate_password_hash('librarian123').decode('utf-8')
    librarian = User(name='Jane Librarian', email='librarian@library.com',
                     password=hashed, role='librarian', status='active')
    db.session.add(librarian)
    db.session.commit()
    print('Database and sample data created successfully!')