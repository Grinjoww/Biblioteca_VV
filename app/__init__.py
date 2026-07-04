from flask import Flask
from app.extensions import db, migrate, login_manager
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

    return app