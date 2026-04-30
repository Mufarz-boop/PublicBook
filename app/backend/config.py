import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'publicbook-dev-secret-key'
    
    # MySQL Configuration
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or 'razitanurin'
    MYSQL_DB = os.environ.get('MYSQL_DB') or 'db_publicbook'
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)

    # Session Configuration
    PERMANENT_SESSION_LIFETIME = 604800  # 1 Minggu