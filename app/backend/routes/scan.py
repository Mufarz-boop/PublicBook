from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from database.database import get_db
from sqlalchemy import text
from utils.password import verify_password
import secrets
import hashlib
import socket
import os
from datetime import datetime, timedelta

bp = Blueprint('scan', __name__, url_prefix='/scan')


# ═══════════════════════════════════════════════════════════════════
# QR TOKEN HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════
def generate_qr_token(booking_id, no_booking):
    """Generate token unik untuk QR Code"""
    raw = f"{booking_id}:{no_booking}:{secrets.token_hex(16)}:{datetime.now().timestamp()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def save_qr_token(db, booking_id, token):
    """Simpan token ke database dengan expiry 24 jam"""
    expiry = datetime.now() + timedelta(hours=24)
    db.execute(text("""
        INSERT INTO qr_tokens (booking_id, token, created_at, expires_at, used)
        VALUES (:booking_id, :token, NOW(), :expires_at, FALSE)
        ON DUPLICATE KEY UPDATE
            token = VALUES(token),
            created_at = VALUES(created_at),
            expires_at = VALUES(expires_at),
            used = FALSE
    """), {
        'booking_id': booking_id,
        'token': token,
        'expires_at': expiry
    })
    db.commit()


def validate_qr_token(db, token):
    """Validasi token QR - return (booking_id, message)"""
    result = db.execute(text("""
        SELECT booking_id, used, expires_at 
        FROM qr_tokens 
        WHERE token = :token
    """), {'token': token}).mappings().first()
    
    if not result:
        return None, "Token tidak valid"
    
    if result['used']:
        return None, "Token sudah digunakan"
    
    if result['expires_at'] < datetime.now():
        return None, "Token sudah expired"
    
    return result['booking_id'], "Valid"


def mark_token_used(db, token):
    """Tandai token sudah digunakan"""
    db.execute(text("""
        UPDATE qr_tokens SET used = TRUE, used_at = NOW()
        WHERE token = :token
    """), {'token': token})
    db.commit()


# ═══════════════════════════════════════════════════════════════════
# ROUTE: Halaman Scan QR (Admin scan dari HP)
# ═══════════════════════════════════════════════════════════════════
@bp.route('/<token>')
def scan_qr_page(token):
    """Halaman scan QR - redirect ke login jika bukan admin"""
    user_id = session.get('user_id')
    if not user_id:
        flash('Silakan login sebagai Admin untuk scan QR', 'warning')
        return redirect(url_for('auth_routes.login_page', next=request.url))
    
    db = get_db()
    
    # Cek apakah user adalah admin
    admin = db.execute(text("""
        SELECT id FROM admins WHERE id = :id
    """), {'id': user_id}).mappings().first()
    
    if not admin:
        flash('Hanya Admin yang boleh scan QR Code', 'danger')
        return redirect(url_for('user_routes.dashboard'))
    
    # Validasi token
    booking_id, message = validate_qr_token(db, token)
    
    if booking_id is None:
        return render_template('scan/error.html', 
                             error_title='QR Tidak Valid',
                             error_message=message,
                             error_icon='fa-times-circle')
    
    # Ambil detail booking
    booking = db.execute(text("""
        SELECT b.*, u.nama_lengkap as nama_user, l.nama_layanan 
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        JOIN layanan l ON b.layanan_id = l.id
        WHERE b.id = :booking_id
    """), {'booking_id': booking_id}).mappings().first()
    
    if not booking:
        return render_template('scan/error.html',
                             error_title='Booking Tidak Ditemukan',
                             error_message='Data booking tidak ditemukan dalam sistem',
                             error_icon='fa-search')
    
    if booking['status'] == 'selesai':
        return render_template('scan/error.html',
                             error_title='Booking Sudah Selesai',
                             error_message='Booking ini sudah diselesaikan sebelumnya',
                             error_icon='fa-check-circle')
    
    return render_template('scan/result.html', 
                         booking=dict(booking), 
                         token=token)


