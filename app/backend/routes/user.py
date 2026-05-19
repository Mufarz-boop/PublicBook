# backend/routes/user.py
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, send_file
from datetime import datetime
from models.user import User
from models.booking import Booking
from models.services import Service
from database.database import get_db
from sqlalchemy import text
import io
import os
from PIL import Image, ImageDraw, ImageFont
import qrcode

bp = Blueprint('user_routes', __name__, url_prefix='/user')


def user_required(f):
    """Decorator untuk cek apakah user sudah login dan bukan admin"""
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            flash('Silakan login terlebih dahulu', 'warning')
            return redirect(url_for('auth_routes.login_page'))
        if session.get('is_admin'):
            flash('Halaman ini khusus pengguna', 'danger')
            return redirect(url_for('admin_routes.dashboard'))
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated


# ═══════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════

@bp.route('/dashboard')
@user_required
def dashboard():
    user_id = session.get('user_id')
    user = User.get_by_id(user_id)
    
    # Ambil 5 booking terakhir
    bookings = Booking.get_by_user_id(user_id, limit=5)
    
    # Statistik
    stats = {
        'total_booking': Booking.count_by_user(user_id),
        'menunggu': Booking.count_by_user(user_id, status='menunggu'),
        'dikonfirmasi': Booking.count_by_user(user_id, status='dikonfirmasi'),
        'selesai': Booking.count_by_user(user_id, status='selesai')
    }
    
    return render_template('user/dashboard.html', user=user, bookings=bookings, stats=stats)


# ═══════════════════════════════════════════════════════════════
# BOOKING LIST
# ═══════════════════════════════════════════════════════════════

@bp.route('/booking')
@user_required
def booking():
    user_id = session.get('user_id')
    user = User.get_by_id(user_id)
    
    # Ambil semua booking user
    bookings = Booking.get_by_user_id(user_id)
    
    # Ambil booking aktif (untuk QR code)
    active_booking = Booking.get_active_queue(user_id)
    
    return render_template('user/booking.html', user=user, bookings=bookings, active_booking=active_booking)


# ═══════════════════════════════════════════════════════════════
# BOOKING DETAIL
# ═══════════════════════════════════════════════════════════════

@bp.route('/booking/detail/<int:id>')
@user_required
def booking_detail(id):
    user_id = session.get('user_id')
    user = User.get_by_id(user_id)
    
    booking = Booking.get_by_id(id)
    
    # Cek kepemilikan
    if not booking or booking.user_id != user_id:
        flash('Booking tidak ditemukan', 'danger')
        return redirect(url_for('user_routes.booking'))
    
    return render_template('user/booking-detail.html', user=user, booking=booking)


# ═══════════════════════════════════════════════════════════════
# BOOKING NEW (Form Page)
# ═══════════════════════════════════════════════════════════════

@bp.route('/booking/new', methods=['GET'])
@user_required
def booking_new():
    """Render booking form page"""
    user_id = session.get('user_id')
    user = User.get_by_id(user_id)
    
    layanan_id = request.args.get('layanan_id', type=int)
    service = Service.get_by_id(layanan_id) if layanan_id else None
    
    if not service:
        flash('Layanan tidak ditemukan', 'danger')
        return redirect(url_for('user_routes.layanan'))
    
    # Get tomorrow's date for min date
    tomorrow = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('user/booking-form.html', 
                         user=user, 
                         service=service,
                         min_date=tomorrow)


# ═══════════════════════════════════════════════════════════════
# BOOKING CREATE (Form Submit → Redirect)
# ═══════════════════════════════════════════════════════════════

