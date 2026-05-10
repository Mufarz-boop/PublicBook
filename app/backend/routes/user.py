from flask import Blueprint, render_template

bp = Blueprint('user_routes', __name__)

@bp.route('/user/dashboard')
def user_dashboard():
    return render_template('user/dashboard.html')