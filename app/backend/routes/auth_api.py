# backend/routes/auth_api.py
"""API Authentication Routes untuk PublicBook
Menggunakan raw SQL + werkzeug.security (sesuai kode user)
Compatible dengan database schema dari SQL dump
"""

from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from database.database import get_db
from sqlalchemy import text
import jwt
import datetime
from flask import current_app
from functools import wraps

bp = Blueprint('auth_api', __name__, url_prefix='/api/auth')


def _get_user_by_email(db_session, email: str):
    """Ambil user dari tabel users berdasarkan email
    Returns: (user_dict, colset, pw_col) atau (None, colset, None)
    """
    # Cek kolom yang ada di tabel users
    cols = db_session.execute(
        text("SELECT COLUMN_NAME as name FROM INFORMATION_SCHEMA.COLUMNS "
             "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users'")
    ).mappings().all()
    colset = {c['name'] for c in cols}

    if 'email' not in colset:
        return None, colset, None

    # SQL dump: tabel users memakai kolom: password
    if 'password' in colset:
        pw_col = 'password'
    elif 'password_hash' in colset:
        pw_col = 'password_hash'
    else:
        pw_col = None

    row = db_session.execute(
        text("SELECT * FROM users WHERE email = :email LIMIT 1"),
        {'email': email},
    ).mappings().first()

    return (row and dict(row) or None), colset, pw_col


def _get_admin_by_email(db_session, email: str):
    """Ambil admin dari tabel admins berdasarkan email"""
    row = db_session.execute(
        text("SELECT * FROM admins WHERE email = :email AND status = 'active' LIMIT 1"),
        {'email': email},
    ).mappings().first()
    return row and dict(row) or None


