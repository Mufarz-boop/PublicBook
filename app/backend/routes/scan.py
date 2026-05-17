# backend/routes/scan.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from models.booking import Booking
from models.admin import Admin
from database.database import get_db
from sqlalchemy import text
from datetime import datetime

bp = Blueprint('scan_routes', __name__, url_prefix='/scan')

# ═══════════════════════════════════════════════════════════════════
# DECORATOR: Hanya Admin yang Boleh Akses
# ═══════════════════════════════════════════════════════════════════
def scan_admin_required(f):
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            session['next_scan_url'] = request.url
            flash('Silakan login sebagai admin untuk melanjutkan scan', 'warning')
            return redirect(url_for('auth_routes.login_page'))
        
        if not session.get('is_admin'):
            flash('Akses ditolak. Hanya admin yang dapat scan QR Code.', 'danger')
            return redirect(url_for('user_routes.dashboard'))
        
        if session.get('role') not in ['super_admin', 'admin_instansi']:
            flash('Role tidak memiliki izin scan QR Code', 'danger')
            return redirect(url_for('auth_routes.login_page'))
        
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

# ═══════════════════════════════════════════════════════════════════
# ROUTE: API Scan QR (POST) - Untuk AJAX dari halaman scanner
# ═══════════════════════════════════════════════════════════════════
@bp.route('/api/scan', methods=['POST'])
@scan_admin_required
def api_scan_qr():
    """API endpoint untuk scan QR via AJAX"""
    data = request.get_json()
    no_booking = data.get('no_booking', '').strip().upper()
    
    if not no_booking:
        return jsonify({
            'success': False,
            'status': 'invalid',
            'message': 'Nomor booking tidak valid',
            'booking': None
        })
    
    booking = Booking.get_by_booking_number(no_booking)
    
    if not booking:
        return jsonify({
            'success': False,
            'status': 'not_found',
            'message': f'Booking "{no_booking}" tidak ditemukan',
            'booking': None
        })
    
    # Cek apakah sudah selesai
    if booking.status == 'selesai':
        return jsonify({
            'success': False,
            'status': 'already_done',
            'message': 'Booking ini sudah selesai!',
            'booking': {
                'no_booking': booking.no_booking,
                'nama_layanan': booking.nama_layanan,
                'nama_pendaftar': booking.nama_pendaftar,
                'status': booking.status,
                'tanggal_booking': str(booking.tanggal_booking),
                'nomor_antrian': booking.nomor_antrian
            }
        })
    
    # Cek apakah bisa diselesaikan
    if booking.status not in ['menunggu', 'dikonfirmasi', 'proses']:
        return jsonify({
            'success': False,
            'status': 'cannot_process',
            'message': f'Tidak dapat menyelesaikan booking dengan status "{booking.status}"',
            'booking': {
                'no_booking': booking.no_booking,
                'nama_layanan': booking.nama_layanan,
                'nama_pendaftar': booking.nama_pendaftar,
                'status': booking.status,
                'tanggal_booking': str(booking.tanggal_booking),
                'nomor_antrian': booking.nomor_antrian
            }
        })
    
    # Update status ke selesai
    admin_id = session.get('user_id')
    updated = Booking.update_status(
        booking_id=booking.id,
        status_baru='selesai',
        admin_id=admin_id,
        keterangan=f'Status diubah ke SELESAI melalui QR Scan oleh Admin #{admin_id}'
    )
    
    if updated:
        return jsonify({
            'success': True,
            'status': 'success',
            'message': 'Booking berhasil diselesaikan!',
            'booking': {
                'no_booking': updated.no_booking,
                'nama_layanan': updated.nama_layanan,
                'nama_pendaftar': updated.nama_pendaftar,
                'status': updated.status,
                'tanggal_booking': str(updated.tanggal_booking),
                'nomor_antrian': updated.nomor_antrian,
                'updated_at': str(updated.updated_at)
            }
        })
    else:
        return jsonify({
            'success': False,
            'status': 'error',
            'message': 'Gagal mengupdate status booking',
            'booking': None
        })

# ═══════════════════════════════════════════════════════════════════
# ROUTE: Scan QR Langsung via URL (untuk scan dari HP/external)
# ═══════════════════════════════════════════════════════════════════
@bp.route('/<no_booking>')
@scan_admin_required
def scan_qr(no_booking):
    """
    Endpoint untuk scan QR Code via URL langsung.
    Hanya bisa diakses oleh admin yang sudah login.
    """
    booking = Booking.get_by_booking_number(no_booking)
    
    if not booking:
        return render_template('scan/result.html', 
                             message='Booking tidak ditemukan',
                             status='not_found',
                             is_admin=True), 404
    
    if booking.status == 'selesai':
        return render_template('scan/result.html', 
                             booking=booking, 
                             message='Booking ini sudah selesai!',
                             status='already_done',
                             is_admin=True)
    
    if booking.status not in ['menunggu', 'dikonfirmasi', 'proses']:
        return render_template('scan/result.html',
                             booking=booking,
                             message=f'Tidak dapat menyelesaikan booking dengan status "{booking.status}"',
                             status='cannot_process',
                             is_admin=True)
    
    admin_id = session.get('user_id')
    updated = Booking.update_status(
        booking_id=booking.id,
        status_baru='selesai',
        admin_id=admin_id,
        keterangan='Status diubah ke SELESAI melalui QR Code Scan oleh Admin'
    )
    
    if updated:
        return render_template('scan/result.html',
                             booking=updated,
                             message='Booking berhasil diselesaikan!',
                             status='success',
                             is_admin=True)
    else:
        return render_template('scan/result.html', 
                             message='Gagal mengupdate status booking',
                             status='error',
                             is_admin=True), 500