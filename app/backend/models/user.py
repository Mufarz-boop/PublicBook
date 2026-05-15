# backend/models/user.py
from database.database import get_db
from sqlalchemy import text

class User:
    def __init__(self, data):
        self.id = data.get('id')
        self.nama_lengkap = data.get('nama_lengkap', 'User')
        self.email = data.get('email', '')
        self.nomor_telepon = data.get('nomor_telepon', '')
        self.alamat = data.get('alamat', '')
        self.foto_profil = data.get('foto_profil')
        self.status = data.get('status', 'active')
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')

    @staticmethod
    def get_by_id(user_id):
        db = get_db()
        row = db.execute(
            text("SELECT * FROM users WHERE id = :id"),
            {'id': user_id}
        ).mappings().first()
        return User(dict(row)) if row else None

    @staticmethod
    def get_by_email(email):
        db = get_db()
        row = db.execute(
            text("SELECT * FROM users WHERE email = :email"),
            {'email': email}
        ).mappings().first()
        return User(dict(row)) if row else None

    @staticmethod
    def get_all():
        db = get_db()
        rows = db.execute(text("SELECT * FROM users ORDER BY id DESC")).mappings().all()
        return [User(dict(row)) for row in rows]
    
    @staticmethod
    def count_all():
        db = get_db()
        result = db.execute(text("SELECT COUNT(*) as total FROM users")).mappings().first()
        return result['total'] if result else 0