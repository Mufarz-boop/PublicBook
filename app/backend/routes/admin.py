from flask import Blueprint, render_template

bp = Blueprint('admin_routes', __name__)

@bp.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin/dashboard.html')