from app import create_app, db
from app.models import User
from app import bcrypt

app = create_app()
with app.app_context():
    # Delete existing member if any
    existing = User.query.filter_by(role='member').all()
    for u in existing:
        db.session.delete(u)
    db.session.commit()
    print(f'Deleted {len(existing)} member(s)')

    # Create fresh member
    hashed = bcrypt.generate_password_hash('member123').decode('utf-8')
    member = User(
        name='Amasha',
        email='member@library.com',
        password=hashed,
        role='member',
        status='active',
        phone='12345678',
        address='Beijing, china'
    )
    db.session.add(member)
    db.session.commit()
    print('Fresh member created!')
    print('Email: member@library.com')
    print('Password: member123')