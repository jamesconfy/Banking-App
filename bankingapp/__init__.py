from flask import Flask
from config import DevConfig
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    bankingApp = Flask('bankingapp')
    bankingApp.config.from_object(DevConfig)
    db.init_app(bankingApp)
    jwt.init_app(bankingApp)

    with bankingApp.app_context():
        from bankingapp import routes
        db.create_all()

    return bankingApp