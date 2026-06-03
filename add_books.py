from app import create_app, db
from app.models import Book

app = create_app()
with app.app_context():
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

        # Science & Technology
        Book(title='A Brief History of Time', author='Stephen Hawking', isbn='978-0553380163', category='Science'),
        Book(title='The Selfish Gene', author='Richard Dawkins', isbn='978-0198788607', category='Science'),
        Book(title='Cosmos', author='Carl Sagan', isbn='978-0345539434', category='Science'),
        Book(title='Clean Code', author='Robert C. Martin', isbn='978-0132350884', category='Technology'),
        Book(title='The Pragmatic Programmer', author='David Thomas', isbn='978-0201616224', category='Technology'),
        Book(title='Design Patterns', author='Gang of Four', isbn='978-0201633610', category='Technology'),
        Book(title='Introduction to Algorithms', author='Thomas H. Cormen', isbn='978-0262033848', category='Technology'),
        Book(title='The Art of Computer Programming', author='Donald E. Knuth', isbn='978-0201896831', category='Technology'),
        Book(title='Python Crash Course', author='Eric Matthes', isbn='978-1593279288', category='Technology'),
        Book(title='Artificial Intelligence: A Modern Approach', author='Stuart Russell', isbn='978-0134610993', category='Technology'),

        # History & Philosophy
        Book(title='Sapiens', author='Yuval Noah Harari', isbn='978-0062316097', category='History'),
        Book(title='Homo Deus', author='Yuval Noah Harari', isbn='978-0062464316', category='History'),
        Book(title='The Art of War', author='Sun Tzu', isbn='978-1599869773', category='Philosophy'),
        Book(title='Meditations', author='Marcus Aurelius', isbn='978-0140449334', category='Philosophy'),
        Book(title='Thus Spoke Zarathustra', author='Friedrich Nietzsche', isbn='978-0140441185', category='Philosophy'),
        Book(title='The Republic', author='Plato', isbn='978-0140455113', category='Philosophy'),
        Book(title='Guns Germs and Steel', author='Jared Diamond', isbn='978-0393317558', category='History'),
        Book(title='The Silk Roads', author='Peter Frankopan', isbn='978-1101912379', category='History'),

        # Business & Self Help
        Book(title='Think and Grow Rich', author='Napoleon Hill', isbn='978-1585424337', category='Business'),
        Book(title='The 7 Habits of Highly Effective People', author='Stephen Covey', isbn='978-1982137274', category='Business'),
        Book(title='Zero to One', author='Peter Thiel', isbn='978-0804139021', category='Business'),
        Book(title='The Lean Startup', author='Eric Ries', isbn='978-0307887894', category='Business'),
        Book(title='Atomic Habits', author='James Clear', isbn='978-0735211292', category='Business'),
        Book(title='Deep Work', author='Cal Newport', isbn='978-1455586691', category='Business'),

        # Dystopian & Sci-Fi
        Book(title='1984', author='George Orwell', isbn='978-0451524935', category='Dystopian'),
        Book(title='Fahrenheit 451', author='Ray Bradbury', isbn='978-1451673319', category='Dystopian'),
        Book(title='The Handmaids Tale', author='Margaret Atwood', isbn='978-0385490818', category='Dystopian'),
        Book(title='Dune', author='Frank Herbert', isbn='978-0441013593', category='Science Fiction'),
        Book(title='The Hitchhiker Guide to the Galaxy', author='Douglas Adams', isbn='978-0345391803', category='Science Fiction'),
        Book(title='Ender Game', author='Orson Scott Card', isbn='978-0812550702', category='Science Fiction'),
    ]

    added = 0
    skipped = 0
    for b in books:
        existing = Book.query.filter_by(isbn=b.isbn).first()
        if not existing:
            db.session.add(b)
            added += 1
        else:
            skipped += 1

    db.session.commit()
    print(f'Done! Added: {added} books, Skipped: {skipped} duplicates')
    print(f'Total books in database: {Book.query.count()}')