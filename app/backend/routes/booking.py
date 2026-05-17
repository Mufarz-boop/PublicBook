
# TAMBAHKAN INI di bagian atas file booking.py yang sudah ada:
# (jika belum ada)

from flask import Blueprint, request, jsonify, session
from database.database import get_db
from sqlalchemy import text

bp = Blueprint('booking', __name__, url_prefix='/booking')

# ... (route-route yang sudah ada di booking.py) ...


# ═══════════════════════════════════════════════════════════════════
# TAMBAHKAN ENDPOINT INI di akhir file booking.py:
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
        # Import fungsi generate token dari scan.py
        from routes.scan import generate_qr_token, save_qr_token
        token = generate_qr_token(booking_id, booking['no_booking'])
        save_qr_token(db, booking_id, token)

    # Generate QR URL
    import socket
    import os
    from flask import current_app

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

    port = current_app.config.get('PORT', 5000)
    qr_url = f"http://{local_ip}:{port}/scan/{token}"

    from datetime import datetime, timedelta

    return jsonify({
        'success': True,
        'qr_url': qr_url,
        'qr_image': f"https://api.qrserver.com/v1/create-qr-code/?size=280x280&data={qr_url}&color=333333&bgcolor=ffffff",
        'token': token,
        'expires_at': (datetime.now() + timedelta(hours=24)).isoformat()
    })