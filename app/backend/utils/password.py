# backend/utils/password.py
import bcrypt
from werkzeug.security import check_password_hash

def hash_password(plain_password: str) -> str:
    """Hash password dengan bcrypt"""
    password_bytes = plain_password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifikasi password — support bcrypt & scrypt/werkzeug legacy"""
    if not hashed_password:
        return False
    # bcrypt format
    if hashed_password.startswith('$2'):
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    # scrypt / pbkdf2 legacy (Werkzeug)
    return check_password_hash(hashed_password, plain_password)