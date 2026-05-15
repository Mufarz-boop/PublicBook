# backend/models/services.py
from database.database import get_db
from sqlalchemy import text

class Service:
    def __init__(self, data):
        self.id = data.get('id')
        self.admin_id = data.get('admin_id')
        self.nama_layanan = data.get('nama_layanan', '')
        self.instansi = data.get('instansi', '')
        self.deskripsi = data.get('deskripsi', '')
        self.jam_operasional = data.get('jam_operasional', '')
        self.status = data.get('status', 'active')
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')

    @staticmethod
    def get_all_active():
        db = get_db()
        rows = db.execute(
            text("SELECT * FROM layanan WHERE status = 'active' ORDER BY nama_layanan"),
        ).mappings().all()
        return [Service(dict(row)) for row in rows]

    @staticmethod
    def get_by_id(service_id):
        db = get_db()
        row = db.execute(
            text("SELECT * FROM layanan WHERE id = :id"),
            {'id': service_id}
        ).mappings().first()
        return Service(dict(row)) if row else None

    @staticmethod
    def search(keyword):
        db = get_db()
        rows = db.execute(
            text("""
                SELECT * FROM layanan 
                WHERE status = 'active' 
                AND (nama_layanan LIKE :kw OR instansi LIKE :kw OR deskripsi LIKE :kw)
                ORDER BY nama_layanan
            """),
            {'kw': f'%{keyword}%'}
        ).mappings().all()
        return [Service(dict(row)) for row in rows]