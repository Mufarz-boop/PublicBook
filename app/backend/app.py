# backend/app.py
from flask import Flask
from config import config_by_publicbook
from database.database import init_db, close_db
import os

env = os.getenv('ENV', 'development')

app = Flask(__name__,
    template_folder='../frontend/pages',
    static_folder='../frontend/assets'
)
app.config.from_object(config_by_publicbook[env])

# Inisialisasi database
init_db(app)

# Register teardown untuk tutup session
@app.teardown_appcontext
def teardown_db(exception):
    close_db()

# Register blueprints
from routes.static import bp as static_bp
from routes.auth import bp as auth_bp
from routes.user import bp as user_bp
from routes.admin import bp as admin_bp
from routes.auth_api import bp as auth_api_bp

app.register_blueprint(static_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(auth_api_bp)
app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)

if __name__ == '__main__':
    app.run(debug=app.config.get('DEBUG', True), port=app.config.get('PORT', 5000))