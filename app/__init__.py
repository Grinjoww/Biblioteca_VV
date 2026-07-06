from flask import Flask
from app.extensions import db, migrate, login_manager
from app.controllers.auth import auth_bp
from app.controllers.temp_dashboards import bibliotecario_bp, estudiante_bp, gerente_bp
from dotenv import load_dotenv
import os

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(basedir, '.env'))


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clave-temporal-desarrollo')

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Debes iniciar sesión para acceder a esta página.'
    login_manager.login_message_category = 'warning'

    with app.app_context():
        from app import models  # noqa: F401

    app.register_blueprint(auth_bp)
    app.register_blueprint(bibliotecario_bp)
    app.register_blueprint(estudiante_bp)
    app.register_blueprint(gerente_bp)

    return app