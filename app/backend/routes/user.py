# backend/routes/user.py
from flask import Blueprint, render_template, session, redirect, url_for, flash, jsonify, request
from datetime import datetime
from models.user import User
from models.booking import Booking
from models.services import Service

bp = Blueprint('user_routes', __name__, url_prefix='/user')

def user_required(f):
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

@bp.route('/booking/create', methods=['POST'])
@user_required
def booking_create():
    """API to create booking dengan nomor antrean otomatis"""
    user_id = session.get('user_id')
    
    try:
        layanan_id = request.form.get('layanan_id', type=int)
        nama_pendaftar = request.form.get('nama_pendaftar', '').strip()
        tanggal_booking = request.form.get('tanggal_booking')
        jam_booking = request.form.get('jam_booking')
        catatan = request.form.get('catatan', '').strip()
        
        # Validation
        if not all([layanan_id, nama_pendaftar, tanggal_booking, jam_booking]):
            return jsonify({'success': False, 'message': 'Semua field wajib diisi'}), 400
        
        # Validate service exists
        service = Service.get_by_id(layanan_id)
        if not service:
            return jsonify({'success': False, 'message': 'Layanan tidak ditemukan'}), 404
        
        # Create booking (nomor antrean otomatis dari model)
        booking = Booking.create(
            user_id=user_id,
            layanan_id=layanan_id,
            nama_pendaftar=nama_pendaftar,
            tanggal_booking=tanggal_booking,
            jam_booking=jam_booking,
            catatan=catatan
        )
        
        # Get queue info
        queue_info = Booking.get_queue_position(booking.id)
        
        return jsonify({
            'success': True,
            'message': f'Booking berhasil! Nomor antrean Anda: #{booking.nomor_antrian}',
            'data': {
                'no_booking': booking.no_booking,
                'nomor_antrian': booking.nomor_antrian,
                'orang_di_depan': queue_info['orang_di_depan'] if queue_info else 0,
                'redirect_url': url_for('user_routes.booking')
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Terjadi kesalahan: {str(e)}'}), 500
    
@bp.route('/layanan')
@user_required
def layanan():
    user_id = session.get('user_id')
    user = User.get_by_id(user_id)
    
    # Ambil semua layanan aktif
    services = Service.get_all_active()
    
    return render_template('user/layanan.html', user=user, services=services)

@bp.route('/profil')
@user_required
def profil():
    user_id = session.get('user_id')
    user = User.get_by_id(user_id)
    active_queue = Booking.get_active_queue(user_id)
    
    # ═══════════════════════════════════════════════════════════════
    # BARU: Ambil info posisi antrean
    # ═══════════════════════════════════════════════════════════════
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
                         queue_info=queue_info,  # ← BARU
                         stats=stats)