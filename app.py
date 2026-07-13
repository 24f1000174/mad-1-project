import os
from flask import Flask
from config import Config
from extensions import db, login_manager

def create_app(config_class=Config):
    """Application factory for the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Ensure the instance folder exists for SQLite db
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
        
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    
    # Import models to register them with SQLAlchemy and Flask-Login
    from database import models

    
    # Register blueprints
    from blueprints.common import common_bp
    from blueprints.auth import auth_bp
    from blueprints.admin import admin_bp
    from blueprints.staff import staff_bp
    from blueprints.user import user_bp
    
    app.register_blueprint(common_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(user_bp)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Auto-create database tables and seed default admin user
    with app.app_context():
        db.create_all()
        from database.models import User, Profile
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@trekking.com',
                role='admin',
                status='approved'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.flush()
            
            profile = Profile(
                user_id=admin.id,
                full_name='System Administrator',
                phone='9876543210',
                address='Admin Headquarters'
            )
            db.session.add(profile)
            db.session.commit()
            print("Database initialized and default Admin seeded successfully.")
            
    return app

def register_error_handlers(app):
    """Registers handlers for common HTTP error codes."""
    from flask import render_template

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_server_error(e):
        return "500 - Internal Server Error", 500

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
