"""
PublicBook - Sistem Booking & Antrean Layanan Publik
Main Application File (app.py)
"""

import os
from flask import Flask, render_template

# ============================================================
# CONFIGURATION
# ============================================================

# Path ke folder project (naik 1 level dari backend/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'frontend', 'pages'),
    static_folder=None  # Static files handled by routes/static.py blueprint
)

# Secret key untuk session (ganti di production!)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'publicbook-dev-secret-key-2026')

# ============================================================
# REGISTER BLUEPRINTS
# ============================================================

from routes.static import static_bp
from routes.auth import auth_bp
from routes.booking import booking_bp
from routes.services import services_bp
from routes.admin import admin_bp

# Static files (CSS, JS, images)
app.register_blueprint(static_bp)

# API endpoints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(booking_bp, url_prefix='/api/booking')
app.register_blueprint(services_bp, url_prefix='/api/services')
app.register_blueprint(admin_bp, url_prefix='/api/admin')

# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# ============================================================
# ROUTES: LANDING PAGE
# ============================================================

@app.route('/')
def index():
    """Landing page / Homepage"""
    return render_template('index.html')

# ============================================================
# ROUTES: AUTH PAGES (HTML Templates)
# ============================================================

@app.route('/login')
def login():
    """Login page"""
    return render_template('auth/login.html')

@app.route('/register')
def register():
    """Register page"""
    return render_template('auth/register.html')

# ============================================================
# ROUTES: USER DASHBOARD PAGES
# ============================================================

@app.route('/user/dashboard')
def user_dashboard():
    """User dashboard - overview"""
    return render_template('user/dashboard.html')

@app.route('/user/layanan')
def user_layanan():
    """User - daftar layanan tersedia"""
    return render_template('user/layanan.html')

@app.route('/user/booking')
def user_booking():
    """User - form booking + QR code"""
    return render_template('user/booking.html')

@app.route('/user/riwayat')
def user_riwayat():
    """User - riwayat pemesanan"""
    return render_template('user/riwayat.html')

@app.route('/user/profil')
def user_profil():
    """User - profil pengguna"""
    return render_template('user/profil.html')

# ============================================================
# ROUTES: ADMIN DASHBOARD PAGES
# ============================================================

@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard - overview"""
    return render_template('admin/dashboard.html')

@app.route('/admin/antrean')
def admin_antrean():
    """Admin - pantau antrean real-time"""
    return render_template('admin/antrean.html')

@app.route('/admin/booking-list')
def admin_booking_list():
    """Admin - daftar semua booking"""
    return render_template('admin/booking-list.html')

@app.route('/admin/layanan')
def admin_layanan():
    """Admin - kelola layanan"""
    return render_template('admin/layanan.html')

@app.route('/admin/pengguna')
def admin_pengguna():
    """Admin - kelola user/pengguna"""
    return render_template('admin/pengguna.html')

@app.route('/admin/security')
def admin_security():
    """Admin - keamanan & audit log"""
    return render_template('admin/security.html')

# ============================================================
# ROUTES: LEGAL PAGES
# ============================================================

@app.route('/disclaimer')
def disclaimer():
    """Disclaimer / Batasan tanggung jawab"""
    return render_template('legal/disclaimer.html')

@app.route('/privacy')
def privacy():
    """Kebijakan privasi"""
    return render_template('legal/privacy.html')

@app.route('/terms')
def terms():
    """Syarat & ketentuan"""
    return render_template('legal/terms.html')

@app.route('/about')
def about():
    """Tentang PublicBook"""
    return render_template('legal/about.html')

@app.route('/hubungi')
def hubungi():
    """Hubungi kami / Kontak"""
    return render_template('legal/hubungi.html')

# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000
    )