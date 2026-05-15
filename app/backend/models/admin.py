# backend/models/admin.py
from database.database import get_db
from sqlalchemy import text

class Admin:
    def __init__(self, data):
        self.id = data.get('id')
        self.nama_lengkap = data.get('nama_lengkap', 'Admin')
        self.email = data.get('email', '')
        self.password = data.get('password', '')
        self.role = data.get('role', 'admin_instansi')
        self.instansi_nama = data.get('instansi_nama', '')
        self.nomor_telepon = data.get('nomor_telepon', '')
        self.foto_profil = data.get('foto_profil')
        self.status = data.get('status', 'active')
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')

    @staticmethod
    def get_by_id(admin_id):
        db = get_db()
        row = db.execute(
            text("SELECT * FROM admins WHERE id = :id"),
            {'id': admin_id}
        ).mappings().first()
        return Admin(dict(row)) if row else None

    @staticmethod
    def get_all():
        db = get_db()
        rows = db.execute(
            text("SELECT * FROM admins ORDER BY id DESC")
        ).mappings().all()
        return [Admin(dict(row)) for row in rows]