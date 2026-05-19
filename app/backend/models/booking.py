# backend/models/booking.py
from database.database import get_db
from sqlalchemy import text
import random
import string

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
    
    # === METHOD UNTUK ADMIN ===
    
    @staticmethod
    def get_all(limit=None):
        db = get_db()
        sql = """
            SELECT b.*, 
                   l.nama_layanan, l.instansi,
                   u.nama_lengkap as user_nama, u.email as user_email
            FROM bookings b
            LEFT JOIN layanan l ON b.layanan_id = l.id
            LEFT JOIN users u ON b.user_id = u.id
            ORDER BY b.created_at DESC
        """
        if limit:
            sql += f" LIMIT {int(limit)}"
        rows = db.execute(text(sql)).mappings().all()
        return [Booking(dict(row)) for row in rows]

    @staticmethod
    def count_all():
        db = get_db()
        result = db.execute(text("SELECT COUNT(*) as total FROM bookings")).mappings().first()
        return result['total'] if result else 0

    @staticmethod
    def count_today():
        db = get_db()
        result = db.execute(
            text("SELECT COUNT(*) as total FROM bookings WHERE DATE(tanggal_booking) = CURDATE()")
        ).mappings().first()
        return result['total'] if result else 0

    @staticmethod
    def count_this_month():
        db = get_db()
        result = db.execute(
            text("SELECT COUNT(*) as total FROM bookings WHERE MONTH(tanggal_booking) = MONTH(CURDATE()) AND YEAR(tanggal_booking) = YEAR(CURDATE())")
        ).mappings().first()
        return result['total'] if result else 0
    
    @staticmethod
    def generate_booking_number():
        """Generate unique booking number: PB-XXXXXX"""
        db = get_db()
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            no_booking = f"PB-{code}"
            
            result = db.execute(
                text("SELECT id FROM bookings WHERE no_booking = :no"),
                {'no': no_booking}
            ).mappings().first()
            
            if not result:
                return no_booking

    # ═══════════════════════════════════════════════════════════════════
    # BARU: Generate Nomor Antrean Otomatis
    # ═══════════════════════════════════════════════════════════════════
    @staticmethod
    def generate_nomor_antrian(layanan_id, tanggal_booking):
        """Generate nomor antrean unik per layanan & tanggal"""
        db = get_db()
        
        # Cari nomor antrean terakhir untuk layanan & tanggal ini
        result = db.execute(
            text("""
                SELECT MAX(nomor_antrian) as last_queue
                FROM bookings 
                WHERE layanan_id = :layanan_id 
                AND tanggal_booking = :tanggal
                AND nomor_antrian IS NOT NULL
            """),
            {'layanan_id': layanan_id, 'tanggal': tanggal_booking}
        ).mappings().first()
        
        last_queue = result['last_queue'] if result and result['last_queue'] else 0
        new_queue = last_queue + 1
        
        return new_queue

    # ═══════════════════════════════════════════════════════════════════
    # BARU: Get posisi antrean (berapa orang di depan)
    # ═══════════════════════════════════════════════════════════════════
    @staticmethod
    def get_queue_position(booking_id):
        """Dapatkan posisi antrean user"""
        db = get_db()
        
        booking = Booking.get_by_id(booking_id)
        if not booking or not booking.nomor_antrian:
            return None
        
        # Hitung berapa orang dengan nomor antrean lebih kecil & status aktif
        result = db.execute(
            text("""
                SELECT COUNT(*) as ahead
                FROM bookings 
                WHERE layanan_id = :layanan_id 
                AND tanggal_booking = :tanggal
                AND nomor_antrian < :nomor
                AND status IN ('menunggu', 'dikonfirmasi', 'proses')
            """),
            {
                'layanan_id': booking.layanan_id,
                'tanggal': booking.tanggal_booking,
                'nomor': booking.nomor_antrian
            }
        ).mappings().first()
        
        return {
            'nomor_antrian': booking.nomor_antrian,
            'orang_di_depan': result['ahead'] if result else 0,
            'status': booking.status
        }

    @staticmethod
    def create(user_id, layanan_id, nama_pendaftar, tanggal_booking, jam_booking, catatan=None):
        db = get_db()
        
        # ═══════════════════════════════════════════════════════════════
        # CEK DUPLIKAT: User sudah booking layanan + tanggal + jam yang sama
        # ═══════════════════════════════════════════════════════════════
        existing = db.execute(
            text("""
                SELECT id FROM bookings 
                WHERE user_id = :user_id 
                AND layanan_id = :layanan_id 
                AND tanggal_booking = :tanggal 
                AND jam_booking = :jam
                AND status != 'dibatalkan'
            """),
            {
                'user_id': user_id,
                'layanan_id': layanan_id,
                'tanggal': tanggal_booking,
                'jam': jam_booking
            }
        ).mappings().first()
        
        if existing:
            raise ValueError("Anda sudah membooking layanan ini pada tanggal dan jam yang sama!")
        
        # ═══════════════════════════════════════════════════════════════
        # CEK KUOTA: Berapa slot tersedia per jam
        # ═══════════════════════════════════════════════════════════════
        # Ambil kuota per jam dari layanan (default 5 kalau nggak ada)
        kuota_result = db.execute(
            text("SELECT kuota_per_jam FROM layanan WHERE id = :id"),
            {'id': layanan_id}
        ).mappings().first()
        
        kuota = kuota_result['kuota_per_jam'] if kuota_result and kuota_result['kuota_per_jam'] else 5
        
        # Hitung berapa booking aktif di jam ini
        booked_count = db.execute(
            text("""
                SELECT COUNT(*) as total 
                FROM bookings 
                WHERE layanan_id = :layanan_id 
                AND tanggal_booking = :tanggal 
                AND jam_booking = :jam
                AND status IN ('menunggu', 'dikonfirmasi', 'proses')
            """),
            {
                'layanan_id': layanan_id,
                'tanggal': tanggal_booking,
                'jam': jam_booking
            }
        ).mappings().first()
        
        if booked_count and booked_count['total'] >= kuota:
            raise ValueError(f"Kuota untuk jam {jam_booking} sudah penuh! Silakan pilih jam lain.")
        
        # Lanjutkan create booking (kode yang udah ada)
        no_booking = Booking.generate_booking_number()
        
        service = db.execute(
            text("SELECT admin_id FROM layanan WHERE id = :id"),
            {'id': layanan_id}
        ).mappings().first()
        admin_id = service['admin_id'] if service else None
        
        nomor_antrian = Booking.generate_nomor_antrian(layanan_id, tanggal_booking)
        
        sql = """
            INSERT INTO bookings 
            (user_id, layanan_id, admin_id, no_booking, nama_pendaftar, 
            tanggal_booking, jam_booking, status, nomor_antrian, catatan, created_at, updated_at)
            VALUES 
            (:user_id, :layanan_id, :admin_id, :no_booking, :nama_pendaftar,
            :tanggal_booking, :jam_booking, 'menunggu', :nomor_antrian, :catatan, NOW(), NOW())
        """
        
        result = db.execute(text(sql), {
            'user_id': user_id,
            'layanan_id': layanan_id,
            'admin_id': admin_id,
            'no_booking': no_booking,
            'nama_pendaftar': nama_pendaftar,
            'tanggal_booking': tanggal_booking,
            'jam_booking': jam_booking,
            'nomor_antrian': nomor_antrian,
            'catatan': catatan or ''
        })
        
        db.commit()
        booking_id = result.lastrowid
        
        return Booking.get_by_id(booking_id)

    @staticmethod
    def update_status(booking_id, status_baru, admin_id=None, keterangan=None):
        """Update status booking dan catat riwayat"""
        db = get_db()
        
        # Get booking current status
        booking = Booking.get_by_id(booking_id)
        if not booking:
            return None
            
        status_sebelum = booking.status
        
        # Update booking status
        db.execute(
            text("""
                UPDATE bookings 
                SET status = :status, updated_at = NOW() 
                WHERE id = :id
            """),
            {'status': status_baru, 'id': booking_id}
        )
        
        # Insert riwayat status
        db.execute(
            text("""
                INSERT INTO riwayat_status 
                (booking_id, status_sebelum, status_baru, admin_id, keterangan, waktu_perubahan)
                VALUES 
                (:booking_id, :status_sebelum, :status_baru, :admin_id, :keterangan, NOW())
            """),
            {
                'booking_id': booking_id,
                'status_sebelum': status_sebelum,
                'status_baru': status_baru,
                'admin_id': admin_id,
                'keterangan': keterangan or f'Status diubah via QR Scan dari {status_sebelum} ke {status_baru}'
            }
        )
        
        db.commit()
        return Booking.get_by_id(booking_id)

    @staticmethod
    def get_by_booking_number(no_booking):
        """Get booking by booking number"""
        db = get_db()
        row = db.execute(
            text("""
                SELECT b.*, l.nama_layanan, l.instansi 
                FROM bookings b
                LEFT JOIN layanan l ON b.layanan_id = l.id
                WHERE b.no_booking = :no_booking
            """),
            {'no_booking': no_booking}
        ).mappings().first()
        return Booking(dict(row)) if row else None