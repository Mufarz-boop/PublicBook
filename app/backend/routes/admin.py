# backend/routes/admin.py
"""Admin Routes untuk PublicBook
Semua route dilindungi dengan session check
Redirect ke login kalau belum login atau bukan admin
"""

from flask import Blueprint, render_template, session, redirect, url_for, flash

bp = Blueprint('admin_routes', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator untuk proteksi route admin"""
    def decorated(*args, **kwargs):
        # Cek sudah login
        if not session.get('user_id'):
            flash('Silakan login terlebih dahulu', 'warning')
            return redirect(url_for('auth_routes.login_page'))

        # Cek adalah admin
        if not session.get('is_admin'):
            flash('Akses ditolak. Halaman ini khusus admin.', 'danger')
            return redirect(url_for('user_routes.dashboard'))

        # Cek role valid
        role = session.get('role')
        if role not in ['super_admin', 'admin_instansi']:
            flash('Role tidak memiliki akses ke halaman ini', 'danger')
            return redirect(url_for('auth_routes.login_page'))

        return f(*args, **kwargs)

    # Preserve function name
    decorated.__name__ = f.__name__
    return decorated


# ============================================
# DASHBOARD
# ============================================
@bp.route('/dashboard')
@admin_required
def dashboard():
    """Dashboard utama admin"""
    return render_template('admin/dashboard.html')


# ============================================
# MANAJEMEN LAYANAN
# ============================================
@bp.route('/layanan')
@admin_required
def layanan():
    """Halaman manajemen layanan instansi"""
    return render_template('admin/layanan.html')


# ============================================
# MANAJEMEN BOOKING
# ============================================
@bp.route('/booking-list')
@admin_required
def booking_list():
    """Halaman daftar booking / antrean"""
    return render_template('admin/booking-list.html')


# ============================================
# MANAJEMEN PENGGUNA
# ============================================
@bp.route('/pengguna')
@admin_required
def pengguna():
    """Halaman daftar pengguna (warga)"""
    return render_template('admin/pengguna.html')


# ============================================
# SECURITY LOGS
# ============================================
@bp.route('/security')
@admin_required
def security():
    """Halaman log keamanan (login/logout/failed)"""
    return render_template('admin/security.html')


# ============================================
# PROFIL ADMIN
# ============================================
@bp.route('/profil')
@admin_required
def profil():
    """Halaman profil admin"""
    return render_template('admin/profil.html')


# ============================================
# UBAH PASSWORD
# ============================================
@bp.route('/ubah-password')
@admin_required
def ubah_password():
    """Halaman ubah password admin"""
    return render_template('admin/ubah_password.html')