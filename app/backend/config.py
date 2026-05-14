# backend/config.py
import os
from datetime import timedelta
from dotenv import load_dotenv

def find_env_file():
    current_file = os.path.abspath(__file__)
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_file))), '.env'),
        os.path.join(os.path.dirname(os.path.dirname(current_file)), '.env'),
        os.path.join(os.path.dirname(current_file), '.env'),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            print(f"  .env ditemukan di: {path}")
            return path
    print("  .env tidak ditemukan! Menggunakan default.")
    return possible_paths[0]

env_path = find_env_file()
if os.path.exists(env_path):
    load_dotenv(env_path)

class Config:
    APP_NAME = os.getenv('APP_NAME', 'PublicBook')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    PORT = int(os.getenv('PORT', 5000))
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_NAME = os.getenv('DB_NAME', 'db_publicbook')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    raw_uri = os.getenv('DATABASE_URI')
    SQLALCHEMY_DATABASE_URI = os.path.expandvars(raw_uri) if raw_uri else f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET', 'default-jwt-secret')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=int(os.getenv('JWT_EXPIRE_MINUTES', 60)))
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend', 'assets', 'uploads')

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    TESTING = True

config_by_publicbook = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
