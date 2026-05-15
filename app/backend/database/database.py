# app/backend/database/database.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session

engine = None
Session = None

def init_db(app):
    global engine, Session
    database_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    if not database_uri:
        raise ValueError("SQLALCHEMY_DATABASE_URI tidak ditemukan di config")
    engine = create_engine(database_uri, pool_pre_ping=True, pool_recycle=3600, echo=app.config.get('SQLALCHEMY_ECHO', False))
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
        print("  Database connected:", database_uri)
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
    return engine

def get_db():
    if Session is None:
        raise RuntimeError("Database belum diinisialisasi. Panggil init_db(app) dulu.")
    return Session()

def close_db(e=None):
    if Session is not None:
        Session.remove()