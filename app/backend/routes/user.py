# backend/routes/user.py
from flask import Blueprint, render_template, session, redirect, url_for

bp = Blueprint('user_routes', __name__, url_prefix='/user')

@bp.route('/dashboard')
def dashboard():
    """Dashboard untuk user biasa."""
    if not session.get('user_id') or session.get('is_admin'):
        return redirect(url_for('auth_routes.login_page'))
    return render_template('user/dashboard.html')