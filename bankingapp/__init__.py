from flask import Flask
from flask_migrate import Migrate
from config import DevConfig
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv as ld

ld(".env")

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()
bcrypt = Bcrypt()
cors = CORS()

def create_app():
    bankingApp = Flask('bankingapp')
    bankingApp.config.from_object(DevConfig)
    db.init_app(app=bankingApp)
    migrate.init_app(app=bankingApp, db=db, render_as_batch=True, compare_type=True)
    bcrypt.init_app(app=bankingApp)
    jwt.init_app(app=bankingApp)
    cors.init_app(app=bankingApp)

    with bankingApp.app_context():
        from bankingapp import routes
        db.create_all()

    return bankingApp