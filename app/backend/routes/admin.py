# backend/routes/admin.py
from flask import Blueprint, render_template, session, redirect, url_for, flash

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
    return render_template('admin/dashboard.html')

@bp.route('/layanan')
@admin_required
def layanan():
    return render_template('admin/layanan.html')

@bp.route('/booking-list')
@admin_required
def booking_list():
    return render_template('admin/booking-list.html')

@bp.route('/pengguna')
@admin_required
def pengguna():
    return render_template('admin/pengguna.html')

@bp.route('/security')
@admin_required
def security():
    return render_template('admin/security.html')

@bp.route('/profil')
@admin_required
def profil():
    return render_template('admin/profil.html')

@bp.route('/ubah-password')
@admin_required
def ubah_password():
    return render_template('admin/ubah_password.html')
