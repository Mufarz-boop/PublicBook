# backend/app.py
from flask import Flask
from config import config_by_publicbook
from database.database import init_db, close_db
import os

env = os.getenv('ENV', 'development')

app = Flask(__name__, template_folder='../frontend/pages', static_folder='../frontend/assets')
app.config.from_object(config_by_publicbook[env])

try:
    init_db(app)
except Exception as e:
    print(f"Database initialization failed: {e}")
    print("Pastikan:")
    print("  1. Laragon/XAMPP MySQL sudah START")
    print("  2. .env berada di root folder")
    print("  3. Database db_publicbook sudah dibuat di phpMyAdmin")
    raise

@app.teardown_appcontext
def teardown_db(exception):
    close_db()

from routes.static import bp as static_bp
from routes.auth import bp as auth_bp
from routes.auth_api import bp as auth_api_bp
from routes.user import bp as user_bp
from routes.admin import bp as admin_bp

app.register_blueprint(static_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(auth_api_bp)
app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)

if __name__ == '__main__':
    app.run(debug=app.config.get('DEBUG', True), port=app.config.get('PORT', 5000))