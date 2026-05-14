# ============================================================
# ⛔ PENTING: TARUH FILE INI DI ROOT FOLDER!
#    (sejajar dengan .env dan folder backend/)
#
#    BENAR:  publicbook/test_connection.py
#    SALAH:  publicbook/backend/test_connection.py
# ============================================================

# ============================================================
# ⛔ PENTING: TARUH FILE INI DI ROOT FOLDER!
#    (sejajar dengan .env dan folder backend/)
#
#    BENAR:  publicbook/test_connection.py
#    SALAH:  publicbook/backend/test_connection.py
# ============================================================

# test_connection.py
# ============================================================
# Script test koneksi database PublicBook
# Taruh file ini di ROOT folder (sejajar dengan .env dan backend/)
# ============================================================

import sys
import os

# Tambahkan backend/ ke Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from flask import Flask
from config import config_by_publicbook
from database.database import init_db, get_db
from sqlalchemy import text

# Buat app minimal untuk test
app = Flask(__name__)
app.config.from_object(config_by_publicbook['development'])

print("=" * 60)
print("🔌 PUBLICBOOK - DATABASE CONNECTION TEST")
print("=" * 60)
print(f"\n📡 Database URI:")
print(f"   {app.config['SQLALCHEMY_DATABASE_URI']}")
print(f"\n🖥️  Environment: {app.config.get('ENV', 'development')}")

try:
    # Inisialisasi database
    init_db(app)
    db = get_db()

    # Test 1: Koneksi dasar
    result = db.execute(text("SELECT 1 as test")).mappings().first()
    print(f"\n✅ [TEST 1] Koneksi database: BERHASIL (result={result['test']})")

    # Test 2: Cek tabel yang ada
    tables = db.execute(text("""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = DATABASE()
        ORDER BY TABLE_NAME
    """)).mappings().all()

    print(f"\n📊 [TEST 2] Tabel di database '{app.config['DB_NAME']}':")
    for t in tables:
        print(f"   • {t['TABLE_NAME']}")

    # Test 3: Cek data admin
    admin_count = db.execute(text("SELECT COUNT(*) as count FROM admins")).mappings().first()
    print(f"\n👤 [TEST 3] Jumlah admin: {admin_count['count']}")

    # Test 4: Cek data user
    user_count = db.execute(text("SELECT COUNT(*) as count FROM users")).mappings().first()
    print(f"\n👥 [TEST 4] Jumlah user: {user_count['count']}")

    # Test 5: Cek struktur tabel users
    user_cols = db.execute(text("""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users'
        ORDER BY ORDINAL_POSITION
    """)).mappings().all()

    print(f"\n📝 [TEST 5] Kolom tabel 'users':")
    for col in user_cols:
        nullable = "NULL" if col['IS_NULLABLE'] == 'YES' else "NOT NULL"
        print(f"   • {col['COLUMN_NAME']:<20} {col['DATA_TYPE']:<15} {nullable}")

    # Test 6: Cek struktur tabel admins
    admin_cols = db.execute(text("""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'admins'
        ORDER BY ORDINAL_POSITION
    """)).mappings().all()

    print(f"\n📝 [TEST 6] Kolom tabel 'admins':")
    for col in admin_cols:
        nullable = "NULL" if col['IS_NULLABLE'] == 'YES' else "NOT NULL"
        print(f"   • {col['COLUMN_NAME']:<20} {col['DATA_TYPE']:<15} {nullable}")

    print("\n" + "=" * 60)
    print("🎉 SEMUA TEST BERHASIL! Database siap digunakan.")
    print("=" * 60)
    print("\n🚀 Selanjutnya: cd backend && python app.py")

except Exception as e:
    print(f"\n❌ [ERROR] {e}")
    print("\n" + "=" * 60)
    print("💡 TROUBLESHOOTING:")
    print("=" * 60)
    print("   1. Pastikan Laragon/MySQL sudah START (hijau)")
    print("   2. Cek .env - DB_PASSWORD harus sesuai")
    print("   3. Pastikan database sudah dibuat di phpMyAdmin")
    print("   4. Coba jalankan: pip install pymysql cryptography")
    print("   5. Cek port MySQL: Laragon → Menu → MySQL → MySQL Console")
    print("      Ketik: SHOW VARIABLES LIKE 'port';")
    print("\n📁 Lokasi .env:")
    print(f"   {os.path.join(os.path.dirname(__file__), '.env')}")