def generate_token(user_id, role, is_admin=False):
    """Generate JWT token"""
    payload = {
        'user_id': user_id,
        'role': role,
        'is_admin': is_admin,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(
            minutes=int(current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', datetime.timedelta(minutes=60)).total_seconds() // 60)
        ),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')


def token_required(f):
    """Decorator untuk proteksi route dengan JWT"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        if not token and 'token' in session:
            token = session.get('token')

        if not token:
            return jsonify({'ok': False, 'message': 'Token tidak ditemukan'}), 401

        try:
            data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            request.user_id = data.get('user_id')
            request.user_role = data.get('role')
            request.is_admin = data.get('is_admin', False)
        except jwt.ExpiredSignatureError:
            return jsonify({'ok': False, 'message': 'Token sudah expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'ok': False, 'message': 'Token tidak valid'}), 401

        return f(*args, **kwargs)
    return decorated


# ============================================
# REGISTER
# ============================================
@bp.route('/register', methods=['POST'])
def api_register():
    """API Register untuk User baru
    Body: {nama_lengkap, email, password, nomor_telepon, alamat(optional)}
    """
    payload = request.get_json(silent=True) or {}

    # Mapping field dari frontend ke database
    nama = (payload.get('nama_lengkap') or payload.get('nama') or '').strip()
    email = (payload.get('email') or '').strip().lower()
    telepon = (payload.get('nomor_telepon') or payload.get('telepon') or '').strip()
    password = payload.get('password') or ''
    alamat = (payload.get('alamat') or '').strip() or None

    if not all([nama, email, telepon, password]):
        return jsonify({'ok': False, 'message': 'Data tidak lengkap (nama, email, telepon, password wajib diisi)'}), 400

    if len(password) < 6:
        return jsonify({'ok': False, 'message': 'Password minimal 6 karakter'}), 400

    db_session = get_db()

    # Cek email sudah terdaftar di users
    user, colset, _ = _get_user_by_email(db_session, email)
    if user:
        return jsonify({'ok': False, 'message': 'Email sudah terdaftar sebagai user'}), 409

    # Cek email sudah terdaftar di admins
    admin = _get_admin_by_email(db_session, email)
    if admin:
        return jsonify({'ok': False, 'message': 'Email sudah terdaftar sebagai admin'}), 409

    if not colset:
        return jsonify({'ok': False, 'message': 'Tidak bisa membaca struktur tabel users'}), 500

    # Build insert data sesuai kolom yang ada
    actual = {}
    if 'email' in colset:
        actual['email'] = email
    if 'nama_lengkap' in colset:
        actual['nama_lengkap'] = nama
    elif 'nama' in colset:
        actual['nama'] = nama
    elif 'name' in colset:
        actual['name'] = nama

    if 'nomor_telepon' in colset:
        actual['nomor_telepon'] = telepon
    elif 'telepon' in colset:
        actual['telepon'] = telepon
    elif 'phone' in colset:
        actual['phone'] = telepon

    if 'alamat' in colset and alamat:
        actual['alamat'] = alamat

    # Password column
    pw_col = None
    if 'password' in colset:
        pw_col = 'password'
    elif 'password_hash' in colset:
        pw_col = 'password_hash'
    else:
        return jsonify({'ok': False, 'message': 'Kolom password tidak ditemukan di tabel users'}), 500

    actual[pw_col] = generate_password_hash(password)

    # Default values
    if 'status' in colset:
        actual['status'] = 'active'

    keys = ', '.join(actual.keys())
    placeholders = ', '.join([f':{k}' for k in actual.keys()])

    try:
        db_session.execute(
            text(f"INSERT INTO users ({keys}) VALUES ({placeholders})"),
            actual,
        )
        db_session.commit()

        return jsonify({
            'ok': True, 
            'message': 'Registrasi berhasil, silakan login',
            'email': email
        }), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({'ok': False, 'message': f'Terjadi kesalahan: {str(e)}'}), 500


# ============================================
# LOGIN
# ============================================
@bp.route('/login', methods=['POST'])
def api_login():
    """API Login untuk User dan Admin
    Body: {email, password}
    Response: {ok, message, role, token, user}
    """
    payload = request.get_json(silent=True) or {}
    email = (payload.get('email') or '').strip().lower()
    password = payload.get('password') or ''

    if not email or not password:
        return jsonify({'ok': False, 'message': 'Email dan password wajib diisi'}), 400

    db_session = get_db()

    # 1. Cek di tabel admins dulu (admin login)
    admin = _get_admin_by_email(db_session, email)
    if admin:
        # Cek password admin
        admin_pw = admin.get('password') or admin.get('password_hash', '')
        if check_password_hash(admin_pw, password):
            token = generate_token(admin['id'], admin.get('role', 'admin_instansi'), is_admin=True)
            session['user_id'] = admin['id']
            session['role'] = admin.get('role', 'admin_instansi')
            session['is_admin'] = True
            session['token'] = token

            return jsonify({
                'ok': True,
                'message': 'Login berhasil',
                'role': admin.get('role', 'admin_instansi'),
                'token': token,
                'user': {
                    'id': admin['id'],
                    'nama_lengkap': admin.get('nama_lengkap', ''),
                    'email': admin['email'],
                    'role': admin.get('role', 'admin_instansi'),
                    'instansi_nama': admin.get('instansi_nama', '')
                }
            }), 200

    # 2. Cek di tabel users (user login)
    user, colset, pw_col = _get_user_by_email(db_session, email)
    if user:
        if not pw_col or pw_col not in user:
            return jsonify({'ok': False, 'message': 'Kolom password tidak ditemukan'}), 500

        if check_password_hash(user[pw_col], password):
            token = generate_token(user['id'], 'user', is_admin=False)
            session['user_id'] = user['id']
            session['role'] = 'user'
            session['is_admin'] = False
            session['token'] = token

            return jsonify({
                'ok': True,
                'message': 'Login berhasil',
                'role': 'user',
                'token': token,
                'user': {
                    'id': user['id'],
                    'nama_lengkap': user.get('nama_lengkap') or user.get('nama', ''),
                    'email': user['email'],
                    'nomor_telepon': user.get('nomor_telepon') or user.get('telepon', '')
                }
            }), 200

    # 3. Tidak ditemukan
    return jsonify({'ok': False, 'message': 'Email atau password salah'}), 401


# ============================================
# LOGOUT
# ============================================
@bp.route('/logout', methods=['POST'])
def api_logout():
    """API Logout"""
    session.clear()
    return jsonify({'ok': True, 'message': 'Logout berhasil'}), 200


# ============================================
# FORGOT PASSWORD
# ============================================
@bp.route('/forgot-password', methods=['POST'])
def api_forgot_password():
    """API Forgot Password - Kirim kode verifikasi (demo/MVP)"""
    payload = request.get_json(silent=True) or {}
    email = (payload.get('email') or '').strip().lower()

    if not email:
        return jsonify({'ok': False, 'message': 'Email wajib diisi'}), 400

    db_session = get_db()

    # Cek email ada di users atau admins
    user, _, _ = _get_user_by_email(db_session, email)
    admin = _get_admin_by_email(db_session, email)

    if not user and not admin:
        return jsonify({'ok': False, 'message': 'Email tidak ditemukan'}), 404

    # MVP: Return success (dalam production, kirim email dengan kode OTP)
    return jsonify({
        'ok': True, 
        'message': 'Kode verifikasi telah dikirim ke email Anda (demo: gunakan kode 123456)',
        'demo_code': '123456'  # Hanya untuk demo!
    }), 200


# ============================================
# RESET PASSWORD
# ============================================
@bp.route('/reset-password', methods=['POST'])
def api_reset_password():
    """API Reset Password
    Body: {email, otp, new_password}
    """
    payload = request.get_json(silent=True) or {}
    email = (payload.get('email') or '').strip().lower()
    otp = (payload.get('otp') or '').strip()
    new_password = payload.get('new_password') or ''

    if not email or not otp or not new_password:
        return jsonify({'ok': False, 'message': 'Data tidak lengkap'}), 400

    if len(new_password) < 6:
        return jsonify({'ok': False, 'message': 'Password minimal 6 karakter'}), 400

    # MVP: Validasi OTP (dalam production, cek dari database/cache)
    # Demo: kode 123456 selalu valid
    if otp != '123456':
        return jsonify({'ok': False, 'message': 'Kode verifikasi salah'}), 400

    db_session = get_db()

    # Cek di users
    user, colset, pw_col = _get_user_by_email(db_session, email)
    if user and pw_col:
        try:
            db_session.execute(
                text(f"UPDATE users SET {pw_col} = :pw WHERE email = :email"),
                {'pw': generate_password_hash(new_password), 'email': email},
            )
            db_session.commit()
            return jsonify({'ok': True, 'message': 'Password berhasil direset'}), 200
        except Exception as e:
            db_session.rollback()
            return jsonify({'ok': False, 'message': str(e)}), 500

    # Cek di admins
    admin = _get_admin_by_email(db_session, email)
    if admin:
        pw_col = 'password' if 'password' in admin else 'password_hash'
        try:
            db_session.execute(
                text(f"UPDATE admins SET {pw_col} = :pw WHERE email = :email"),
                {'pw': generate_password_hash(new_password), 'email': email},
            )
            db_session.commit()
            return jsonify({'ok': True, 'message': 'Password berhasil direset'}), 200
        except Exception as e:
            db_session.rollback()
            return jsonify({'ok': False, 'message': str(e)}), 500

    return jsonify({'ok': False, 'message': 'Email tidak ditemukan'}), 404


# ============================================
# GET CURRENT USER
# ============================================
@bp.route('/me', methods=['GET'])
@token_required
def get_current_user():
    """Ambil data user/admin yang sedang login"""
    db_session = get_db()

    if request.is_admin:
        user = _get_admin_by_email(db_session, '')  # Perlu modifikasi
        # Simpler approach:
        row = db_session.execute(
            text("SELECT * FROM admins WHERE id = :id"),
            {'id': request.user_id}
        ).mappings().first()
    else:
        row = db_session.execute(
            text("SELECT * FROM users WHERE id = :id"),
            {'id': request.user_id}
        ).mappings().first()

    if not row:
        return jsonify({'ok': False, 'message': 'User tidak ditemukan'}), 404

    user = dict(row)
    return jsonify({
        'ok': True,
        'user': {
            'id': user['id'],
            'nama_lengkap': user.get('nama_lengkap') or user.get('nama', ''),
            'email': user['email']
        },
        'role': request.user_role,
        'is_admin': request.is_admin
    }), 200