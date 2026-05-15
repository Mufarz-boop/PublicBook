# backend/routes/auth_api.py
from flask import Blueprint, request, jsonify, session
import bcrypt
from werkzeug.security import check_password_hash  # ← legacy support
from database.database import get_db
from sqlalchemy import text
import jwt
import datetime
from utils.password import hash_password, verify_password # ← gunakan util untuk konsistensi
from flask import current_app

bp = Blueprint('auth_api', __name__, url_prefix='/api/auth')

def _get_user_by_email(db_session, email):
    cols = db_session.execute(text("SELECT COLUMN_NAME as name FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users'")).mappings().all()
    colset = {c['name'] for c in cols}
    if 'email' not in colset:
        return None, colset, None
    pw_col = 'password' if 'password' in colset else ('password_hash' if 'password_hash' in colset else None)
    row = db_session.execute(text("SELECT * FROM users WHERE email = :email LIMIT 1"), {'email': email}).mappings().first()
    return (row and dict(row) or None), colset, pw_col

def _get_admin_by_email(db_session, email):
    row = db_session.execute(text("SELECT * FROM admins WHERE email = :email AND status = 'active' LIMIT 1"), {'email': email}).mappings().first()
    return row and dict(row) or None

def generate_token(user_id, role, is_admin=False):
    payload = {'user_id': user_id, 'role': role, 'is_admin': is_admin, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60), 'iat': datetime.datetime.utcnow()}
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

