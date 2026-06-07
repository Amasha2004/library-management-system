from app import create_app, db
from app.models import User
from app import bcrypt

app = create_app()
with app.app_context():
    existing = User.query.filter_by(email='member@library.com').first()
    if not existing:
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
        print('Member created successfully!')
    else:
        print('Member already exists!')