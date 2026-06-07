from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    from app.auth import auth
    from app.books import books
    from app.members import members
    from app.loans import loans
    from app.reports import reports

    app.register_blueprint(auth)
    app.register_blueprint(books)
    app.register_blueprint(members)
    app.register_blueprint(loans)
    app.register_blueprint(reports)

    with app.app_context():
        db.create_all()

    from flask import render_template

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template('500.html'), 500

    return app