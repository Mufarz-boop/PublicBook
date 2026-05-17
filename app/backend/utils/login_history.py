# backend/utils/login_history.py
"""
Utility untuk mencatat riwayat login
Dipisahkan agar menghindari circular import
"""
from database.database import get_db
from sqlalchemy import text
from flask import request

def get_device_info(user_agent_string):
    """Parse user agent sederhana untuk mendapatkan info perangkat"""
    if not user_agent_string:
        return 'Unknown Device'
    
    ua = user_agent_string.lower()
    
    # Detect OS
    if 'windows' in ua:
        os_name = 'Windows'
    elif 'macintosh' in ua or 'mac os' in ua:
        os_name = 'macOS'
    elif 'linux' in ua:
        os_name = 'Linux'
    elif 'android' in ua:
        os_name = 'Android'
    elif 'iphone' in ua or 'ipad' in ua:
        os_name = 'iOS'
    else:
        os_name = 'Unknown OS'
    
    # Detect Browser
    if 'chrome' in ua and 'edg' not in ua:
        browser = 'Chrome'
    elif 'firefox' in ua:
        browser = 'Firefox'
    elif 'safari' in ua and 'chrome' not in ua:
        browser = 'Safari'
    elif 'edg' in ua:
        browser = 'Edge'
    elif 'opera' in ua:
        browser = 'Opera'
    else:
        browser = 'Unknown Browser'
    
    # Detect Device Type
    if 'mobile' in ua:
        device = 'Mobile'
    elif 'tablet' in ua or 'ipad' in ua:
        device = 'Tablet'
    else:
        device = 'Desktop'
    
    return f"{browser} on {os_name} ({device})"

def get_client_ip():
    """Mendapatkan IP client yang akurat"""
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        ip = request.headers.get('X-Real-IP')
    else:
        ip = request.remote_addr or 'Unknown'
    return ip

def catat_login_history(user_id=None, admin_id=None, status='success'):
    """
    Catat riwayat login ke database
    Dipanggil dari routes/auth.py setelah login berhasil/gagal
    """
    try:
        db = get_db()
        ip = get_client_ip()
        user_agent = request.headers.get('User-Agent', '')
        device_info = get_device_info(user_agent)
        
        # Untuk local/Laragon, tetap catat dengan label Local Network
        if ip in ['127.0.0.1', 'localhost', '::1'] or \
           ip.startswith('192.168.') or \
           ip.startswith('10.') or \
           ip.startswith('172.'):
            location = 'Local Network (Laragon)'
        else:
            location = 'Unknown'
        
        db.execute(
            text("""
                INSERT INTO login_history 
                (user_id, admin_id, ip_address, user_agent, device_info, location, status, created_at)
                VALUES (:user_id, :admin_id, :ip, :ua, :device, :location, :status, NOW())
            """),
            {
                'user_id': user_id,
                'admin_id': admin_id,
                'ip': ip,
                'ua': user_agent[:255] if user_agent else None,
                'device': device_info[:100],
                'location': location[:150],
                'status': status
            }
        )
        db.commit()
        print(f"[LOGIN HISTORY] Recorded: admin_id={admin_id}, user_id={user_id}, status={status}, ip={ip}, device={device_info}")
    except Exception as e:
        print(f"[LOGIN HISTORY ERROR] {e}")
        # Jangan crash aplikasi jika gagal mencatat history