# ═══════════════════════════════════════════════════════════════════
# ROUTE: API Konfirmasi Scan (Admin submit password)
# ═══════════════════════════════════════════════════════════════════
@bp.route('/api/confirm', methods=['POST'])
def confirm_scan():
    """Admin konfirmasi scan QR - ubah status jadi selesai"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Login required'}), 401
    
    db = get_db()
    
    # Cek admin - FIX: pakai 'password' bukan 'password_hash'
    admin = db.execute(text("SELECT id, password FROM admins WHERE id = :id"), 
                      {'id': user_id}).mappings().first()
    if not admin:
        return jsonify({'success': False, 'message': 'Hanya Admin yang boleh scan'}), 403
    
    data = request.get_json()
    token = data.get('token')
    admin_password = data.get('admin_password')
    
    if not token or not admin_password:
        return jsonify({'success': False, 'message': 'Token dan password diperlukan'}), 400
    
    # Verifikasi password admin
    if not verify_password(admin_password, admin['password']):
        return jsonify({'success': False, 'message': 'Password Admin salah'}), 403
    
    # Validasi token
    booking_id, message = validate_qr_token(db, token)
    if booking_id is None:
        return jsonify({'success': False, 'message': message}), 400
    
    # Update status booking jadi selesai + log ke riwayat_status
    db.execute(text("""
        UPDATE bookings 
        SET status = 'selesai', 
            completed_at = NOW(),
            completed_by = :admin_id
        WHERE id = :booking_id
    """), {'booking_id': booking_id, 'admin_id': user_id})
    
    # Insert ke riwayat_status (BARU)
    db.execute(text("""
        INSERT INTO riwayat_status 
        (booking_id, status_sebelum, status_baru, admin_id, keterangan, waktu_perubahan)
        VALUES 
        (:booking_id, 'menunggu', 'selesai', :admin_id, 'Status diubah ke SELESAI melalui QR Code Scan', NOW())
    """), {'booking_id': booking_id, 'admin_id': user_id})
    
    # Tandai token sudah digunakan
    mark_token_used(db, token)
    
    db.commit()
    
    return jsonify({
        'success': True,
        'message': 'Booking berhasil diselesaikan',
        'booking_id': booking_id
    })


# ═══════════════════════════════════════════════════════════════════
# ROUTE: API Cek Status Booking (untuk polling user)
# ═══════════════════════════════════════════════════════════════════
@bp.route('/api/check-status/<int:booking_id>')
def check_booking_status(booking_id):
    """Cek status booking terbaru (untuk polling dari user)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Login required'}), 401
    
    db = get_db()
    
    booking = db.execute(text("""
        SELECT id, status, completed_at, completed_by 
        FROM bookings 
        WHERE id = :booking_id AND user_id = :user_id
    """), {'booking_id': booking_id, 'user_id': user_id}).mappings().first()
    
    if not booking:
        return jsonify({'success': False, 'message': 'Booking tidak ditemukan'}), 404
    
    # Ambil nama admin yang menyelesaikan
    admin_name = None
    if booking['completed_by']:
        admin = db.execute(text("""
            SELECT nama_lengkap FROM admins WHERE id = :id
        """), {'id': booking['completed_by']}).mappings().first()
        if admin:
            admin_name = admin['nama_lengkap']
    
    return jsonify({
        'success': True,
        'status': booking['status'],
        'completed_at': booking['completed_at'].isoformat() if booking['completed_at'] else None,
        'completed_by': admin_name,
        'is_selesai': booking['status'] == 'selesai'
    })


# ═══════════════════════════════════════════════════════════════════
# ROUTE: API Get QR untuk booking (untuk user)
# ═══════════════════════════════════════════════════════════════════
@bp.route('/api/booking-qr/<int:booking_id>')
def get_booking_qr(booking_id):
    """Ambil QR Code untuk booking (generate jika belum ada)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Login required'}), 401
    
    db = get_db()
    
    # Cek booking milik user
    booking = db.execute(text("""
        SELECT id, no_booking, status FROM bookings 
        WHERE id = :booking_id AND user_id = :user_id
    """), {'booking_id': booking_id, 'user_id': user_id}).mappings().first()
    
    if not booking:
        return jsonify({'success': False, 'message': 'Booking tidak ditemukan'}), 404
    
    if booking['status'] == 'selesai':
        return jsonify({'success': False, 'message': 'Booking sudah selesai'}), 400
    
    # Cek token yang sudah ada dan masih valid
    existing = db.execute(text("""
        SELECT token, expires_at FROM qr_tokens 
        WHERE booking_id = :booking_id AND used = FALSE AND expires_at > NOW()
        ORDER BY created_at DESC LIMIT 1
    """), {'booking_id': booking_id}).mappings().first()
    
    if existing:
        token = existing['token']
    else:
        # Generate token baru
        token = generate_qr_token(booking_id, booking['no_booking'])
        save_qr_token(db, booking_id, token)
    
    # Generate QR URL dengan IP lokal
    manual_ip = os.getenv('PUBLICBOOK_IP')
    if manual_ip:
        local_ip = manual_ip
    else:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(2)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except:
            local_ip = '127.0.0.1'
    
    from flask import current_app
    port = current_app.config.get('PORT', 5000)
    qr_url = f"http://{local_ip}:{port}/scan/{token}"
    
    return jsonify({
        'success': True,
        'qr_url': qr_url,
        'qr_image': f"https://api.qrserver.com/v1/create-qr-code/?size=280x280&data={qr_url}&color=333333&bgcolor=ffffff",
        'token': token,
        'expires_at': (datetime.now() + timedelta(hours=24)).isoformat()
    })