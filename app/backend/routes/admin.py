# backend/routes/admin.py
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from models.user import User
from models.booking import Booking
from models.services import Service
from models.admin import Admin
from utils.password import verify_password, hash_password
from database.database import get_db
from sqlalchemy import text
from datetime import datetime

bp = Blueprint('admin_routes', __name__, url_prefix='/admin')

def admin_required(f):
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            flash('Silakan login terlebih dahulu', 'warning')
            return redirect(url_for('auth_routes.login_page'))
        if not session.get('is_admin'):
            flash('Akses ditolak', 'danger')
            return redirect(url_for('user_routes.dashboard'))
        if session.get('role') not in ['super_admin', 'admin_instansi']:
            flash('Role tidak valid', 'danger')
            return redirect(url_for('auth_routes.login_page'))
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

@bp.route('/dashboard')
@admin_required
def dashboard():
    stats = {
        'booking_today': Booking.count_today(),
        'booking_month': Booking.count_this_month(),
        'total_users': User.count_all(),
        'active_services': Service.count_active()
    }
    recent_bookings = Booking.get_all(limit=10)
    admin = Admin.get_by_id(session.get('user_id'))
    
    return render_template('admin/dashboard.html', 
                         stats=stats, 
                         bookings=recent_bookings,
                         admin=admin)

@bp.route('/layanan')
@admin_required
def layanan():
    services = Service.get_all()
    admin = Admin.get_by_id(session.get('user_id'))
    return render_template('admin/layanan.html', services=services, admin=admin)

