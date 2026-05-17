from flask import Flask, session
from config import config_by_publicbook
from database.database import init_db, close_db, get_db
from sqlalchemy import text
import socket
import os
import subprocess
import re

env = os.getenv('ENV', 'development')

app = Flask(
    __name__,
    template_folder='../frontend/pages',
    static_folder='../frontend/assets'
)
app.config.from_object(config_by_publicbook[env])

app.jinja_env.auto_reload = True
app.config['TEMPLATES_AUTO_RELOAD'] = True

# ═══════════════════════════════════════════════════════════════════
# KONFIGURASI PORT
# ═══════════════════════════════════════════════════════════════════
PORT = int(os.getenv('PORT', os.getenv('FLASK_RUN_PORT', 5000)))
app.config['PORT'] = PORT

try:
    init_db(app)
except Exception as e:
    print(f"Database initialization failed: {e}")
    raise

@app.teardown_appcontext
def teardown_db(exception):
    close_db()


# ═══════════════════════════════════════════════════════════════════
# DETEKSI IP LOKAL
# ═══════════════════════════════════════════════════════════════════
def get_all_local_ips():
    ips = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(2)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith("127."):
            ips.append(ip)
    except:
        pass

    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        if ip and not ip.startswith("127.") and ip not in ips:
            ips.append(ip)
    except:
        pass

    try:
        if os.name == 'nt':
            result = subprocess.run(['ipconfig'], capture_output=True, text=True)
            ip_pattern = r'IPv4 Address[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)'
            found = re.findall(ip_pattern, result.stdout)
            for ip in found:
                if not ip.startswith("127.") and ip not in ips:
                    ips.append(ip)
        else:
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
            found = result.stdout.strip().split()
            for ip in found:
                if not ip.startswith("127.") and ip not in ips:
                    ips.append(ip)
    except:
        pass

    return ips


def get_best_local_ip():
    ips = get_all_local_ips()
    for ip in ips:
        if ip.startswith("192.168."):
            return ip
    for ip in ips:
        if ip.startswith(("10.", "172.")):
            return ip
    if ips:
        return ips[0]
    return '127.0.0.1'


# ═══════════════════════════════════════════════════════════════════
# Context processor untuk current_user
# ═══════════════════════════════════════════════════════════════════
@app.context_processor
def inject_current_user():
    user_id = session.get('user_id')
    if user_id:
        db = get_db()
        row = db.execute(
            text("SELECT * FROM users WHERE id = :id"),
            {'id': user_id}
        ).mappings().first()

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
                    self.nama = data.get('nama_lengkap') or data.get('nama', 'User')
                    self.email = data.get('email', 'user@email.com')
                    self.avatar = data.get('avatar')
                    self.role = data.get('role', 'user')
                    self.is_admin = bool(data.get('is_admin', False))
                    self.is_authenticated = True

            return {'current_user': CurrentUser(user)}

    class AnonymousUser:
        is_authenticated = False
        is_admin = False
        nama = None
        email = None
        avatar = None
        role = None

    return {'current_user': AnonymousUser()}


# ═══════════════════════════════════════════════════════════════════
# Context processor untuk local_ip
# ═══════════════════════════════════════════════════════════════════
@app.context_processor
def inject_local_ip():
    manual_ip = os.getenv('PUBLICBOOK_IP')
    local_ip = manual_ip if manual_ip else get_best_local_ip()
    port = app.config.get('PORT', 5000)
    local_url = f'http://{local_ip}:{port}'

    return {
        'local_ip': local_ip,
        'local_url': local_url,
        'port': port,
        'server_url': local_url
    }


# ═══════════════════════════════════════════════════════════════════
# REGISTER BLUEPRINTS
# ═══════════════════════════════════════════════════════════════════
from routes.static import bp as static_bp
from routes.auth import bp as auth_bp
from routes.auth_api import bp as auth_api_bp
from routes.user import bp as user_bp
from routes.admin import bp as admin_bp
from routes.scan import bp as scan_bp
# HAPUS: from routes.booking import bp as booking_bp  ← file tidak ada
from routes.services import bp as services_bp

app.register_blueprint(static_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(auth_api_bp)
app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(scan_bp)
# HAPUS: app.register_blueprint(booking_bp)  ← file tidak ada
app.register_blueprint(services_bp)


if __name__ == '__main__':
    detected_ip = get_best_local_ip()
    all_ips = get_all_local_ips()

    print("=" * 60)
    print("🚀 PUBLICBOOK SERVER STARTED")
    print("=" * 60)
    print(f"🌐 Local URL:      http://localhost:{PORT}")
    print(f"📡 Best Network IP: http://{detected_ip}:{PORT}")
    if len(all_ips) > 1:
        print(f"📡 All IPs found:   {', '.join(all_ips)}")
    print(f"📱 QR Scan URL:    http://{detected_ip}:{PORT}/scan/<token>")
    print("=" * 60)
    print("🔐 QR TOKEN SYSTEM: Aktif")
    print("   - Token unik per booking")
    print("   - Expired 24 jam")
    print("   - Hanya Admin yang bisa scan")
    print("   - Password Admin wajib untuk konfirmasi")
    print("=" * 60)

    app.run(
        host='0.0.0.0',
        debug=app.config.get('DEBUG', True), 
        port=PORT
    )