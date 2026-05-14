from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from database.database import get_db

bp = Blueprint('auth_api_routes', __name__)


def _get_user_by_email(session, email: str):
    # Assume table: users
    cols = session.execute(
        "SELECT COLUMN_NAME as name FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users'"
    ).mappings().all()
    colset = {c['name'] for c in cols}

    if 'email' not in colset:
        return None, colset, None

    # SQL dump: tabel users memakai kolom: password (bukan password_hash)
    if 'password' in colset:
        pw_col = 'password'
    elif 'password_hash' in colset:
        pw_col = 'password_hash'

    else:
        pw_col = None



    row = session.execute(
        "SELECT * FROM users WHERE email = :email LIMIT 1",
        {'email': email},
    ).mappings().first()

    return row and dict(row) or None, colset, pw_col


@bp.route('/api/auth/register', methods=['POST'])
def api_register():
    payload = request.get_json(silent=True) or {}
    nama = (payload.get('nama') or '').strip()
    email = (payload.get('email') or '').strip().lower()
    telepon = (payload.get('telepon') or '').strip()
    password = payload.get('password') or ''

    if not all([nama, email, telepon, password]):
        return jsonify({'ok': False, 'message': 'Data tidak lengkap'}), 400

    if len(password) < 6:
        return jsonify({'ok': False, 'message': 'Password minimal 6 karakter'}), 400

    session = get_db()

    user, colset, _ = _get_user_by_email(session, email)
    if user:
        return jsonify({'ok': False, 'message': 'Email sudah terdaftar'}), 409

    if not colset:
        return jsonify({'ok': False, 'message': 'Tidak bisa membaca struktur tabel users'}), 500

    # Determine target columns that exist
    # We'll set whatever columns exist among common names.
    actual = {}
    if 'email' in colset:
        actual['email'] = email

    if 'nama' in colset:
        actual['nama'] = nama
    elif 'name' in colset:
        actual['name'] = nama

    # SQL dump: users.nomor_telepon
    if 'nomor_telepon' in colset:
        actual['nomor_telepon'] = telepon
    elif 'telepon' in colset:
        actual['telepon'] = telepon
    elif 'phone' in colset:
        actual['phone'] = telepon


    pw_col = None
    # SQL dump: tabel users memakai kolom password
    if 'password' in colset:
        pw_col = 'password'
    elif 'password_hash' in colset:
        pw_col = 'password_hash'

    else:
        return jsonify({'ok': False, 'message': 'Kolom password tidak ditemukan di tabel users'}), 500

    actual[pw_col] = generate_password_hash(password)

    keys = ', '.join(actual.keys())
    values = ', '.join([f':{k}' for k in actual.keys()])

    session.execute(
        f"INSERT INTO users ({keys}) VALUES ({values})",
        actual,
    )
    session.commit()

    return jsonify({'ok': True, 'message': 'Registrasi berhasil'}), 201


@bp.route('/api/auth/login', methods=['POST'])
def api_login():
    payload = request.get_json(silent=True) or {}
    email = (payload.get('email') or '').strip().lower()
    password = payload.get('password') or ''

    if not email or not password:
        return jsonify({'ok': False, 'message': 'Email dan password wajib diisi'}), 400

    session = get_db()
    user, colset, pw_col = _get_user_by_email(session, email)

    if not user:
        return jsonify({'ok': False, 'message': 'Akun tidak ditemukan'}), 404

    if not pw_col or pw_col not in user:
        return jsonify({'ok': False, 'message': 'Kolom password tidak ditemukan'}), 500

    if not check_password_hash(user[pw_col], password):
        return jsonify({'ok': False, 'message': 'Password salah'}), 401

    # Determine role for redirect
    # admins table: role enum('super_admin','admin_instansi')
    try:
        admins_cols = session.execute(
            "SELECT COLUMN_NAME as name FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'admins'"
        ).mappings().all()
        admins_colset = {c['name'] for c in admins_cols}
    except Exception:
        admins_colset = set()

    role = None
    if user and admins_colset:
        if 'email' in admins_colset:
            admin_row = session.execute(
                "SELECT * FROM admins WHERE email = :email LIMIT 1",
                {'email': email},
            ).mappings().first()
            if admin_row:
                admin = dict(admin_row)
                role = admin.get('role') or 'admin'

    # MVP: no JWT/session yet
    return jsonify({'ok': True, 'message': 'Login berhasil', 'email': email, 'role': role}), 200



@bp.route('/api/auth/forgot-password', methods=['POST'])
def api_forgot_password():
    # Demo MVP: validate email exists
    payload = request.get_json(silent=True) or {}
    email = (payload.get('email') or '').strip().lower()
    if not email:
        return jsonify({'ok': False, 'message': 'Email wajib diisi'}), 400

    session = get_db()
    user, _, _ = _get_user_by_email(session, email)
    if not user:
        return jsonify({'ok': False, 'message': 'Email tidak ditemukan'}), 404

    return jsonify({'ok': True, 'message': 'Kode verifikasi terkirim (demo)'}), 200


@bp.route('/api/auth/reset-password', methods=['POST'])
def api_reset_password():
    payload = request.get_json(silent=True) or {}
    email = (payload.get('email') or '').strip().lower()
    otp = (payload.get('otp') or '').strip()  # demo: not validated
    new_password = payload.get('new_password') or ''

    if not email or not otp or not new_password:
        return jsonify({'ok': False, 'message': 'Data tidak lengkap'}), 400
    if len(new_password) < 6:
        return jsonify({'ok': False, 'message': 'Password minimal 6 karakter'}), 400

    session = get_db()
    user, colset, pw_col = _get_user_by_email(session, email)
    if not user:
        return jsonify({'ok': False, 'message': 'Email tidak ditemukan'}), 404

    if not pw_col:
        return jsonify({'ok': False, 'message': 'Kolom password tidak ditemukan'}), 500

    session.execute(
        f"UPDATE users SET {pw_col} = :pw WHERE email = :email",
        {'pw': generate_password_hash(new_password), 'email': email},
    )
    session.commit()

    return jsonify({'ok': True, 'message': 'Password berhasil direset'}), 200

