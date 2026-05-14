# backend/config.py
# Konfigurasi aplikasi PublicBook — sesuai .env (MySQL / phpMyAdmin / Laragon)

import os
from datetime import timedelta
from dotenv import load_dotenv

# Cari .env di beberapa lokasi yang mungkin
# Prioritas:
#   1. Folder parent dari app/ (root project)
#   2. Folder saat ini (app/backend/)
#   3. Folder app/

def find_env_file():
    """Cari .env di beberapa lokasi"""
    current_file = os.path.abspath(__file__)

    # Lokasi yang mungkin
    possible_paths = [
        # 1. Root folder (parent dari app/)
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_file))), '.env'),
        # 2. Folder app/ (sibling dari backend/)
        os.path.join(os.path.dirname(os.path.dirname(current_file)), '.env'),
        # 3. Folder backend/
        os.path.join(os.path.dirname(current_file), '.env'),
    ]

    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ .env ditemukan di: {path}")
            return path

    # Kalau tidak ditemukan, return yang pertama sebagai default
    print(f"⚠️  .env tidak ditemukan di lokasi manapun!")
    print(f"   Dicari di:")
    for p in possible_paths:
        print(f"      - {p}")
    return possible_paths[0]

env_path = find_env_file()
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    print("⚠️  Menggunakan default config (tanpa .env)")


class Config:
    """Konfigurasi dasar — baca dari .env"""

    # App
    APP_NAME = os.getenv('APP_NAME', 'PublicBook')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    PORT = int(os.getenv('PORT', 5000))

    # Database (MySQL/MariaDB dari .env — Laragon)
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_NAME = os.getenv('DB_NAME', 'db_publicbook')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')

    # Full URI untuk SQLAlchemy (gunakan PyMySQL driver)
    raw_uri = os.getenv('DATABASE_URI')
    if raw_uri:
        SQLALCHEMY_DATABASE_URI = os.path.expandvars(raw_uri)
    else:
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET', 'default-jwt-secret')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv('JWT_EXPIRE_MINUTES', 60))
    )

    # Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend', 'assets', 'uploads')

    # Redis (Queue / Realtime)
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD') or None

    # Email
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'


class DevelopmentConfig(Config):
    """Development mode — DEBUG on, log SQL."""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Production — DEBUG off, wajib secret key kuat."""
    DEBUG = False


class TestingConfig(Config):
    """Testing — SQLite in-memory."""
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    TESTING = True


# Mapping untuk app factory
config_by_publicbook = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}