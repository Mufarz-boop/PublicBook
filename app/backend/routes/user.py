# backend/routes/user.py
from flask import Blueprint, render_template, session, redirect, url_for, flash
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
    
    # Ambil antrean aktif
    active_queue = Booking.get_active_queue(user_id)
    
    return render_template('user/profil.html', user=user, queue=active_queue)