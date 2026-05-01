# backend/app.py

from flask import Flask

app = Flask(__name__,
    template_folder='../frontend/pages',  # ← folder templates
    static_folder='../frontend/assets'    # ← folder static
)

# Register blueprint
from routes.static import bp as static_bp
from routes.auth import bp as auth_bp

app.register_blueprint(static_bp)
app.register_blueprint(auth_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5000)