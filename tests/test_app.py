import pytest
from app import create_app, db
from app.models import User, Book, Loan, Fine
from app.auth import create_admin
from datetime import date, timedelta


@pytest.fixture
def app():
    """Create test application with in-memory database."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        db.create_all()
        create_admin()
    yield app
    with app.app_context():
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def init_data(app):
    """Create test data: librarian, member, and books."""
    with app.app_context():
        from app import bcrypt
        # Create librarian
        librarian = User(
            name='Test Librarian',
            email='librarian@test.com',
            password=bcrypt.generate_password_hash('lib123').decode('utf-8'),
            role='librarian', status='active'
        )
        # Create active member
        member = User(
            name='Test Member',
            email='member@test.com',
            password=bcrypt.generate_password_hash('mem123').decode('utf-8'),
            role='member', status='active'
        )
        # Create pending member
        pending = User(
            name='Pending Member',
            email='pending@test.com',
            password=bcrypt.generate_password_hash('pen123').decode('utf-8'),
            role='member', status='pending'
        )
        # Create books
        book1 = Book(title='Test Book One', author='Author A',
                     isbn='111-1111111111', category='Fiction', status='available')
        book2 = Book(title='Test Book Two', author='Author B',
                     isbn='222-2222222222', category='Science', status='available')
        book3 = Book(title='Test Book Three', author='Author C',
                     isbn='333-3333333333', category='History', status='borrowed')

        db.session.add_all([librarian, member, pending, book1, book2, book3])
        db.session.commit()
    yield


# ── TC-01: Admin login with valid credentials ────────────────────────────────
def test_TC01_admin_login_valid(client):
    response = client.post('/login', data={
        'email': 'admin@library.com',
        'password': 'admin123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Dashboard' in response.data or b'Admin' in response.data


# ── TC-02: Login with invalid credentials ────────────────────────────────────
def test_TC02_login_invalid_credentials(client):
    response = client.post('/login', data={
        'email': 'admin@library.com',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid email or password' in response.data


# ── TC-03: Login with pending account ────────────────────────────────────────
def test_TC03_login_pending_account(client, init_data):
    response = client.post('/login', data={
        'email': 'pending@test.com',
        'password': 'pen123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'pending approval' in response.data


# ── TC-04: Member registration with valid data ───────────────────────────────
def test_TC04_member_registration_valid(client):
    response = client.post('/register', data={
        'name': 'New User',
        'email': 'newuser@test.com',
        'phone': '1234567890',
        'address': '123 Test Street',
        'password': 'pass1234',
        'confirm_password': 'pass1234'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Registration successful' in response.data


# ── TC-05: Registration with mismatched passwords ────────────────────────────
def test_TC05_registration_password_mismatch(client):
    response = client.post('/register', data={
        'name': 'New User',
        'email': 'another@test.com',
        'phone': '0987654321',
        'address': '456 Test Ave',
        'password': 'pass1234',
        'confirm_password': 'different'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Passwords do not match' in response.data


# ── TC-06: Registration with duplicate email ─────────────────────────────────
def test_TC06_registration_duplicate_email(client, init_data):
    response = client.post('/register', data={
        'name': 'Duplicate',
        'email': 'member@test.com',
        'phone': '111',
        'address': 'Somewhere',
        'password': 'pass1234',
        'confirm_password': 'pass1234'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'already registered' in response.data


# ── TC-07: Add book with valid data ──────────────────────────────────────────
def test_TC07_add_book_valid(client, init_data):
    # Login as admin
    client.post('/login', data={'email': 'admin@library.com', 'password': 'admin123'})
    response = client.post('/books/add', data={
        'title': 'New Test Book',
        'author': 'Test Author',
        'isbn': '999-9999999999',
        'category': 'Technology'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'added successfully' in response.data


# ── TC-08: Add book with duplicate ISBN ──────────────────────────────────────
def test_TC08_add_book_duplicate_isbn(client, init_data):
    client.post('/login', data={'email': 'admin@library.com', 'password': 'admin123'})
    response = client.post('/books/add', data={
        'title': 'Duplicate ISBN Book',
        'author': 'Author',
        'isbn': '111-1111111111',
        'category': 'Fiction'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'already exists' in response.data


# ── TC-09: Search books by title ─────────────────────────────────────────────
def test_TC09_search_books_by_title(client, init_data):
    client.post('/login', data={'email': 'admin@library.com', 'password': 'admin123'})
    response = client.get('/books?q=Test+Book+One')
    assert response.status_code == 200
    assert b'Test Book One' in response.data


# ── TC-10: Search books with no results ──────────────────────────────────────
def test_TC10_search_books_no_results(client, init_data):
    client.post('/login', data={'email': 'admin@library.com', 'password': 'admin123'})
    response = client.get('/books?q=XYZNOTEXIST')
    assert response.status_code == 200
    assert b'No books found' in response.data


# ── TC-11: Member borrows available book ─────────────────────────────────────
def test_TC11_borrow_available_book(client, app, init_data):
    client.post('/login', data={'email': 'member@test.com', 'password': 'mem123'})
    with app.app_context():
        book = Book.query.filter_by(isbn='222-2222222222').first()
        book_id = book.id
    response = client.post(f'/loans/borrow/{book_id}', follow_redirects=True)
    assert response.status_code == 200
    assert b'borrowed' in response.data.lower()


# ── TC-12: Member cannot borrow already borrowed book ────────────────────────
def test_TC12_borrow_unavailable_book(client, app, init_data):
    client.post('/login', data={'email': 'member@test.com', 'password': 'mem123'})
    with app.app_context():
        book = Book.query.filter_by(status='borrowed').first()
        book_id = book.id
    response = client.post(f'/loans/borrow/{book_id}', follow_redirects=True)
    assert response.status_code == 200
    assert b'not available' in response.data


# ── TC-13: Fine calculation — overdue book ───────────────────────────────────
def test_TC13_fine_calculation_overdue(app, init_data):
    with app.app_context():
        member = User.query.filter_by(email='member@test.com').first()
        book = Book.query.filter_by(isbn='111-1111111111').first()
        # Create a loan that is 5 days overdue
        loan = Loan(
            user_id=member.id,
            book_id=book.id,
            borrow_date=date.today() - timedelta(days=19),
            due_date=date.today() - timedelta(days=5),
            return_date=date.today(),
            status='returned'
        )
        db.session.add(loan)
        db.session.commit()
        fine = loan.calculate_fine()
        assert fine == 2.50  # 5 days * 0.50


# ── TC-14: Fine calculation — on-time return ─────────────────────────────────
def test_TC14_fine_calculation_ontime(app, init_data):
    with app.app_context():
        member = User.query.filter_by(email='member@test.com').first()
        book = Book.query.filter_by(isbn='111-1111111111').first()
        loan = Loan(
            user_id=member.id,
            book_id=book.id,
            borrow_date=date.today() - timedelta(days=5),
            due_date=date.today() + timedelta(days=9),
            return_date=date.today(),
            status='returned'
        )
        db.session.add(loan)
        db.session.commit()
        fine = loan.calculate_fine()
        assert fine == 0.0


# ── TC-15: Admin approves pending member ─────────────────────────────────────
def test_TC15_approve_member(client, app, init_data):
    client.post('/login', data={'email': 'admin@library.com', 'password': 'admin123'})
    with app.app_context():
        pending = User.query.filter_by(email='pending@test.com').first()
        user_id = pending.id
    response = client.post(f'/admin/members/approve/{user_id}', follow_redirects=True)
    assert response.status_code == 200
    assert b'approved' in response.data


# ── TC-16: Logout ─────────────────────────────────────────────────────────────
def test_TC16_logout(client):
    client.post('/login', data={'email': 'admin@library.com', 'password': 'admin123'})
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'logged out' in response.data