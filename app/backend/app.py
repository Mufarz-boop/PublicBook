# backend/app.py
from flask import Flask, session, request, flash, redirect, url_for, current_app
from werkzeug.utils import secure_filename
from config import config_by_publicbook
from database.database import init_db, close_db, get_db
from sqlalchemy import text
from datetime import datetime
import socket
import os

env = os.getenv('ENV', 'development')

app = Flask(
    __name__,
    template_folder='../frontend/pages',
    static_folder='../frontend/assets'
)
app.config.from_object(config_by_publicbook[env])

# ═══════════════════════════════════════════════════════════════════
# KONFIGURASI UPLOAD FOTO PROFIL
# ═══════════════════════════════════════════════════════════════════
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'assets', 'uploads', 'profil')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
# Helper: Cek ekstensi file yang diizinkan
# ═══════════════════════════════════════════════════════════════════
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ═══════════════════════════════════════════════════════════════════
# Context processor untuk current_user
# ═══════════════════════════════════════════════════════════════════
@app.context_processor
def inject_current_user():
    user_id = session.get('user_id')
    if user_id:
        db = get_db()
        # Query SELECT * untuk ambil semua kolom yang ada
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
                    # Support nama_lengkap (sesuai struktur tabel)
                    self.nama = data.get('nama_lengkap', 'User')
                    self.nama_lengkap = data.get('nama_lengkap', 'User')
                    self.email = data.get('email', 'user@email.com')
                    # Hanya foto_profil (sesuai struktur tabel, tidak ada avatar)
                    self.foto_profil = data.get('foto_profil')
                    self.nomor_telepon = data.get('nomor_telepon', '')
                    self.alamat = data.get('alamat', '')
                    # Status di DB: active/inactive (bukan aktif)
                    self.status = data.get('status', 'active')
                    self.role = data.get('role', 'user')
                    self.is_admin = bool(data.get('is_admin', False))
                    self.is_authenticated = True

            return {'current_user': CurrentUser(user), 'user': CurrentUser(user)}

    # Anonymous user (belum login)
    class AnonymousUser:
        is_authenticated = False
        is_admin = False
        nama = None
        nama_lengkap = None
        email = None
        foto_profil = None
        nomor_telepon = None
        alamat = None
        status = None
        role = None

    return {'current_user': AnonymousUser(), 'user': AnonymousUser()}

# ═══════════════════════════════════════════════════════════════════
# ROUTE: Upload Foto Profil
# ═══════════════════════════════════════════════════════════════════
@app.route('/profil/upload-foto', methods=['POST'])
def upload_foto():
    """Handle upload foto profil user"""
    user_id = session.get('user_id')
    if not user_id:
        flash('Silakan login terlebih dahulu', 'error')
        return redirect(url_for('auth.login'))

    # Cek apakah ada file yang diupload
    if 'foto' not in request.files:
        flash('Tidak ada file yang dipilih', 'error')
        return redirect(url_for('user_routes.profil'))

    file = request.files['foto']

    if file.filename == '':
        flash('Tidak ada file yang dipilih', 'error')
        return redirect(url_for('user_routes.profil'))

    if file and allowed_file(file.filename):
        db = get_db()

        # Ambil data user untuk cek foto lama - HANYA foto_profil
        row = db.execute(
            text("SELECT foto_profil FROM users WHERE id = :id"),
            {'id': user_id}
        ).mappings().first()

        # Hapus foto lama jika ada dan bukan foto default
        if row:
            old_foto = row.get('foto_profil')
            if old_foto and 'Afdal Adha Firnansyah.png' not in old_foto:
                old_path = os.path.join(UPLOAD_FOLDER, os.path.basename(old_foto))
                if os.path.exists(old_path):
                    os.remove(old_path)

        # Generate nama file unik dengan timestamp
        ext = secure_filename(file.filename).rsplit('.', 1)[1].lower()
        filename = f"profil_{user_id}_{int(datetime.now().timestamp())}.{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        # Simpan file
        file.save(filepath)

        # Path relatif untuk disimpan di database (dari folder assets)
        foto_profil_path = f"uploads/profil/{filename}"

        # Update database - hanya kolom foto_profil
        db.execute(
            text("UPDATE users SET foto_profil = :foto WHERE id = :id"),
            {'foto': foto_profil_path, 'id': user_id}
        )
        db.commit()

        flash('Foto profil berhasil diperbarui!', 'success')
    else:
        flash('Format file tidak didukung. Gunakan JPG, PNG, atau GIF (Max 2MB).', 'error')

    return redirect(url_for('user_routes.profil'))

# ═══════════════════════════════════════════════════════════════════
# ROUTE: Hapus Foto Profil (Reset ke Default)
# ═══════════════════════════════════════════════════════════════════
@app.route('/profil/hapus-foto', methods=['POST'])
def hapus_foto():
    """Hapus foto profil dan reset ke default"""
    user_id = session.get('user_id')
    if not user_id:
        flash('Silakan login terlebih dahulu', 'error')
        return redirect(url_for('auth.login'))

    db = get_db()

    # Ambil foto lama - HANYA foto_profil
    row = db.execute(
        text("SELECT foto_profil FROM users WHERE id = :id"),
        {'id': user_id}
    ).mappings().first()

    # Hapus file foto lama
    if row:
        old_foto = row.get('foto_profil')
        if old_foto and 'Afdal Adha Firnansyah.png' not in old_foto:
            old_path = os.path.join(UPLOAD_FOLDER, os.path.basename(old_foto))
            if os.path.exists(old_path):
                os.remove(old_path)

    # Reset foto_profil di database ke NULL
    db.execute(
        text("UPDATE users SET foto_profil = NULL WHERE id = :id"),
        {'id': user_id}
    )
    db.commit()

    flash('Foto profil dihapus. Menggunakan foto default.', 'success')
    return redirect(url_for('user_routes.profil'))

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
        host='0.0.0.0',  # ← WAJIB untuk akses dari HP
        debug=app.config.get('DEBUG', True), 
        port=app.config.get('PORT', 5000)
    )