@bp.route('/layanan/tambah', methods=['POST'])
@admin_required
def tambah_layanan():
    nama_layanan = request.form.get('nama_layanan', '').strip()
    instansi = request.form.get('instansi', '').strip()
    jam_operasional = request.form.get('jam_operasional', '').strip()
    deskripsi = request.form.get('deskripsi', '').strip()
    status = request.form.get('status', 'active')
    
    if not nama_layanan or not instansi:
        flash('Nama layanan dan instansi wajib diisi', 'danger')
        return redirect(url_for('admin_routes.layanan'))
    
    db = get_db()
    try:
        db.execute(
            text("""
                INSERT INTO layanan (nama_layanan, instansi, jam_operasional, deskripsi, status, created_at)
                VALUES (:nama, :instansi, :jam, :deskripsi, :status, NOW())
            """),
            {
                'nama': nama_layanan,
                'instansi': instansi,
                'jam': jam_operasional or None,
                'deskripsi': deskripsi or None,
                'status': status
            }
        )
        db.commit()
        flash('Layanan berhasil ditambahkan', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Gagal menambahkan layanan: {str(e)}', 'danger')
    
    return redirect(url_for('admin_routes.layanan'))

@bp.route('/layanan/edit', methods=['POST'])
@admin_required
def edit_layanan():
    service_id = request.form.get('service_id')
    nama_layanan = request.form.get('nama_layanan', '').strip()
    instansi = request.form.get('instansi', '').strip()
    jam_operasional = request.form.get('jam_operasional', '').strip()
    deskripsi = request.form.get('deskripsi', '').strip()
    status = request.form.get('status', 'active')
    
    if not service_id or not nama_layanan or not instansi:
        flash('Data tidak lengkap', 'danger')
        return redirect(url_for('admin_routes.layanan'))
    
    db = get_db()
    try:
        db.execute(
            text("""
                UPDATE layanan 
                SET nama_layanan = :nama, instansi = :instansi, jam_operasional = :jam,
                    deskripsi = :deskripsi, status = :status
                WHERE id = :id
            """),
            {
                'nama': nama_layanan,
                'instansi': instansi,
                'jam': jam_operasional or None,
                'deskripsi': deskripsi or None,
                'status': status,
                'id': service_id
            }
        )
        db.commit()
        flash('Layanan berhasil diperbarui', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Gagal memperbarui layanan: {str(e)}', 'danger')
    
    return redirect(url_for('admin_routes.layanan'))

@bp.route('/layanan/hapus', methods=['POST'])
@admin_required
def hapus_layanan():
    service_id = request.form.get('service_id')
    
    if not service_id:
        flash('ID layanan tidak valid', 'danger')
        return redirect(url_for('admin_routes.layanan'))
    
    db = get_db()
    try:
        db.execute(text("DELETE FROM layanan WHERE id = :id"), {'id': service_id})
        db.commit()
        flash('Layanan berhasil dihapus', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Gagal menghapus layanan: {str(e)}', 'danger')
    
    return redirect(url_for('admin_routes.layanan'))

@bp.route('/layanan/toggle', methods=['POST'])
@admin_required
def toggle_layanan():
    service_id = request.form.get('service_id')
    
    if not service_id:
        return jsonify({'success': False, 'message': 'ID tidak valid'})
    
    db = get_db()
    try:
        result = db.execute(
            text("SELECT status FROM layanan WHERE id = :id"),
            {'id': service_id}
        ).mappings().first()
        
        if not result:
            return jsonify({'success': False, 'message': 'Layanan tidak ditemukan'})
        
        current_status = result['status']
        new_status = 'inactive' if current_status == 'active' else 'active'
        
        db.execute(
            text("UPDATE layanan SET status = :status WHERE id = :id"),
            {'status': new_status, 'id': service_id}
        )
        db.commit()
        
        status_text = 'diaktifkan' if new_status == 'active' else 'dinonaktifkan'
        return jsonify({'success': True, 'message': f'Layanan berhasil {status_text}'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/booking-list')
@admin_required
def booking_list():
    bookings = Booking.get_all()
    admin = Admin.get_by_id(session.get('user_id'))
    return render_template('admin/booking-list.html', bookings=bookings, admin=admin)

@bp.route('/pengguna')
@admin_required
def pengguna():
    users = User.get_all()
    admin = Admin.get_by_id(session.get('user_id'))
    return render_template('admin/pengguna.html', users=users, admin=admin)

@bp.route('/pengguna/tambah', methods=['POST'])
@admin_required
def tambah_user():
    nama_lengkap = request.form.get('nama_lengkap', '').strip()
    email = request.form.get('email', '').strip()
    nomor_telepon = request.form.get('nomor_telepon', '').strip()
    password = request.form.get('password', '')
    status = request.form.get('status', 'active')
    
    if not nama_lengkap or not email or not password:
        flash('Nama lengkap, email, dan password wajib diisi', 'danger')
        return redirect(url_for('admin_routes.pengguna'))
    
    if len(password) < 6:
        flash('Password minimal 6 karakter', 'danger')
        return redirect(url_for('admin_routes.pengguna'))
    
    db = get_db()
    existing = db.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {'email': email}
    ).mappings().first()
    
    if existing:
        flash('Email sudah terdaftar', 'danger')
        return redirect(url_for('admin_routes.pengguna'))
    
    try:
        db.execute(
            text("""
                INSERT INTO users (nama_lengkap, email, nomor_telepon, password, status, created_at)
                VALUES (:nama, :email, :telp, :pw, :status, NOW())
            """),
            {
                'nama': nama_lengkap,
                'email': email,
                'telp': nomor_telepon or None,
                'pw': hash_password(password),
                'status': status
            }
        )
        db.commit()
        flash('User berhasil ditambahkan', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Gagal menambahkan user: {str(e)}', 'danger')
    
    return redirect(url_for('admin_routes.pengguna'))

@bp.route('/pengguna/edit', methods=['POST'])
@admin_required
def edit_user():
    user_id = request.form.get('user_id')
    nama_lengkap = request.form.get('nama_lengkap', '').strip()
    email = request.form.get('email', '').strip()
    nomor_telepon = request.form.get('nomor_telepon', '').strip()
    password = request.form.get('password', '')
    status = request.form.get('status', 'active')
    
    if not user_id or not nama_lengkap or not email:
        flash('Data tidak lengkap', 'danger')
        return redirect(url_for('admin_routes.pengguna'))
    
    db = get_db()
    
    existing = db.execute(
        text("SELECT id FROM users WHERE email = :email AND id != :id"),
        {'email': email, 'id': user_id}
    ).mappings().first()
    
    if existing:
        flash('Email sudah digunakan user lain', 'danger')
        return redirect(url_for('admin_routes.pengguna'))
    
    try:
        if password:
            if len(password) < 6:
                flash('Password minimal 6 karakter', 'danger')
                return redirect(url_for('admin_routes.pengguna'))
            db.execute(
                text("""
                    UPDATE users 
                    SET nama_lengkap = :nama, email = :email, nomor_telepon = :telp, 
                        password = :pw, status = :status
                    WHERE id = :id
                """),
                {
                    'nama': nama_lengkap,
                    'email': email,
                    'telp': nomor_telepon or None,
                    'pw': hash_password(password),
                    'status': status,
                    'id': user_id
                }
            )
        else:
            db.execute(
                text("""
                    UPDATE users 
                    SET nama_lengkap = :nama, email = :email, nomor_telepon = :telp, 
                        status = :status
                    WHERE id = :id
                """),
                {
                    'nama': nama_lengkap,
                    'email': email,
                    'telp': nomor_telepon or None,
                    'status': status,
                    'id': user_id
                }
            )
        db.commit()
        flash('User berhasil diperbarui', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Gagal memperbarui user: {str(e)}', 'danger')
    
    return redirect(url_for('admin_routes.pengguna'))

@bp.route('/pengguna/hapus', methods=['POST'])
@admin_required
def hapus_user():
    user_id = request.form.get('user_id')
    
    if not user_id:
        flash('ID user tidak valid', 'danger')
        return redirect(url_for('admin_routes.pengguna'))
    
    db = get_db()
    try:
        db.execute(text("DELETE FROM users WHERE id = :id"), {'id': user_id})
        db.commit()
        flash('User berhasil dihapus', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Gagal menghapus user: {str(e)}', 'danger')
    
    return redirect(url_for('admin_routes.pengguna'))

@bp.route('/security')
@admin_required
def security():
    admin = Admin.get_by_id(session.get('user_id'))
    
    # Stats untuk sidebar profile card
    stats = {
        'booking_total': Booking.count_all(),
        'service_total': Service.count_active()
    }
    
    # ═══════════════════════════════════════════════════════════════
    # RIWAYAT LOGIN - PAGINATION
    # ═══════════════════════════════════════════════════════════════
    db = get_db()
    
    # Ambil parameter page dari URL (default halaman 1)
    try:
        page = int(request.args.get('page', 1))
        if page < 1:
            page = 1
    except ValueError:
        page = 1
    
    per_page = 5 # Jumlah item per halaman
    offset = (page - 1) * per_page
    
    # Hitung total records
    total_result = db.execute(
        text("SELECT COUNT(*) as total FROM login_history WHERE admin_id = :admin_id"),
        {'admin_id': session.get('user_id')}
    ).mappings().first()
    total_records = total_result['total'] if total_result else 0
    
    # Hitung total halaman
    total_pages = (total_records + per_page - 1) // per_page
    if total_pages < 1:
        total_pages = 1
    
    # Ambil data untuk halaman ini
    login_history = db.execute(
        text("""
            SELECT 
                id,
                ip_address,
                device_info,
                location,
                status,
                created_at as waktu
            FROM login_history 
            WHERE admin_id = :admin_id 
            ORDER BY created_at DESC 
            LIMIT :limit OFFSET :offset
        """),
        {
            'admin_id': session.get('user_id'),
            'limit': per_page,
            'offset': offset
        }
    ).mappings().all()
    
    # Format data untuk template
    history_list = []
    for row in login_history:
        history_list.append({
            'waktu': row['waktu'],
            'perangkat': row['device_info'] or 'Unknown Device',
            'ip': row['ip_address'] or '-',
            'lokasi': row['location'] or '-',
            'status': row['status']
        })
    
    # Data pagination untuk template
    pagination = {
        'page': page,
        'per_page': per_page,
        'total_records': total_records,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_page': page - 1,
        'next_page': page + 1,
        'pages': []
    }
    
    # Generate list halaman yang ditampilkan (max 5 tombol)
    start_page = max(1, page - 2)
    end_page = min(total_pages, page + 2)
    
    if end_page - start_page < 4 and total_pages > 4:
        if start_page == 1:
            end_page = min(5, total_pages)
        else:
            start_page = max(1, end_page - 4)
    
    pagination['pages'] = list(range(start_page, end_page + 1))
    
    # ═══════════════════════════════════════════════════════════════
    # JIKA AJAX REQUEST, RETURN JSON SAJA
    # ═══════════════════════════════════════════════════════════════
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'login_history': history_list,
            'pagination': pagination
        })
    
    return render_template('admin/security.html', 
                         admin=admin, 
                         stats=stats,
                         login_history=history_list,
                         pagination=pagination)

@bp.route('/security/ubah-password', methods=['POST'])
@admin_required
def ubah_password_post():
    admin_id = session.get('user_id')
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    if not all([current_password, new_password, confirm_password]):
        flash('Semua field wajib diisi', 'danger')
        return redirect(url_for('admin_routes.security'))
    
    if len(new_password) < 6:
        flash('Password baru minimal 6 karakter', 'danger')
        return redirect(url_for('admin_routes.security'))
    
    if new_password != confirm_password:
        flash('Password baru dan konfirmasi tidak cocok', 'danger')
        return redirect(url_for('admin_routes.security'))
    
    db = get_db()
    admin = db.execute(
        text("SELECT * FROM admins WHERE id = :id"),
        {'id': admin_id}
    ).mappings().first()
    
    if not admin:
        flash('Data admin tidak ditemukan', 'danger')
        return redirect(url_for('admin_routes.security'))
    
    admin_dict = dict(admin)
    stored_password = admin_dict.get('password') or admin_dict.get('password_hash', '')
    
    if not verify_password(current_password, stored_password):
        flash('Password saat ini salah', 'danger')
        return redirect(url_for('admin_routes.security'))
    
    pw_col = 'password' if 'password' in admin_dict else 'password_hash'
    try:
        db.execute(
            text(f"UPDATE admins SET {pw_col} = :pw WHERE id = :id"),
            {'pw': hash_password(new_password), 'id': admin_id}
        )
        db.commit()
        flash('Password berhasil diubah', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Gagal mengubah password: {str(e)}', 'danger')
    
    return redirect(url_for('admin_routes.security'))

# ═══════════════════════════════════════════════════════════════════
# ROUTE: HALAMAN SCANNER QR (ADMIN)
# ═══════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════
# ROUTE: HALAMAN SCANNER QR (ADMIN)
# ═══════════════════════════════════════════════════════════════════
@bp.route('/scan')
@admin_required
def scan_page():
    """Halaman scanner QR code untuk admin"""
    admin = Admin.get_by_id(session.get('user_id'))
    return render_template('admin/scan.html', admin=admin)

@bp.route('/profil')
@admin_required
def profil():
    admin = Admin.get_by_id(session.get('user_id'))
    return render_template('admin/profil.html', admin=admin)

@bp.route('/ubah-password')
@admin_required
def ubah_password():
    return redirect(url_for('admin_routes.security'))