@bp.route('/booking/create', methods=['POST'])
@user_required
def booking_create():
    """Create booking dengan nomor antrean otomatis lalu redirect ke halaman booking"""
    user_id = session.get('user_id')
    
    try:
        layanan_id = request.form.get('layanan_id', type=int)
        nama_pendaftar = request.form.get('nama_pendaftar', '').strip()
        tanggal_booking = request.form.get('tanggal_booking')
        jam_booking = request.form.get('jam_booking')
        catatan = request.form.get('catatan', '').strip()
        
        # Validation
        if not all([layanan_id, nama_pendaftar, tanggal_booking, jam_booking]):
            flash('Semua field wajib diisi!', 'danger')
            return redirect(url_for('user_routes.booking_new', layanan_id=layanan_id))
        
        # Validate service exists
        service = Service.get_by_id(layanan_id)
        if not service:
            flash('Layanan tidak ditemukan', 'danger')
            return redirect(url_for('user_routes.layanan'))
        
        # ═══════════════════════════════════════════════════════════════
        # CREATE BOOKING — TANGKAP ERROR DUPLIKAT/KUOTA
        # ═══════════════════════════════════════════════════════════════
        try:
            booking = Booking.create(
                user_id=user_id,
                layanan_id=layanan_id,
                nama_pendaftar=nama_pendaftar,
                tanggal_booking=tanggal_booking,
                jam_booking=jam_booking,
                catatan=catatan
            )
            
            flash(f'Booking berhasil! Nomor antrean Anda: #{booking.nomor_antrian}', 'success')
            return redirect(url_for('user_routes.booking'))
            
        except ValueError as ve:
            # Error dari model (duplikat atau kuota penuh)
            flash(str(ve), 'warning')
            return redirect(url_for('user_routes.booking_new', layanan_id=layanan_id))
        
    except Exception as e:
        flash(f'Terjadi kesalahan: {str(e)}', 'danger')
        return redirect(url_for('user_routes.layanan'))
    
@bp.route('/booking/cancel/<int:id>', methods=['POST'])
@user_required
def booking_cancel(id):
    """Cancel booking yang masih menunggu"""
    user_id = session.get('user_id')
    
    booking = Booking.get_by_id(id)
    
    if not booking or booking.user_id != user_id:
        flash('Booking tidak ditemukan', 'danger')
        return redirect(url_for('user_routes.booking'))
    
    if booking.status != 'menunggu':
        flash(f'Booking dengan status "{booking.status}" tidak bisa dibatalkan', 'warning')
        return redirect(url_for('user_routes.booking'))
    
    # ═══════════════════════════════════════════════════════════════
    # Pake method update_status yang udah ada di model!
    # ═══════════════════════════════════════════════════════════════
    try:
        Booking.update_status(
            booking_id=id,
            status_baru='dibatalkan',
            admin_id=None,
            keterangan='Booking dibatalkan oleh user'
        )
        
        flash('Booking berhasil dibatalkan', 'success')
        
    except Exception as e:
        flash(f'Gagal membatalkan booking: {str(e)}', 'danger')
    
    return redirect(url_for('user_routes.booking'))

# ═══════════════════════════════════════════════════════════════
# BOOKING RECEIPT — GENERATE IMAGE PNG (PURE PYTHON, NO BROWSER)
# ═══════════════════════════════════════════════════════════════

