# backend/app.py
from flask import Flask, session
from config import config_by_publicbook
from database.database import init_db, close_db, get_db
from sqlalchemy import text
import socket  # ← TAMBAHKAN INI
import os

env = os.getenv('ENV', 'development')

app = Flask(
    __name__,
    template_folder='../frontend/pages',
    static_folder='../frontend/assets'
)
app.config.from_object(config_by_publicbook[env])

# Auto-reload template (tidak perlu restart server tiap ubah HTML)
app.jinja_env.auto_reload = True
app.config['TEMPLATES_AUTO_RELOAD'] = True

try:
    init_db(app)
except Exception as e:
    print(f"Database initialization failed: {e}")
    print("Pastikan:")
    print("  1. Laragon/XAMPP MySQL sudah START")
    print("  2. .env berada di root folder")
    print("  3. Database db_publicbook sudah dibuat di phpMyAdmin")
    raise

@app.teardown_appcontext
def teardown_db(exception):
    close_db()

# ═══════════════════════════════════════════════════════════════════
# Context processor untuk current_user
# ═══════════════════════════════════════════════════════════════════
@app.context_processor
def inject_current_user():
    user_id = session.get('user_id')
    if user_id:
        db = get_db()
        # ═══════════════════════════════════════════════════════════
        # PERUBAHAN: Query SELECT * lalu ambil field yang ada
        # SEBELUM: SELECT id, nama, nama_lengkap, email, avatar, is_admin
        #          → error karena kolom 'nama' tidak ada di tabel
        # SESUDAH: SELECT * → ambil semua kolom, lalu cek field yang ada
        # ═══════════════════════════════════════════════════════════
        row = db.execute(
            text("SELECT * FROM users WHERE id = :id"),
            {'id': user_id}
        ).mappings().first()
        
        # Kalau tidak di users, cek tabel admins
        if not row:
            row = db.execute(
                text("SELECT * FROM admins WHERE id = :id"),
                {'id': user_id}
            ).mappings().first()
        
        if row:
            user = dict(row)
            class CurrentUser:
                def __init__(self, data):
                    self.id = data['id']
                    # ═══════════════════════════════════════════════
                    # PERUBAHAN: Support nama_lengkap (bukan nama)
                    # SEBELUM: data.get('nama') or data.get('nama_lengkap', 'User')
                    # SESUDAH: data.get('nama_lengkap') or data.get('nama', 'User')
                    # ═══════════════════════════════════════════════
                    self.nama = data.get('nama_lengkap') or data.get('nama', 'User')
                    self.email = data.get('email', 'user@email.com')
                    self.avatar = data.get('avatar')
                    self.role = data.get('role', 'user')
                    self.is_admin = bool(data.get('is_admin', False))
                    self.is_authenticated = True
            
            return {'current_user': CurrentUser(user)}
    
    # Anonymous user (belum login)
    class AnonymousUser:
        is_authenticated = False
        is_admin = False
        nama = None
        email = None
        avatar = None
        role = None
    
    return {'current_user': AnonymousUser()}

# ═══════════════════════════════════════════════════════════════════
# Context processor untuk local_ip (auto-detect untuk QR Code)
# ═══════════════════════════════════════════════════════════════════
@app.context_processor
def inject_local_ip():
    """Auto-detect IP lokal untuk QR Code"""
    try:
        # Cara 1: Connect ke Google DNS untuk dapat IP outbound
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        # Fallback: coba ambil dari hostname
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            local_ip = '127.0.0.1'  # Last resort fallback
    
    port = app.config.get('PORT', 5000)
    return {
        'local_ip': local_ip,
        'local_url': f'http://{local_ip}:{port}'
    }

from routes.static import bp as static_bp
from routes.auth import bp as auth_bp
from routes.auth_api import bp as auth_api_bp
from routes.user import bp as user_bp
from routes.admin import bp as admin_bp
from routes.scan import bp as scan_bp

app.register_blueprint(static_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(auth_api_bp)
app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(scan_bp)

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',  # ← TAMBAHKAN INI (agar bisa diakses dari HP/lan)
        debug=app.config.get('DEBUG', True), 
        port=app.config.get('PORT', 5000)
    )