from os import environ as env
from datetime import timedelta
from dotenv import load_dotenv as ld
import pymysql

ld(".env")

ADDRESS = env.get('DB_ADDRESS')
PASSWORD = env.get('DB_PASSWORD')
USER = env.get('DB_USER')
NAME = env.get('DB_NAME')
PORT = env.get('PORT')

class DevConfig(object):
    SECRET_KEY = env.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = "sqlite:///site.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = env.get('SQLALCHEMY_TRACK_MODIFICATIONS')
    JWT_COOKIE_SECURE = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=10)
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_COOKIE_CSRF_PROTECT = False

class ProdConfig(DevConfig):
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{USER}:{PASSWORD}@{ADDRESS}/{NAME}'