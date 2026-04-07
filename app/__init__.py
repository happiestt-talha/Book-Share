from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

COVER_COLORS = [
    '#1a6b45', '#2d6a8c', '#7b3fa0', '#c0392b',
    '#e67e22', '#16a085', '#2980b9', '#8e44ad',
    '#d35400', '#27ae60', '#2c3e50', '#c0392b',
]


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    # Register custom template filter
    @app.template_global()
    def loop_color(index):
        return COVER_COLORS[index % len(COVER_COLORS)]

    from app.auth import auth_bp
    from app.books import books_bp
    from app.borrow import borrow_bp
    from app.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(borrow_bp)
    app.register_blueprint(admin_bp)

    # Register error handlers
    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template('errors/500.html'), 500

    return app


@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))