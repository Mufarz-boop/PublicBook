# backend/database/database.py
"""Database connection module untuk PublicBook
Menggunakan SQLAlchemy engine dengan raw SQL execution
Compatible dengan Laragon MySQL/MariaDB
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from flask import current_app
import os

# Engine akan diinisialisasi saat app startup
engine = None
Session = None

def init_db(app):
    """Inisialisasi database engine dengan app config"""
    global engine, Session

    database_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    if not database_uri:
        raise ValueError("SQLALCHEMY_DATABASE_URI tidak ditemukan di config")

    # Create engine dengan PyMySQL
    engine = create_engine(
        database_uri,
        pool_pre_ping=True,  # Cek koneksi sebelum dipakai
        pool_recycle=3600,   # Recycle koneksi setelah 1 jam
        echo=app.config.get('SQLALCHEMY_ECHO', False)
    )

    # Test koneksi
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
        print("✅ Database connected:", database_uri)

    # Buat session factory
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)

    return engine

def get_db():
    """Dapatkan database session
    Usage: session = get_db()
    """
    if Session is None:
        raise RuntimeError("Database belum diinisialisasi. Panggil init_db(app) dulu.")
    return Session()

def close_db(e=None):
    """Tutup database session setelah request"""
    if Session is not None:
        Session.remove()