@bp.route('/booking/receipt/<int:id>/image')
@user_required
def booking_receipt_image(id):
    """Download bukti booking sebagai image PNG"""
    user_id = session.get('user_id')
    booking = Booking.get_by_id(id)
    
    if not booking or booking.user_id != user_id:
        flash('Booking tidak ditemukan', 'danger')
        return redirect(url_for('user_routes.booking'))
    
    if booking.status != 'selesai':
        flash('Bukti hanya tersedia untuk booking yang sudah selesai', 'warning')
        return redirect(url_for('user_routes.booking'))
    
    try:
        # ═══════════════════════════════════════════════════════════════
        # 1. SETUP CANVAS
        # ═══════════════════════════════════════════════════════════════
        width, height = 600, 800
        img = Image.new('RGB', (width, height), color='#FFFFFF')
        draw = ImageDraw.Draw(img)
        
        # ═══════════════════════════════════════════════════════════════
        # 2. LOAD FONT (cari yang ada di Windows)
        # ═══════════════════════════════════════════════════════════════
        font_paths = [
            "C:/Windows/Fonts/arialbd.ttf",      # Arial Bold
            "C:/Windows/Fonts/arial.ttf",         # Arial
            "C:/Windows/Fonts/segoeuib.ttf",      # Segoe UI Bold
            "C:/Windows/Fonts/segoeui.ttf",       # Segoe UI
            "C:/Windows/Fonts/tahomabd.ttf",      # Tahoma Bold
            "C:/Windows/Fonts/tahoma.ttf",        # Tahoma
        ]
        
        def load_font(size, bold=False):
            """Coba load font, fallback ke default"""
            for path in font_paths:
                if os.path.exists(path):
                    try:
                        return ImageFont.truetype(path, size)
                    except:
                        continue
            return ImageFont.load_default()
        
        font_title = load_font(22, bold=True)
        font_header = load_font(18, bold=True)
        font_bold = load_font(14, bold=True)
        font_normal = load_font(14)
        font_small = load_font(12)
        
        # ═══════════════════════════════════════════════════════════════
        # 3. GAMBAR HEADER GRADIENT
        # ═══════════════════════════════════════════════════════════════
        for i in range(8):
            r = 255
            g = int(107 + (i * 20))
            b = int(i * 10)
            draw.rectangle([(0, i), (width, i+1)], fill=(r, g, b))
        
        # ═══════════════════════════════════════════════════════════════
        # 4. KONTEN
        # ═══════════════════════════════════════════════════════════════
        y = 40
        
        # Icon kotak
        box_size = 50
        box_x = width // 2 - box_size // 2
        draw.rounded_rectangle(
            [(box_x, y), (box_x + box_size, y + box_size)],
            radius=12,
            fill=(255, 107, 0)
        )
        
        # Text "PB" di dalam kotak
        draw.text((width // 2, y + box_size // 2), "PB", 
                 fill='white', font=font_header, anchor='mm')
        y += box_size + 20
        
        # Judul
        draw.text((width // 2, y), "BUKTI BOOKING", 
                 fill='#333333', font=font_header, anchor='mm')
        y += 30
        
        # Subtitle
        draw.text((width // 2, y), "PublicBook - Sistem Antrean Online", 
                 fill='#888888', font=font_small, anchor='mm')
        y += 40
        
        # Status badge
        badge_w, badge_h = 120, 32
        badge_x = width // 2 - badge_w // 2
        draw.rounded_rectangle(
            [(badge_x, y), (badge_x + badge_w, y + badge_h)],
            radius=16,
            fill=(232, 245, 233)
        )
        draw.text((width // 2, y + badge_h // 2), "SELESAI", 
                 fill='#388E3C', font=font_bold, anchor='mm')
        y += badge_h + 30
        
        # Garis pemisah
        draw.line([(40, y), (width - 40, y)], fill='#FF6B00', width=2)
        y += 25
        
        # ═══════════════════════════════════════════════════════════════
        # 5. DATA BOOKING
        # ═══════════════════════════════════════════════════════════════
        data_rows = [
            ("No. Booking", booking.no_booking, True),
            ("Nomor Antrean", f"#{booking.nomor_antrian}", False),
            ("Layanan", booking.nama_layanan, False),
            ("Instansi", booking.instansi or '-', False),
            ("Nama Pendaftar", booking.nama_pendaftar, False),
            ("Tanggal", str(booking.tanggal_booking), False),
            ("Jam", str(booking.jam_booking), False),
            ("Selesai", datetime.now().strftime('%d %b %Y, %H:%M'), False),
        ]
        
        for label, value, is_highlight in data_rows:
            # Label kiri
            draw.text((40, y), label, fill='#888888', font=font_small)
            
            # Value kanan
            if is_highlight:
                # Background highlight
                bbox = draw.textbbox((0, 0), value, font=font_bold)
                text_w = bbox[2] - bbox[0]
                draw.rounded_rectangle(
                    [(width - 40 - text_w - 10, y - 2), (width - 40, y + 22)],
                    radius=4,
                    fill=(255, 248, 240)
                )
                draw.text((width - 40, y), value, 
                         fill='#FF6B00', font=font_bold, anchor='ra')
            else:
                draw.text((width - 40, y), value, 
                         fill='#333333', font=font_normal, anchor='ra')
            
            y += 35
            # Garis bawah tipis
            draw.line([(40, y - 8), (width - 40, y - 8)], 
                     fill='#f5f5f5', width=1)
        
        # ═══════════════════════════════════════════════════════════════
        # 6. QR CODE
        # ═══════════════════════════════════════════════════════════════
        y += 20
        
        # Generate QR
        qr = qrcode.QRCode(version=1, box_size=4, border=2)
        qr.add_data(f"{request.host_url.rstrip('/')}/scan/{booking.no_booking}")
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="#333333", back_color="#ffffff")
        
        # Resize dan tempel
        qr_size = 120
        qr_img = qr_img.resize((qr_size, qr_size))
        img.paste(qr_img, (width // 2 - qr_size // 2, y))
        y += qr_size + 15
        
        # Text bawah QR
        draw.text((width // 2, y), "Scan untuk verifikasi", 
                 fill='#aaaaaa', font=font_small, anchor='mm')
        y += 25
        
        # Footer text
        draw.text((width // 2, y), 
                 "Dokumen ini adalah bukti sah bahwa booking telah selesai dilayani.",
                 fill='#cccccc', font=font_small, anchor='mm')
        
        # ═══════════════════════════════════════════════════════════════
        # 7. STAMP "SELESAI" (transparan, rotated)
        # ═══════════════════════════════════════════════════════════════
        stamp_size = 140
        stamp = Image.new('RGBA', (stamp_size, stamp_size), (255, 255, 255, 0))
        stamp_draw = ImageDraw.Draw(stamp)
        
        # Lingkaran stamp
        stamp_draw.ellipse(
            [(5, 5), (stamp_size - 5, stamp_size - 5)],
            outline='#4CAF50',
            width=3
        )
        
        # Text stamp
        stamp_draw.text((stamp_size // 2, stamp_size // 2), "SELESAI",
                       fill='#4CAF50', font=font_bold, anchor='mm')
        
        # Rotate
        stamp = stamp.rotate(-20, expand=True)
        
        # Tempel ke image utama (pake alpha)
        img.paste(stamp, (width - 180, height - 200), stamp)
        
        # ═══════════════════════════════════════════════════════════════
        # 8. BORDER FRAME
        # ═══════════════════════════════════════════════════════════════
        # Border luar
        draw.rounded_rectangle(
            [(10, 10), (width - 10, height - 10)],
            radius=20,
            outline='#FF6B00',
            width=3
        )

        # ═══════════════════════════════════════════════════════════════
        # 9. SAVE & KIRIM
        # ═══════════════════════════════════════════════════════════════
        img_io = io.BytesIO()
        img.save(img_io, 'PNG', quality=95)
        img_io.seek(0)
        
        return send_file(
            img_io,
            mimetype='image/png',
            as_attachment=True,
            download_name=f'bukti-{booking.no_booking}.png'
        )
        
    except Exception as e:
        flash(f'Gagal generate bukti: {str(e)}', 'danger')
        return redirect(url_for('user_routes.booking'))
    
# ═══════════════════════════════════════════════════════════════
# LAYANAN
# ═══════════════════════════════════════════════════════════════

@bp.route('/layanan')
@user_required
def layanan():
    user_id = session.get('user_id')
    user = User.get_by_id(user_id)
    
    # Ambil semua layanan aktif
    services = Service.get_all_active()
    
    return render_template('user/layanan.html', user=user, services=services)


# ═══════════════════════════════════════════════════════════════
# PROFIL
# ═══════════════════════════════════════════════════════════════

@bp.route('/profil')
@user_required
def profil():
    user_id = session.get('user_id')
    user = User.get_by_id(user_id)
    active_queue = Booking.get_active_queue(user_id)
    
    # Ambil info posisi antrean
    queue_info = None
    if active_queue and active_queue.nomor_antrian:
        queue_info = Booking.get_queue_position(active_queue.id)
    
    stats = {
        'total_booking': Booking.count_by_user(user_id),
        'menunggu': Booking.count_by_user(user_id, status='menunggu'),
        'selesai': Booking.count_by_user(user_id, status='selesai')
    }
    
    return render_template('user/profil.html', 
                         user=user, 
                         queue=active_queue, 
                         queue_info=queue_info,
                         stats=stats)