# backend/models/booking.py
from database.database import get_db
from sqlalchemy import text

class Booking:
    def __init__(self, data):
        self.id = data.get('id')
        self.user_id = data.get('user_id')
        self.layanan_id = data.get('layanan_id')
        self.admin_id = data.get('admin_id')
        self.no_booking = data.get('no_booking', '')
        self.nama_pendaftar = data.get('nama_pendaftar', '')
        self.tanggal_booking = data.get('tanggal_booking')
        self.jam_booking = data.get('jam_booking')
        self.status = data.get('status', 'menunggu')
        self.nomor_antrian = data.get('nomor_antrian')
        self.catatan = data.get('catatan', '')
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')
        # Join data (akan diisi manual)
        self.nama_layanan = data.get('nama_layanan', '')
        self.instansi = data.get('instansi', '')

    @staticmethod
    def get_by_user_id(user_id, limit=None):
        db = get_db()
        sql = """
            SELECT b.*, l.nama_layanan, l.instansi 
            FROM bookings b
            LEFT JOIN layanan l ON b.layanan_id = l.id
            WHERE b.user_id = :user_id
            ORDER BY b.created_at DESC
        """
        if limit:
            sql += f" LIMIT {int(limit)}"
        rows = db.execute(text(sql), {'user_id': user_id}).mappings().all()
        return [Booking(dict(row)) for row in rows]

    @staticmethod
    def get_by_id(booking_id):
        db = get_db()
        row = db.execute(
            text("""
                SELECT b.*, l.nama_layanan, l.instansi 
                FROM bookings b
                LEFT JOIN layanan l ON b.layanan_id = l.id
                WHERE b.id = :id
            """),
            {'id': booking_id}
        ).mappings().first()
        return Booking(dict(row)) if row else None

    @staticmethod
    def count_by_user(user_id, status=None):
        db = get_db()
        sql = "SELECT COUNT(*) as total FROM bookings WHERE user_id = :user_id"
        params = {'user_id': user_id}
        if status:
            sql += " AND status = :status"
            params['status'] = status
        result = db.execute(text(sql), params).mappings().first()
        return result['total'] if result else 0

    @staticmethod
    def get_active_queue(user_id):
        db = get_db()
        row = db.execute(
            text("""
                SELECT b.*, l.nama_layanan 
                FROM bookings b
                LEFT JOIN layanan l ON b.layanan_id = l.id
                WHERE b.user_id = :user_id 
                AND b.status IN ('menunggu', 'dikonfirmasi', 'proses')
                ORDER BY b.created_at DESC
                LIMIT 1
            """),
            {'user_id': user_id}
        ).mappings().first()
        return Booking(dict(row)) if row else None