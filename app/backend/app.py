# backend/app.py
from flask import Flask, session, request, flash, redirect, url_for, current_app
from werkzeug.utils import secure_filename
from config import config_by_publicbook
from database.database import init_db, close_db, get_db
from sqlalchemy import text
from datetime import datetime
import os

env = os.getenv('ENV', 'development')

app = Flask(
    __name__,
    template_folder='../frontend/pages',
    static_folder='../frontend/assets'
)
app.config.from_object(config_by_publicbook[env])

# ═══════════════════════════════════════════════════════════════════
# KONFIGURASI UPLOAD FOTO
# ═══════════════════════════════════════════════════════════════════
UPLOAD_FOLDER_PROFIL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'assets', 'uploads', 'profil')
UPLOAD_FOLDER_COVER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'assets', 'uploads', 'cover')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

os.makedirs(UPLOAD_FOLDER_PROFIL, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_COVER, exist_ok=True)

app.config['UPLOAD_FOLDER_PROFIL'] = UPLOAD_FOLDER_PROFIL
app.config['UPLOAD_FOLDER_COVER'] = UPLOAD_FOLDER_COVER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # Max 5MB

# Auto-reload template
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
                    self.nama_lengkap = data.get('nama_lengkap', self.nama)
                    self.email = data.get('email', 'user@email.com')
                    self.foto_profil = data.get('foto_profil')
                    self.foto_cover = data.get('foto_cover')
                    self.nomor_telepon = data.get('nomor_tengkap', '')
                    self.alamat = data.get('alamat', '')
                    self.status = data.get('status', 'active')
                    self.role = data.get('role', 'user')
                    self.is_admin = bool(data.get('is_admin', False))
                    self.is_authenticated = True
                    self.instansi_nama = data.get('instansi_nama', '')

            return {'current_user': CurrentUser(user), 'user': CurrentUser(user)}

    class AnonymousUser:
        is_authenticated = False
        is_admin = False
        nama = None
        nama_lengkap = None
        email = None
        foto_profil = None
        foto_cover = None
        nomor_telepon = None
        alamat = None
        status = None
        role = None
        instansi_nama = None

    return {'current_user': AnonymousUser(), 'user': AnonymousUser()}

# ═══════════════════════════════════════════════════════════════════
# HELPER: Hapus file lama
# ═══════════════════════════════════════════════════════════════════
def hapus_file_lama(folder, old_foto, exclude_default=None):
    """Hapus file lama jika ada dan bukan file default"""
    if old_foto and exclude_default and exclude_default not in old_foto:
        old_path = os.path.join(folder, os.path.basename(old_foto))
        if os.path.exists(old_path):
            os.remove(old_path)

# ═══════════════════════════════════════════════════════════════════
# HELPER: Simpan file upload
# ═══════════════════════════════════════════════════════════════════
def simpan_file_upload(file, folder, user_id, prefix):
    """Simpan file dan return path relatif"""
    ext = secure_filename(file.filename).rsplit('.', 1)[1].lower()
    filename = f"{prefix}_{user_id}_{int(datetime.now().timestamp())}.{ext}"
    filepath = os.path.join(folder, filename)
    file.save(filepath)
    return f"uploads/{os.path.basename(folder)}/{filename}"

# ═══════════════════════════════════════════════════════════════════
# ROUTE: Upload Foto Profil (User & Admin)
# ═══════════════════════════════════════════════════════════════════
@app.route('/profil/upload-foto', methods=['POST'])
def upload_foto():
    """Handle upload foto profil"""
    user_id = session.get('user_id')
    if not user_id:
        flash('Silakan login terlebih dahulu', 'error')
        return redirect(url_for('auth.login'))

    if 'foto' not in request.files:
        flash('Tidak ada file yang dipilih', 'error')
        return redirect_back()

    file = request.files['foto']
    if file.filename == '':
        flash('Tidak ada file yang dipilih', 'error')
        return redirect_back()

    if file and allowed_file(file.filename):
        db = get_db()

        # Cek tabel mana
        user_row = db.execute(text("SELECT foto_profil FROM users WHERE id = :id"), {'id': user_id}).mappings().first()
        admin_row = None
        if not user_row:
            admin_row = db.execute(text("SELECT foto_profil FROM admins WHERE id = :id"), {'id': user_id}).mappings().first()

        # Hapus foto lama
        old_foto = (user_row.get('foto_profil') if user_row else None) or (admin_row.get('foto_profil') if admin_row else None)
        hapus_file_lama(current_app.config['UPLOAD_FOLDER_PROFIL'], old_foto, 'Afdal Adha Firnansyah.png')

        # Simpan file baru
        foto_path = simpan_file_upload(file, current_app.config['UPLOAD_FOLDER_PROFIL'], user_id, 'profil')

        # Update DB
        if user_row:
            db.execute(text("UPDATE users SET foto_profil = :foto WHERE id = :id"), {'foto': foto_path, 'id': user_id})
        elif admin_row:
            db.execute(text("UPDATE admins SET foto_profil = :foto WHERE id = :id"), {'foto': foto_path, 'id': user_id})
        db.commit()

        flash('Foto profil berhasil diperbarui!', 'success')
    else:
        flash('Format file tidak didukung. Gunakan JPG, PNG, atau GIF (Max 5MB).', 'error')

    return redirect_back()

