# backend/routes/admin.py
from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from models.user import User
from models.booking import Booking
from models.services import Service
from models.admin import Admin
from auth_api import verify_password, hash_password  # import dari auth_api.py
from database.database import get_db
from sqlalchemy import text

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
    stats = {
        'booking_today': Booking.count_today(),
        'booking_month': Booking.count_this_month(),
        'total_users': User.count_all(),
        'active_services': Service.count_active()
    }
    recent_bookings = Booking.get_all(limit=10)
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
    stats = {
        'booking_total': Booking.count_all(),
        'service_total': Service.count_active()
    }
    return render_template('admin/security.html', admin=admin, stats=stats)

@bp.route('/security/ubah-password', methods=['POST'])
@admin_required
def ubah_password_post():
    """Proses ubah password admin"""
    admin_id = session.get('user_id')
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    # Validasi input
    if not all([current_password, new_password, confirm_password]):
        flash('Semua field wajib diisi', 'danger')
        return redirect(url_for('admin_routes.security'))
    
    if len(new_password) < 6:
        flash('Password baru minimal 6 karakter', 'danger')
        return redirect(url_for('admin_routes.security'))
    
    if new_password != confirm_password:
        flash('Password baru dan konfirmasi tidak cocok', 'danger')
        return redirect(url_for('admin_routes.security'))
    
    # Ambil data admin dari database
    db = get_db()
    admin = db.execute(
        text("SELECT * FROM admins WHERE id = :id"),
        {'id': admin_id}
    ).mappings().first()
    
    if not admin:
        flash('Data admin tidak ditemukan', 'danger')
        return redirect(url_for('admin_routes.security'))
    
    # Verifikasi password saat ini
    admin_dict = dict(admin)
    stored_password = admin_dict.get('password') or admin_dict.get('password_hash', '')
    
    if not verify_password(current_password, stored_password):
        flash('Password saat ini salah', 'danger')
        return redirect(url_for('admin_routes.security'))
    
    # Update password baru
    pw_col = 'password' if 'password' in admin_dict else 'password_hash'
    try:
        db.execute(
            text(f"UPDATE admins SET {pw_col} = :pw WHERE id = :id"),
            {'pw': hash_password(new_password), 'id': admin_id}
        )
        db.commit()
        flash('Password berhasil diubah', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Gagal mengubah password: {str(e)}', 'danger')
    
    return redirect(url_for('admin_routes.security'))

@bp.route('/profil')
@admin_required
def profil():
    admin = Admin.get_by_id(session.get('user_id'))
    return render_template('admin/profil.html', admin=admin)

@bp.route('/ubah-password')
@admin_required
def ubah_password():
    return redirect(url_for('admin_routes.security'))