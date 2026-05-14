# backend/routes/auth.py
from flask import Blueprint, render_template, redirect, url_for, session

bp = Blueprint('auth_routes', __name__)

@bp.route('/login')
def login_page():
    """Render halaman login."""
    if session.get('user_id'):
        if session.get('is_admin'):
            return redirect(url_for('admin_routes.dashboard'))
        return redirect(url_for('user_routes.dashboard'))
    return render_template('auth/login.html')

@bp.route('/register')
def register_page():
    """Render halaman register."""
    if session.get('user_id'):
        return redirect(url_for('auth_routes.login_page'))
    return render_template('auth/register.html')

@bp.route('/forgot-password')
def forgot_password():
    """Render halaman lupa password."""
    return render_template('auth/forgot_password.html')