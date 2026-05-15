from flask import Blueprint, render_template, redirect, url_for, session, flash

bp = Blueprint('auth_routes', __name__)

@bp.route('/login')
def login_page():
    if session.get('user_id'):
        if session.get('is_admin'):
            return redirect(url_for('admin_routes.dashboard'))
        return redirect(url_for('user_routes.dashboard'))
    return render_template('auth/login.html')

@bp.route('/register')
def register_page():
    if session.get('user_id'):
        return redirect(url_for('auth_routes.login_page'))
    return render_template('auth/register.html')

@bp.route('/forgot-password')
def forgot_password():
    return render_template('auth/forgot_password.html')

@bp.route('/logout')
def logout():
    """Logout user/admin — clear session dan redirect ke login page"""
    session.clear()
    flash('Anda telah logout', 'info')
    # ═══════════════════════════════════════════════════════════════
    # PERUBAHAN: redirect string hardcoded → url_for() agar konsisten
    # SEBELUM: return redirect('/login')
    # SESUDAH: return redirect(url_for('auth_routes.login_page'))
    # ═══════════════════════════════════════════════════════════════
    return redirect(url_for('auth_routes.login_page'))