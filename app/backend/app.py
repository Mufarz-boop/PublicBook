from flask import Flask
from config import Config
from app.database.db import init_db
from app.routes import auth_routes, admin_routes, teacher_routes, student_routes, static_routes
import os

def create_app():
    app = Flask(__name__, 
                template_folder='app/templates',
                static_folder='app/static')
    app.config.from_object(Config)
    
    # Ensure upload folder exists
    upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), app.config['UPLOAD_FOLDER'])
    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(os.path.join(upload_folder, 'images'), exist_ok=True)
    os.makedirs(os.path.join(upload_folder, 'videos'), exist_ok=True)
    os.makedirs(os.path.join(upload_folder, 'audio'), exist_ok=True)
    os.makedirs(os.path.join(upload_folder, 'documents'), exist_ok=True)
    
    # Initialize database
    init_db(app)
    
    # Register blueprints
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(admin_routes.bp)
    app.register_blueprint(teacher_routes.bp)
    app.register_blueprint(student_routes.bp)
    app.register_blueprint(static_routes.bp)
    
    # Context processor for global template variables
    @app.context_processor
    def inject_globals():
        from flask import session
        return {
            'current_user': session.get('user'),
            'current_role': session.get('role')
        }
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)