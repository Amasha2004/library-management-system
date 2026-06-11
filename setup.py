from app import create_app, db
from app.models import Book, User
from app import bcrypt
from app.auth import create_admin
import os, struct, zlib

app = create_app()
with app.app_context():
    db.create_all()
    create_admin()

    # ── Create librarian ────────────────────────────────────────────
    if not User.query.filter_by(email='librarian@library.com').first():
        hashed = bcrypt.generate_password_hash('librarian123').decode('utf-8')
        librarian = User(name='Jane Librarian', email='librarian@library.com',
                         password=hashed, role='librarian', status='active')
        db.session.add(librarian)
        print('Librarian created!')

    # ── Create sample member ─────────────────────────────────────────
    if not User.query.filter_by(email='member@library.com').first():
        hashed2 = bcrypt.generate_password_hash('member123').decode('utf-8')
        member = User(name='John Member', email='member@library.com',
                      password=hashed2, role='member', status='active')
        db.session.add(member)
        print('Member created!')

    # ── Add all 38 books ─────────────────────────────────────────────
    books = [
        # Fiction
        Book(title='The Great Gatsby', author='F. Scott Fitzgerald', isbn='978-0743273565', category='Fiction'),
        Book(title='To Kill a Mockingbird', author='Harper Lee', isbn='978-0061935466', category='Fiction'),
        Book(title='Pride and Prejudice', author='Jane Austen', isbn='978-0141439518', category='Fiction'),
        Book(title='The Catcher in the Rye', author='J.D. Salinger', isbn='978-0316769174', category='Fiction'),
        Book(title='Brave New World', author='Aldous Huxley', isbn='978-0060850524', category='Fiction'),
        Book(title='The Alchemist', author='Paulo Coelho', isbn='978-0062315007', category='Fiction'),
        Book(title='Harry Potter and the Sorcerer Stone', author='J.K. Rowling', isbn='978-0439708180', category='Fiction'),
        Book(title='The Lord of the Rings', author='J.R.R. Tolkien', isbn='978-0544003415', category='Fiction'),
        # Science
        Book(title='A Brief History of Time', author='Stephen Hawking', isbn='978-0553380163', category='Science'),
        Book(title='The Selfish Gene', author='Richard Dawkins', isbn='978-0198788607', category='Science'),
        Book(title='Cosmos', author='Carl Sagan', isbn='978-0345539434', category='Science'),
        # Technology
        Book(title='Clean Code', author='Robert C. Martin', isbn='978-0132350884', category='Technology'),
        Book(title='The Pragmatic Programmer', author='David Thomas', isbn='978-0201616224', category='Technology'),
        Book(title='Design Patterns', author='Gang of Four', isbn='978-0201633610', category='Technology'),
        Book(title='Introduction to Algorithms', author='Thomas H. Cormen', isbn='978-0262033848', category='Technology'),
        Book(title='The Art of Computer Programming', author='Donald E. Knuth', isbn='978-0201896831', category='Technology'),
        Book(title='Python Crash Course', author='Eric Matthes', isbn='978-1593279288', category='Technology'),
        Book(title='Artificial Intelligence: A Modern Approach', author='Stuart Russell', isbn='978-0134610993', category='Technology'),
        # History
        Book(title='Sapiens', author='Yuval Noah Harari', isbn='978-0062316097', category='History'),
        Book(title='Homo Deus', author='Yuval Noah Harari', isbn='978-0062464316', category='History'),
        Book(title='Guns Germs and Steel', author='Jared Diamond', isbn='978-0393317558', category='History'),
        Book(title='The Silk Roads', author='Peter Frankopan', isbn='978-1101912379', category='History'),
        # Philosophy
        Book(title='The Art of War', author='Sun Tzu', isbn='978-1599869773', category='Philosophy'),
        Book(title='Meditations', author='Marcus Aurelius', isbn='978-0140449334', category='Philosophy'),
        Book(title='Thus Spoke Zarathustra', author='Friedrich Nietzsche', isbn='978-0140441185', category='Philosophy'),
        Book(title='The Republic', author='Plato', isbn='978-0140455113', category='Philosophy'),
        # Business
        Book(title='Think and Grow Rich', author='Napoleon Hill', isbn='978-1585424337', category='Business'),
        Book(title='The 7 Habits of Highly Effective People', author='Stephen Covey', isbn='978-1982137274', category='Business'),
        Book(title='Zero to One', author='Peter Thiel', isbn='978-0804139021', category='Business'),
        Book(title='The Lean Startup', author='Eric Ries', isbn='978-0307887894', category='Business'),
        Book(title='Atomic Habits', author='James Clear', isbn='978-0735211292', category='Business'),
        Book(title='Deep Work', author='Cal Newport', isbn='978-1455586691', category='Business'),
        # Dystopian
        Book(title='1984', author='George Orwell', isbn='978-0451524935', category='Dystopian'),
        Book(title='Fahrenheit 451', author='Ray Bradbury', isbn='978-1451673319', category='Dystopian'),
        Book(title='The Handmaids Tale', author='Margaret Atwood', isbn='978-0385490818', category='Dystopian'),
        # Science Fiction
        Book(title='Dune', author='Frank Herbert', isbn='978-0441013593', category='Science Fiction'),
        Book(title='The Hitchhiker Guide to the Galaxy', author='Douglas Adams', isbn='978-0345391803', category='Science Fiction'),
        Book(title='Ender Game', author='Orson Scott Card', isbn='978-0812550702', category='Science Fiction'),
    ]

    added = 0
    for b in books:
        if not Book.query.filter_by(isbn=b.isbn).first():
            db.session.add(b)
            added += 1

    db.session.commit()
    print(f'Added {added} books!')

    # ── Create default cover image ───────────────────────────────────
    def create_png(width, height, color):
        def chunk(name, data):
            c = struct.pack('>I', len(data)) + name + data
            return c + struct.pack('>I', zlib.crc32(c[4:]) & 0xffffffff)
        raw = b''
        for y in range(height):
            raw += b'\x00'
            for x in range(width):
                raw += bytes(color)
        png = b'\x89PNG\r\n\x1a\n'
        png += chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
        png += chunk(b'IDAT', zlib.compress(raw))
        png += chunk(b'IEND', b'')
        return png

    os.makedirs('app/static/uploads', exist_ok=True)
    cover_path = 'app/static/uploads/default_cover.png'
    if not os.path.exists(cover_path):
        with open(cover_path, 'wb') as f:
            f.write(create_png(200, 280, [26, 35, 126]))
        print('Default cover created!')

    print('\n✅ Setup complete!')
    print('Admin:     admin@library.com / admin123')
    print('Librarian: librarian@library.com / librarian123')
    print('Member:    member@library.com / member123')