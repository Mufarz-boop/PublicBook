# backend/routes/admin.py
from flask import Blueprint, render_template, session, redirect, url_for, flash
from models.user import User
from models.booking import Booking
from models.services import Service
from models.admin import Admin

bp = Blueprint('admin_routes', __name__, url_prefix='/admin')

def admin_required(f):
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            flash('Silakan login terlebih dahulu', 'warning')
            return redirect(url_for('auth_routes.login_page'))
        if not session.get('is_admin'):
            flash('Akses ditolak', 'danger')
            return redirect(url_for('user_routes.dashboard'))
        if session.get('role') not in ['super_admin', 'admin_instansi']:
            flash('Role tidak valid', 'danger')
            return redirect(url_for('auth_routes.login_page'))
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

@bp.route('/dashboard')
@admin_required
def dashboard():
    # Statistik
    stats = {
        'booking_today': Booking.count_today(),
        'booking_month': Booking.count_this_month(),
        'total_users': User.count_all(),
        'active_services': Service.count_active()
    }
    
    # Booking terbaru (10 terakhir)
    recent_bookings = Booking.get_all(limit=10)
    
    # Data admin yang login
    admin = Admin.get_by_id(session.get('user_id'))
    
    return render_template('admin/dashboard.html', 
                         stats=stats, 
                         bookings=recent_bookings,
                         admin=admin)

@bp.route('/layanan')
@admin_required
def layanan():
    services = Service.get_all()
    admin = Admin.get_by_id(session.get('user_id'))
    return render_template('admin/layanan.html', services=services, admin=admin)

@bp.route('/booking-list')
@admin_required
def booking_list():
    bookings = Booking.get_all()
    admin = Admin.get_by_id(session.get('user_id'))
    return render_template('admin/booking-list.html', bookings=bookings, admin=admin)

@bp.route('/pengguna')
@admin_required
def pengguna():
    users = User.get_all()
    admin = Admin.get_by_id(session.get('user_id'))
    return render_template('admin/pengguna.html', users=users, admin=admin)

@bp.route('/security')
@admin_required
def security():
    admin = Admin.get_by_id(session.get('user_id'))
    
    # Stats untuk sidebar profile card
    stats = {
        'booking_total': Booking.count_all(),
        'service_total': Service.count_active()
    }
    
    return render_template('admin/security.html', admin=admin, stats=stats)

@bp.route('/profil')
@admin_required
def profil():
    admin = Admin.get_by_id(session.get('user_id'))
    return render_template('admin/profil.html', admin=admin)

@bp.route('/ubah-password')
@admin_required
def ubah_password():
    return render_template('admin/ubah_password.html')