# ═══════════════════════════════════════════════════════════════════
# ROUTE: Upload Foto Cover (Admin Only)
# ═══════════════════════════════════════════════════════════════════
@app.route('/profil/upload-cover', methods=['POST'])
def upload_cover():
    """Handle upload foto cover admin"""
    user_id = session.get('user_id')
    if not user_id:
        flash('Silakan login terlebih dahulu', 'error')
        return redirect(url_for('auth.login'))

    if 'cover' not in request.files:
        flash('Tidak ada file yang dipilih', 'error')
        return redirect(url_for('admin_routes.security'))

    file = request.files['cover']
    if file.filename == '':
        flash('Tidak ada file yang dipilih', 'error')
        return redirect(url_for('admin_routes.security'))

    if file and allowed_file(file.filename):
        db = get_db()

        # Cek admin
        admin_row = db.execute(text("SELECT foto_cover FROM admins WHERE id = :id"), {'id': user_id}).mappings().first()

        if not admin_row:
            flash('Hanya admin yang bisa mengubah cover', 'error')
            return redirect(url_for('user_routes.profil'))

        # Hapus cover lama
        hapus_file_lama(current_app.config['UPLOAD_FOLDER_COVER'], admin_row.get('foto_cover'), 'background2.jpg')

        # Simpan file baru
        cover_path = simpan_file_upload(file, current_app.config['UPLOAD_FOLDER_COVER'], user_id, 'cover')

        # Update DB
        db.execute(text("UPDATE admins SET foto_cover = :cover WHERE id = :id"), {'cover': cover_path, 'id': user_id})
        db.commit()

        flash('Foto cover berhasil diperbarui!', 'success')
    else:
        flash('Format file tidak didukung. Gunakan JPG, PNG, atau GIF (Max 5MB).', 'error')

    return redirect(url_for('admin_routes.security'))

# ═══════════════════════════════════════════════════════════════════
# ROUTE: Hapus Foto Cover (Reset ke Default)
# ═══════════════════════════════════════════════════════════════════
@app.route('/profil/hapus-cover', methods=['POST'])
def hapus_cover():
    """Hapus foto cover dan reset ke default"""
    user_id = session.get('user_id')
    if not user_id:
        flash('Silakan login terlebih dahulu', 'error')
        return redirect(url_for('auth.login'))

    db = get_db()

    # Cek admin
    admin_row = db.execute(text("SELECT foto_cover FROM admins WHERE id = :id"), {'id': user_id}).mappings().first()

    if not admin_row:
        flash('Hanya admin yang bisa mengubah cover', 'error')
        return redirect(url_for('user_routes.profil'))

    # Hapus file
    hapus_file_lama(current_app.config['UPLOAD_FOLDER_COVER'], admin_row.get('foto_cover'), 'background2.jpg')

    # Reset DB
    db.execute(text("UPDATE admins SET foto_cover = NULL WHERE id = :id"), {'id': user_id})
    db.commit()

    flash('Foto cover dihapus. Menggunakan cover default.', 'success')
    return redirect(url_for('admin_routes.security'))

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

    user_row = db.execute(text("SELECT foto_profil FROM users WHERE id = :id"), {'id': user_id}).mappings().first()
    admin_row = None
    if not user_row:
        admin_row = db.execute(text("SELECT foto_profil FROM admins WHERE id = :id"), {'id': user_id}).mappings().first()

    old_foto = (user_row.get('foto_profil') if user_row else None) or (admin_row.get('foto_profil') if admin_row else None)
    hapus_file_lama(current_app.config['UPLOAD_FOLDER_PROFIL'], old_foto, 'Afdal Adha Firnansyah.png')

    if user_row:
        db.execute(text("UPDATE users SET foto_profil = NULL WHERE id = :id"), {'id': user_id})
    elif admin_row:
        db.execute(text("UPDATE admins SET foto_profil = NULL WHERE id = :id"), {'id': user_id})
    db.commit()

    flash('Foto profil dihapus. Menggunakan foto default.', 'success')
    return redirect_back()

# ═══════════════════════════════════════════════════════════════════
# HELPER: Redirect balik sesuai role
# ═══════════════════════════════════════════════════════════════════
def redirect_back():
    """Redirect ke halaman profil sesuai role"""
    if session.get('is_admin'):
        return redirect(url_for('admin_routes.profil'))
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
        host='0.0.0.0',
        debug=app.config.get('DEBUG', True), 
        port=app.config.get('PORT', 5000)
    )