from app import create_app, db
from app.models import Book, User
from app import bcrypt
from app.auth import create_admin
import os, struct, zlib

app = create_app()
with app.app_context():
    db.create_all()
    create_admin()

    # ── Create librarian ─────────────────────────────────────────────
    if not User.query.filter_by(email='librarian@library.com').first():
        hashed = bcrypt.generate_password_hash('librarian123').decode('utf-8')
        librarian = User(
            name='Jane Librarian',
            email='librarian@library.com',
            password=hashed,
            role='librarian',
            status='active'
        )
        db.session.add(librarian)
        print('Librarian created!')

    # ── Create sample member ──────────────────────────────────────────
    if not User.query.filter_by(email='member@library.com').first():
        hashed2 = bcrypt.generate_password_hash('member123').decode('utf-8')
        member = User(
            name='John Member',
            email='member@library.com',
            password=hashed2,
            role='member',
            status='active'
        )
        db.session.add(member)
        print('Member created!')

    db.session.commit()

    # ── Add all 38 books with covers ──────────────────────────────────
    books_data = [
        # Fiction
        ('The Great Gatsby', 'F. Scott Fitzgerald', '978-0743273565', 'Fiction', 'great_gatsby.jpg'),
        ('To Kill a Mockingbird', 'Harper Lee', '978-0061935466', 'Fiction', 'mockingbird.jpg'),
        ('Pride and Prejudice', 'Jane Austen', '978-0141439518', 'Fiction', 'pride_prejudice.jpg'),
        ('The Catcher in the Rye', 'J.D. Salinger', '978-0316769174', 'Fiction', 'catcher_rye.jpg'),
        ('Brave New World', 'Aldous Huxley', '978-0060850524', 'Fiction', 'brave_new_world.jpg'),
        ('The Alchemist', 'Paulo Coelho', '978-0062315007', 'Fiction', 'alchemist.jpg'),
        ('Harry Potter and the Sorcerer Stone', 'J.K. Rowling', '978-0439708180', 'Fiction', 'harry_potter.jpg'),
        ('The Lord of the Rings', 'J.R.R. Tolkien', '978-0544003415', 'Fiction', 'lord_rings.jpg'),
        # Science
        ('A Brief History of Time', 'Stephen Hawking', '978-0553380163', 'Science', 'brief_history.jpg'),
        ('The Selfish Gene', 'Richard Dawkins', '978-0198788607', 'Science', 'selfish_gene.jpg'),
        ('Cosmos', 'Carl Sagan', '978-0345539434', 'Science', 'cosmos.jpg'),
        # Technology
        ('Clean Code', 'Robert C. Martin', '978-0132350884', 'Technology', 'clean_code.jpg'),
        ('The Pragmatic Programmer', 'David Thomas', '978-0201616224', 'Technology', 'pragmatic.jpg'),
        ('Design Patterns', 'Gang of Four', '978-0201633610', 'Technology', 'design_patterns.jpg'),
        ('Introduction to Algorithms', 'Thomas H. Cormen', '978-0262033848', 'Technology', 'algorithms.jpg'),
        ('The Art of Computer Programming', 'Donald E. Knuth', '978-0201896831', 'Technology', 'art_computer.jpg'),
        ('Python Crash Course', 'Eric Matthes', '978-1593279288', 'Technology', 'python_crash.jpg'),
        ('Artificial Intelligence: A Modern Approach', 'Stuart Russell', '978-0134610993', 'Technology', 'ai_modern.jpg'),
        # History
        ('Sapiens', 'Yuval Noah Harari', '978-0062316097', 'History', 'sapiens.jpg'),
        ('Homo Deus', 'Yuval Noah Harari', '978-0062464316', 'History', 'homo_deus.jpg'),
        ('Guns Germs and Steel', 'Jared Diamond', '978-0393317558', 'History', 'guns_germs.jpg'),
        ('The Silk Roads', 'Peter Frankopan', '978-1101912379', 'History', 'silk_roads.jpg'),
        # Philosophy
        ('The Art of War', 'Sun Tzu', '978-1599869773', 'Philosophy', 'art_war.jpg'),
        ('Meditations', 'Marcus Aurelius', '978-0140449334', 'Philosophy', 'meditations.jpg'),
        ('Thus Spoke Zarathustra', 'Friedrich Nietzsche', '978-0140441185', 'Philosophy', 'zarathustra.jpg'),
        ('The Republic', 'Plato', '978-0140455113', 'Philosophy', 'republic.jpg'),
        # Business
        ('Think and Grow Rich', 'Napoleon Hill', '978-1585424337', 'Business', 'think_grow_rich.jpg'),
        ('The 7 Habits of Highly Effective People', 'Stephen Covey', '978-1982137274', 'Business', 'seven_habits.jpg'),
        ('Zero to One', 'Peter Thiel', '978-0804139021', 'Business', 'zero_to_one.jpg'),
        ('The Lean Startup', 'Eric Ries', '978-0307887894', 'Business', 'lean_startup.jpg'),
        ('Atomic Habits', 'James Clear', '978-0735211292', 'Business', 'atomic_habits.jpg'),
        ('Deep Work', 'Cal Newport', '978-1455586691', 'Business', 'deep_work.jpg'),
        # Dystopian
        ('1984', 'George Orwell', '978-0451524935', 'Dystopian', '1984.jpg'),
        ('Fahrenheit 451', 'Ray Bradbury', '978-1451673319', 'Dystopian', 'fahrenheit.jpg'),
        ('The Handmaids Tale', 'Margaret Atwood', '978-0385490818', 'Dystopian', 'handmaids_tale.jpg'),
        # Science Fiction
        ('Dune', 'Frank Herbert', '978-0441013593', 'Science Fiction', 'dune.jpg'),
        ('The Hitchhiker Guide to the Galaxy', 'Douglas Adams', '978-0345391803', 'Science Fiction', 'hitchhiker.jpg'),
        ('Ender Game', 'Orson Scott Card', '978-0812550702', 'Science Fiction', 'ender_game.jpg'),
    ]

    added = 0
    updated = 0
    for title, author, isbn, category, cover in books_data:
        existing = Book.query.filter_by(isbn=isbn).first()
        if not existing:
            book = Book(
                title=title, author=author, isbn=isbn,
                category=category, cover_image=cover
            )
            db.session.add(book)
            added += 1
        else:
            # Update cover even if book exists
            existing.cover_image = cover
            updated += 1

    db.session.commit()
    print(f'Books: {added} added, {updated} covers updated!')

    # ── Create default cover image ────────────────────────────────────
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