from flask import Blueprint, render_template

bp = Blueprint('admin_routes', __name__)

@bp.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin/dashboard.html')

@bp.route('/admin/layanan')
def admin_layanan():
    return render_template('admin/layanan.html')

@bp.route('/admin/booking-list')
def admin_booking_list():
    return render_template('admin/booking-list.html')

@bp.route('/admin/pengguna')
def admin_pengguna():
    return render_template('admin/pengguna.html')

@bp.route('/admin/security')
def admin_security():
    return render_template('admin/security.html')

@bp.route('/admin/profil')
def admin_profil():
    return render_template('admin/profil.html')

@bp.route('/admin/ubah-password')
def admin_ubah_password():
    return render_template('admin/ubah_password.html')

