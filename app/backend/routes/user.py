# backend/routes/user.py
from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from datetime import datetime
from models.user import User
from models.booking import Booking
from models.services import Service
from database.database import get_db

bp = Blueprint('user_routes', __name__, url_prefix='/user')


def user_required(f):
    """Decorator untuk cek apakah user sudah login dan bukan admin"""
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            flash('Silakan login terlebih dahulu', 'warning')
            return redirect(url_for('auth_routes.login_page'))
        if session.get('is_admin'):
            flash('Halaman ini khusus pengguna', 'danger')
            return redirect(url_for('admin_routes.dashboard'))
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated


# ═══════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════

@bp.route('/dashboard')
@user_required
def dashboard():
    user_id = session.get('user_id')
    user = User.get_by_id(user_id)
    
    # Ambil 5 booking terakhir
    bookings = Booking.get_by_user_id(user_id, limit=5)
    
    # Statistik
    stats = {
        'total_booking': Booking.count_by_user(user_id),
        'menunggu': Booking.count_by_user(user_id, status='menunggu'),
        'dikonfirmasi': Booking.count_by_user(user_id, status='dikonfirmasi'),
        'selesai': Booking.count_by_user(user_id, status='selesai')
    }
    
    return render_template('user/dashboard.html', user=user, bookings=bookings, stats=stats)


# ═══════════════════════════════════════════════════════════════
# BOOKING LIST
# ═══════════════════════════════════════════════════════════════

@bp.route('/booking')
@user_required
def booking():
    user_id = session.get('user_id')
    user = User.get_by_id(user_id)
    
    # Ambil semua booking user
    bookings = Booking.get_by_user_id(user_id)
    
    # Ambil booking aktif (untuk QR code)
    active_booking = Booking.get_active_queue(user_id)
    
    return render_template('user/booking.html', user=user, bookings=bookings, active_booking=active_booking)


# ═══════════════════════════════════════════════════════════════
# BOOKING DETAIL
# ═══════════════════════════════════════════════════════════════

@bp.route('/booking/detail/<int:id>')
@user_required
def booking_detail(id):
    user_id = session.get('user_id')
    user = User.get_by_id(user_id)
    
    booking = Booking.get_by_id(id)
    
    # Cek kepemilikan
    if not booking or booking.user_id != user_id:
        flash('Booking tidak ditemukan', 'danger')
        return redirect(url_for('user_routes.booking'))
    
    return render_template('user/booking-detail.html', user=user, booking=booking)


# ═══════════════════════════════════════════════════════════════
# BOOKING NEW (Form Page)
# ═══════════════════════════════════════════════════════════════

@bp.route('/booking/new', methods=['GET'])
@user_required
def booking_new():
    """Render booking form page"""
    user_id = session.get('user_id')
    user = User.get_by_id(user_id)
    
    layanan_id = request.args.get('layanan_id', type=int)
    service = Service.get_by_id(layanan_id) if layanan_id else None
    
    if not service:
        flash('Layanan tidak ditemukan', 'danger')
        return redirect(url_for('user_routes.layanan'))
    
    # Get tomorrow's date for min date
    tomorrow = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('user/booking-form.html', 
                         user=user, 
                         service=service,
                         min_date=tomorrow)


# ═══════════════════════════════════════════════════════════════
# BOOKING CREATE (Form Submit → Redirect)
# ═══════════════════════════════════════════════════════════════

@bp.route('/booking/create', methods=['POST'])
@user_required
def booking_create():
    """Create booking dengan nomor antrean otomatis lalu redirect ke halaman booking"""
    user_id = session.get('user_id')
    
    try:
        layanan_id = request.form.get('layanan_id', type=int)
        nama_pendaftar = request.form.get('nama_pendaftar', '').strip()
        tanggal_booking = request.form.get('tanggal_booking')
        jam_booking = request.form.get('jam_booking')
        catatan = request.form.get('catatan', '').strip()
        
        # Validation
        if not all([layanan_id, nama_pendaftar, tanggal_booking, jam_booking]):
            flash('Semua field wajib diisi!', 'danger')
            return redirect(url_for('user_routes.booking_new', layanan_id=layanan_id))
        
        # Validate service exists
        service = Service.get_by_id(layanan_id)
        if not service:
            flash('Layanan tidak ditemukan', 'danger')
            return redirect(url_for('user_routes.layanan'))
        
        # Create booking (nomor antrean otomatis dari model)
        booking = Booking.create(
            user_id=user_id,
            layanan_id=layanan_id,
            nama_pendaftar=nama_pendaftar,
            tanggal_booking=tanggal_booking,
            jam_booking=jam_booking,
            catatan=catatan
        )
        
        # Flash pesan sukses
        flash(f'Booking berhasil! Nomor antrean Anda: #{booking.nomor_antrian}', 'success')
        
        # Redirect ke halaman list booking
        return redirect(url_for('user_routes.booking'))
        
    except Exception as e:
        flash(f'Terjadi kesalahan: {str(e)}', 'danger')
        return redirect(url_for('user_routes.layanan'))

@bp.route('/booking/cancel/<int:id>', methods=['POST'])
@user_required
def booking_cancel(id):
    """Cancel booking yang masih menunggu"""
    user_id = session.get('user_id')
    
    booking = Booking.get_by_id(id)
    
    if not booking or booking.user_id != user_id:
        flash('Booking tidak ditemukan', 'danger')
        return redirect(url_for('user_routes.booking'))
    
    if booking.status != 'menunggu':
        flash(f'Booking dengan status "{booking.status}" tidak bisa dibatalkan', 'warning')
        return redirect(url_for('user_routes.booking'))
    
    # ═══════════════════════════════════════════════════════════════
    # Pake method update_status yang udah ada di model!
    # ═══════════════════════════════════════════════════════════════
    try:
        Booking.update_status(
            booking_id=id,
            status_baru='dibatalkan',
            admin_id=None,
            keterangan='Booking dibatalkan oleh user'
        )
        
        flash('Booking berhasil dibatalkan', 'success')
        
    except Exception as e:
        flash(f'Gagal membatalkan booking: {str(e)}', 'danger')
    
    return redirect(url_for('user_routes.booking'))

# ═══════════════════════════════════════════════════════════════
# LAYANAN
# ═══════════════════════════════════════════════════════════════

@bp.route('/layanan')
@user_required
def layanan():
    user_id = session.get('user_id')
    user = User.get_by_id(user_id)
    
    # Ambil semua layanan aktif
    services = Service.get_all_active()
    
    return render_template('user/layanan.html', user=user, services=services)


# ═══════════════════════════════════════════════════════════════
# PROFIL
# ═══════════════════════════════════════════════════════════════

@bp.route('/profil')
@user_required
def profil():
    user_id = session.get('user_id')
    user = User.get_by_id(user_id)
    active_queue = Booking.get_active_queue(user_id)
    
    # Ambil info posisi antrean
    queue_info = None
    if active_queue and active_queue.nomor_antrian:
        queue_info = Booking.get_queue_position(active_queue.id)
    
    stats = {
        'total_booking': Booking.count_by_user(user_id),
        'menunggu': Booking.count_by_user(user_id, status='menunggu'),
        'selesai': Booking.count_by_user(user_id, status='selesai')
    }
    
    return render_template('user/profil.html', 
                         user=user, 
                         queue=active_queue, 
                         queue_info=queue_info,
                         stats=stats)