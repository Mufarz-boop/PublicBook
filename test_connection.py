# test_connection.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'backend'))

from flask import Flask
from config import config_by_publicbook
from database.database import init_db, get_db
from sqlalchemy import text

app = Flask(__name__)
app.config.from_object(config_by_publicbook['development'])

print("="*60)
print("  PUBLICBOOK - DATABASE CONNECTION TEST")
print("="*60)
print(f"  Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

try:
    init_db(app)
    db = get_db()
    result = db.execute(text("SELECT 1 as test")).mappings().first()
    print(f"  [TEST 1] Koneksi database: BERHASIL (result={result['test']})")

    tables = db.execute(text("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = DATABASE() ORDER BY TABLE_NAME")).mappings().all()
    print(f"  [TEST 2] Tabel di database '{app.config['DB_NAME']}':")
    for t in tables:
        print(f"    - {t['TABLE_NAME']}")

    admin_count = db.execute(text("SELECT COUNT(*) as count FROM admins")).mappings().first()
    user_count = db.execute(text("SELECT COUNT(*) as count FROM users")).mappings().first()
    print(f"  [TEST 3] Jumlah admin: {admin_count['count']}")
    print(f"  [TEST 4] Jumlah user: {user_count['count']}")
    print("  SEMUA TEST BERHASIL!")
    print("  Selanjutnya: cd app/backend && python app.py")

except Exception as e:
    print(f"  [ERROR] {e}")
    print("  TROUBLESHOOTING:")
    print("    1. Pastikan Laragon/MySQL sudah START")
    print("    2. Cek .env - DB_PASSWORD harus 'razitanurin'")
    print("    3. Pastikan database 'db_publicbook' sudah dibuat")
