# backend/database/database.py
# Setup koneksi database MySQL via SQLAlchemy
# CATATAN: Table sudah dibuat via SQL dump phpMyAdmin — jangan recreate

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, inspect

# Instance global SQLAlchemy
db = SQLAlchemy()


def init_db(app):
    """
    Inisialisasi database dengan Flask app.
    Table sudah ada di MySQL — hanya test koneksi & verify struktur.

    Args:
        app: Flask application instance

    Returns:
        db: SQLAlchemy instance yang sudah di-bind ke app
    """
    db.init_app(app)

    with app.app_context():
        try:
            # Test koneksi dengan query sederhana
            db.session.execute(text('SELECT 1'))
            print("✅ Database connected successfully!")

            # Cek table yang tersedia di database
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 Tables found: {', '.join(tables) if tables else 'None'}")

            # Verifikasi table wajib ada
            required_tables = {
                'users', 'admins', 'layanan', 'bookings',
                'riwayat_status', 'security_logs', 'statistik_harian'
            }
            missing = required_tables - set(tables)
            if missing:
                print(f"⚠️  Missing tables: {', '.join(missing)}")
                print("   Run SQL dump di phpMyAdmin untuk membuat table.")
            else:
                print("✅ All required tables present!")

        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise

    return db


def get_db():
    """
    Helper untuk mendapatkan session database.
    Gunakan ini di routes untuk query.

    Returns:
        SQLAlchemy session

    Example:
        from database.database import get_db
        db = get_db()
        users = db.session.query(User).all()
    """
    return db.session


def close_db(e=None):
    """
    Tutup database session setelah request selesai.
    Dipasang sebagai teardown handler di app factory.
    """
    db.session.remove()


def reset_db():
    """
    ⚠️ HATI-HATI: Drop semua table dan recreate.
    Gunakan hanya untuk development/testing.
    """
    with db.engine.connect() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        conn.commit()

        # Drop semua table
        db.drop_all()

        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        conn.commit()

    # Recreate (hanya kalau pakai model SQLAlchemy dengan create_all)
    # db.create_all()
    print("🔄 Database reset complete")
    print("   ⚠️  Table kosong — import ulang SQL dump di phpMyAdmin")