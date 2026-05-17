# backend/routes/auth.py
from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from database.database import get_db
from sqlalchemy import text
from utils.password import verify_password, hash_password
from utils.login_history import catat_login_history

bp = Blueprint('auth_routes', __name__)

# ═══════════════════════════════════════════════════════════════════
# HALAMAN LOGIN (GET)
# ═══════════════════════════════════════════════════════════════════
@bp.route('/login')
def login_page():
    """Tampilkan halaman login"""
    if session.get('user_id'):
        # Sudah login, redirect ke dashboard sesuai role
        if session.get('is_admin'):
            return redirect(url_for('admin_routes.dashboard'))
        return redirect(url_for('user_routes.dashboard'))
    return render_template('auth/login.html')

# ═══════════════════════════════════════════════════════════════════
# PROSES LOGIN (POST)
# ═══════════════════════════════════════════════════════════════════
@bp.route('/login', methods=['POST'])
def login_post():
    """Proses autentikasi login"""
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    
    # Validasi input tidak kosong
    if not email or not password:
        flash('Email dan password wajib diisi', 'danger')
        return redirect(url_for('auth_routes.login_page'))
    
    db = get_db()
    
    # ═══════════════════════════════════════════════════════════════
    # CEK DI TABEL ADMINS DULU
    # ═══════════════════════════════════════════════════════════════
    admin = db.execute(
        text("SELECT * FROM admins WHERE email = :email AND status = 'active'"),
        {'email': email}
    ).mappings().first()
    
    if admin:
        admin_dict = dict(admin)
        stored_password = admin_dict.get('password') or admin_dict.get('password_hash', '')
        
        if verify_password(password, stored_password):
            # ═══════════════════════════════════════════════════════
            # LOGIN ADMIN BERHASIL
            # ═══════════════════════════════════════════════════════
            session['user_id'] = admin_dict['id']
            session['is_admin'] = True
            session['role'] = admin_dict.get('role', 'admin_instansi')
            session['nama_lengkap'] = admin_dict.get('nama_lengkap', 'Admin')
            
            # Catat riwayat login
            catat_login_history(admin_id=admin_dict['id'], status='success')
            
            flash(f'Selamat datang, {session["nama_lengkap"]}!', 'success')
            return redirect(url_for('admin_routes.dashboard'))
        else:
            # Password salah - catat login gagal
            catat_login_history(admin_id=admin_dict['id'], status='failed')
            flash('Email atau password salah', 'danger')
            return redirect(url_for('auth_routes.login_page'))
    
    # ═══════════════════════════════════════════════════════════════
    # CEK DI TABEL USERS
    # ═══════════════════════════════════════════════════════════════
    user = db.execute(
        text("SELECT * FROM users WHERE email = :email AND status = 'active'"),
        {'email': email}
    ).mappings().first()
    
    if user:
        user_dict = dict(user)
        stored_password = user_dict.get('password') or user_dict.get('password_hash', '')
        
        if verify_password(password, stored_password):
            # ═══════════════════════════════════════════════════════
            # LOGIN USER BERHASIL
            # ═══════════════════════════════════════════════════════
            session['user_id'] = user_dict['id']
            session['is_admin'] = False
            session['role'] = 'user'
            session['nama_lengkap'] = user_dict.get('nama_lengkap', 'User')
            
            # Catat riwayat login
            catat_login_history(user_id=user_dict['id'], status='success')
            
            flash(f'Selamat datang, {session["nama_lengkap"]}!', 'success')
            return redirect(url_for('user_routes.dashboard'))
        else:
            # Password salah - catat login gagal
            catat_login_history(user_id=user_dict['id'], status='failed')
            flash('Email atau password salah', 'danger')
            return redirect(url_for('auth_routes.login_page'))
    
    # ═══════════════════════════════════════════════════════════════
    # EMAIL TIDAK DITEMUKAN
    # ═══════════════════════════════════════════════════════════════
    flash('Email atau password salah', 'danger')
    return redirect(url_for('auth_routes.login_page'))

# ═══════════════════════════════════════════════════════════════════
# HALAMAN REGISTER (GET)
# ═══════════════════════════════════════════════════════════════════
@bp.route('/register')
def register_page():
    """Tampilkan halaman register"""
    if session.get('user_id'):
        return redirect(url_for('auth_routes.login_page'))
    return render_template('auth/register.html')

# ═══════════════════════════════════════════════════════════════════
# PROSES REGISTER (POST)
# ═══════════════════════════════════════════════════════════════════
@bp.route('/register', methods=['POST'])
def register_post():
    """Proses registrasi user baru"""
    nama_lengkap = request.form.get('nama_lengkap', '').strip()
    email = request.form.get('email', '').strip()
    nomor_telepon = request.form.get('nomor_telepon', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    # Validasi
    if not all([nama_lengkap, email, password, confirm_password]):
        flash('Semua field wajib diisi', 'danger')
        return redirect(url_for('auth_routes.register_page'))
    
    if len(password) < 6:
        flash('Password minimal 6 karakter', 'danger')
        return redirect(url_for('auth_routes.register_page'))
    
    if password != confirm_password:
        flash('Password dan konfirmasi tidak cocok', 'danger')
        return redirect(url_for('auth_routes.register_page'))
    
    db = get_db()
    
    # Cek email sudah terdaftar
    existing = db.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {'email': email}
    ).mappings().first()
    
    if existing:
        flash('Email sudah terdaftar', 'danger')
        return redirect(url_for('auth_routes.register_page'))
    
    # Cek email di admins juga
    existing_admin = db.execute(
        text("SELECT id FROM admins WHERE email = :email"),
        {'email': email}
    ).mappings().first()
    
    if existing_admin:
        flash('Email sudah terdaftar sebagai admin', 'danger')
        return redirect(url_for('auth_routes.register_page'))
    
    # Insert user baru
    try:
        db.execute(
            text("""
                INSERT INTO users (nama_lengkap, email, nomor_telepon, password, status, created_at)
                VALUES (:nama, :email, :telp, :pw, 'active', NOW())
            """),
            {
                'nama': nama_lengkap,
                'email': email,
                'telp': nomor_telepon or None,
                'pw': hash_password(password)
            }
        )
        db.commit()
        flash('Registrasi berhasil! Silakan login', 'success')
        return redirect(url_for('auth_routes.login_page'))
    except Exception as e:
        db.rollback()
        flash(f'Gagal registrasi: {str(e)}', 'danger')
        return redirect(url_for('auth_routes.register_page'))

# ═══════════════════════════════════════════════════════════════════
# FORGOT PASSWORD
# ═══════════════════════════════════════════════════════════════════
@bp.route('/forgot-password')
def forgot_password():
    """Tampilkan halaman lupa password"""
    return render_template('auth/forgot_password.html')

# ═══════════════════════════════════════════════════════════════════
# LOGOUT
# ═══════════════════════════════════════════════════════════════════
@bp.route('/logout')
def logout():
    """Logout user/admin — clear session dan redirect ke index page"""
    session.clear()
    flash('Anda telah logout', 'info')
    return redirect(url_for('static_routes.index'))