# ========== BCRYPT HELPERS ==========
def hash_password(plain_password: str) -> str:
    """Hash password dengan bcrypt"""
    password_bytes = plain_password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifikasi password — support bcrypt & scrypt/werkzeug legacy"""
    if not hashed_password:
        return False
    # bcrypt format
    if hashed_password.startswith('$2'):
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    # scrypt / pbkdf2 legacy (Werkzeug)
    return check_password_hash(hashed_password, plain_password)
# ====================================

@bp.route('/register', methods=['POST'])
def api_register():
    payload = request.get_json(silent=True) or {}
    nama = (payload.get('nama_lengkap') or payload.get('nama') or '').strip()
    email = (payload.get('email') or '').strip().lower()
    telepon = (payload.get('nomor_telepon') or payload.get('telepon') or '').strip()
    password = payload.get('password') or ''
    if not all([nama, email, telepon, password]):
        return jsonify({'ok': False, 'message': 'Data tidak lengkap'}), 400
    if len(password) < 6:
        return jsonify({'ok': False, 'message': 'Password minimal 6 karakter'}), 400
    db_session = get_db()
    user, colset, _ = _get_user_by_email(db_session, email)
    if user:
        return jsonify({'ok': False, 'message': 'Email sudah terdaftar'}), 409
    actual = {}
    if 'email' in colset: actual['email'] = email
    if 'nama_lengkap' in colset: actual['nama_lengkap'] = nama
    elif 'nama' in colset: actual['nama'] = nama
    if 'nomor_telepon' in colset: actual['nomor_telepon'] = telepon
    elif 'telepon' in colset: actual['telepon'] = telepon
    pw_col = 'password' if 'password' in colset else ('password_hash' if 'password_hash' in colset else None)
    if not pw_col:
        return jsonify({'ok': False, 'message': 'Kolom password tidak ditemukan'}), 500
    actual[pw_col] = hash_password(password)
    if 'status' in colset: actual['status'] = 'active'
    keys = ', '.join(actual.keys())
    placeholders = ', '.join([f':{k}' for k in actual.keys()])
    try:
        db_session.execute(text(f"INSERT INTO users ({keys}) VALUES ({placeholders})"), actual)
        db_session.commit()
        return jsonify({'ok': True, 'message': 'Registrasi berhasil', 'email': email}), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({'ok': False, 'message': str(e)}), 500

@bp.route('/login', methods=['POST'])
def api_login():
    payload = request.get_json(silent=True) or {}
    email = (payload.get('email') or '').strip().lower()
    password = payload.get('password') or ''
    if not email or not password:
        return jsonify({'ok': False, 'message': 'Email dan password wajib diisi'}), 400
    db_session = get_db()
    
    # ─────────────────────────────────────────────────────────────
    # CEK ADMIN LOGIN
    # ─────────────────────────────────────────────────────────────
    admin = _get_admin_by_email(db_session, email)
    if admin:
        admin_pw = admin.get('password') or admin.get('password_hash', '')
        if verify_password(password, admin_pw):
            token = generate_token(admin['id'], admin.get('role', 'admin_instansi'), is_admin=True)
            session['user_id'] = admin['id']
            session['role'] = admin.get('role', 'admin_instansi')
            session['is_admin'] = True
            session['token'] = token
            # ═══════════════════════════════════════════════════════
            # PERUBAHAN: Tambah user data ke session untuk template
            # ═══════════════════════════════════════════════════════
            session['user_nama'] = admin.get('nama', 'Admin')
            session['user_email'] = admin.get('email', email)
            session['user_avatar'] = admin.get('avatar')
            return jsonify({'ok': True, 'message': 'Login berhasil', 'role': admin.get('role', 'admin_instansi'), 'token': token}), 200
    
    # ─────────────────────────────────────────────────────────────
    # CEK USER LOGIN
    # ─────────────────────────────────────────────────────────────
    user, colset, pw_col = _get_user_by_email(db_session, email)
    if user and pw_col:
        if verify_password(password, user[pw_col]):
            token = generate_token(user['id'], 'user', is_admin=False)
            session['user_id'] = user['id']
            session['role'] = 'user'
            session['is_admin'] = False
            session['token'] = token
            # ═══════════════════════════════════════════════════════
            # PERUBAHAN: Tambah user data ke session untuk template
            # SEBELUM: tidak ada baris ini → template error undefined
            # SESUDAH: session punya nama, email, avatar
            # ═══════════════════════════════════════════════════════
            session['user_nama'] = user.get('nama') or user.get('nama_lengkap', 'User')
            session['user_email'] = user.get('email', email)
            session['user_avatar'] = user.get('avatar')
            return jsonify({'ok': True, 'message': 'Login berhasil', 'role': 'user', 'token': token}), 200
    
    return jsonify({'ok': False, 'message': 'Email atau password salah'}), 401

@bp.route('/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'ok': True, 'message': 'Logout berhasil'}), 200

@bp.route('/forgot-password', methods=['POST'])
def api_forgot_password():
    payload = request.get_json(silent=True) or {}
    email = (payload.get('email') or '').strip().lower()
    if not email:
        return jsonify({'ok': False, 'message': 'Email wajib diisi'}), 400
    db_session = get_db()
    user, _, _ = _get_user_by_email(db_session, email)
    admin = _get_admin_by_email(db_session, email)
    if not user and not admin:
        return jsonify({'ok': False, 'message': 'Email tidak ditemukan'}), 404
    return jsonify({'ok': True, 'message': 'Kode verifikasi terkirim (demo: 123456)', 'demo_code': '123456'}), 200

@bp.route('/reset-password', methods=['POST'])
def api_reset_password():
    payload = request.get_json(silent=True) or {}
    email = (payload.get('email') or '').strip().lower()
    otp = (payload.get('otp') or '').strip()
    new_password = payload.get('new_password') or ''
    if not email or not otp or not new_password:
        return jsonify({'ok': False, 'message': 'Data tidak lengkap'}), 400
    if len(new_password) < 6:
        return jsonify({'ok': False, 'message': 'Password minimal 6 karakter'}), 400
    if otp != '123456':
        return jsonify({'ok': False, 'message': 'Kode verifikasi salah'}), 400
    db_session = get_db()
    user, colset, pw_col = _get_user_by_email(db_session, email)
    if user and pw_col:
        db_session.execute(text(f"UPDATE users SET {pw_col} = :pw WHERE email = :email"), {'pw': hash_password(new_password), 'email': email})
        db_session.commit()
        return jsonify({'ok': True, 'message': 'Password berhasil direset'}), 200
    admin = _get_admin_by_email(db_session, email)
    if admin:
        pw_col = 'password' if 'password' in admin else 'password_hash'
        db_session.execute(text(f"UPDATE admins SET {pw_col} = :pw WHERE email = :email"), {'pw': hash_password(new_password), 'email': email})
        db_session.commit()
        return jsonify({'ok': True, 'message': 'Password berhasil direset'}), 200
    return jsonify({'ok': False, 'message': 'Email tidak ditemukan'}), 404