# backend/routes/scan.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from models.booking import Booking
from models.admin import Admin

bp = Blueprint('scan_routes', __name__, url_prefix='/scan')

@bp.route('/<no_booking>')
def scan_qr(no_booking):
    """
    Endpoint untuk scan QR Code.
    Bisa diakses tanpa login (public) atau dengan login admin.
    """
    booking = Booking.get_by_booking_number(no_booking)
    
    if not booking:
        return render_template('scan/error.html', message='Booking tidak ditemukan'), 404
    
    # Cek apakah sudah selesai
    if booking.status == 'selesai':
        return render_template('scan/result.html', 
                             booking=booking, 
                             message='Booking ini sudah selesai!',
                             status='already_done')
    
    # Cek apakah bisa diselesaikan (hanya yang status menunggu/dikonfirmasi/proses)
    if booking.status not in ['menunggu', 'dikonfirmasi', 'proses']:
        return render_template('scan/result.html',
                             booking=booking,
                             message=f'Tidak dapat menyelesaikan booking dengan status "{booking.status}"',
                             status='invalid')
    
    # Jika admin yang scan (ada session admin)
    admin_id = session.get('admin_id')
    
    # Update status ke selesai
    updated = Booking.update_status(
        booking_id=booking.id,
        status_baru='selesai',
        admin_id=admin_id,
        keterangan='Status diubah ke SELESAI melalui QR Code Scan'
    )
    
    if updated:
        return render_template('scan/result.html',
                             booking=updated,
                             message='Booking berhasil diselesaikan!',
                             status='success',
                             is_admin=bool(admin_id))
    else:
        return render_template('scan/error.html', message='Gagal mengupdate status'), 500