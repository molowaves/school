import secrets

from flask import Flask, render_template, session
from werkzeug.security import generate_password_hash

from config import Config
from extensions import db
from models import Admin
from views import admin_bp, main_bp


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    @app.before_request
    def ensure_csrf_token():
        session.setdefault('_csrf_token', secrets.token_urlsafe(32))

    @app.context_processor
    def inject_globals():
        return {
            'school': app.config['SCHOOL'],
            'csrf_token': session.get('_csrf_token', ''),
        }

    @app.errorhandler(400)
    def bad_request(error):
        return render_template(
            'error.html',
            title='Request Error',
            message=getattr(error, 'description', 'The request could not be processed.'),
        ), 400

    @app.errorhandler(404)
    def not_found(error):
        return render_template(
            'error.html',
            title='Page Not Found',
            message='Sorry, that page could not be found.',
        ), 404

    with app.app_context():
        db.create_all()
        username = app.config.get('ADMIN_USERNAME')
        password = app.config.get('ADMIN_PASSWORD')
        if username and password and Admin.query.filter_by(username=username).first() is None:
            db.session.add(Admin(
                username=username,
                password_hash=generate_password_hash(password),
            ))
            db.session.commit()

    return app


app = create_app()


if __name__ == '__main__':
    app.run(debug=app.config.get('FLASK_DEBUG', False))
