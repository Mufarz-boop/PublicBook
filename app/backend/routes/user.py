# backend/routes/user.py
from flask import Blueprint, render_template, session, redirect, url_for, flash

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
    return render_template('user/dashboard.html')

@bp.route('/booking')
@user_required
def booking():
    return render_template('user/booking.html')

@bp.route('/layanan')
@user_required
def layanan():
    return render_template('user/layanan.html')

@bp.route('/profil')
@user_required
def profil():
    return render_template('user/profil.html')