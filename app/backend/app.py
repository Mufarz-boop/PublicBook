# backend/app.py

from flask import Flask
from config import config_by_publicbook
import os

env = os.getenv('ENV', 'development')
app = Flask(__name__,
    template_folder='../frontend/pages',  # ← folder templates
    static_folder='../frontend/assets'    # ← folder static
)
app.config.from_object(config_by_publicbook[env])

# Register blueprint
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
    app.run(debug=True, port=5000)