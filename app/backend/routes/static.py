# backend/routes/static.py
from flask import Blueprint, render_template

bp = Blueprint('static_routes', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/about')
def about():
    return render_template('legal/about.html')

@bp.route('/privacy')
def privacy():
    return render_template('legal/privacy.html')

@bp.route('/terms')
def terms():
    return render_template('legal/terms.html')

@bp.route('/hubungi')
def hubungi():
    return render_template('legal/hubungi.html')

@bp.route('/disclaimer')
def disclaimer():
    return render_template('legal/disclaimer.html')
