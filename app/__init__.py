import os
from flask import Flask
from .config import Config
from .extensions import db, login_manager, migrate
from flask_cors import CORS
import sqlalchemy as sa
from sqlalchemy import text

def setup_database(app):
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Create default admin if no users exist
        from app.models.user import User
        if not User.query.first():
            admin_user = User(username='admin', email='admin@local', role='admin', fullname='Administrador')
            admin_user.set_password('admin')
            db.session.add(admin_user)
            db.session.commit()
            app.logger.info("Default admin user created.")

        
        # Check for missing columns (manual migration)
        try:
            inspector = sa.inspect(db.engine)
            
            # Check User table for fullname
            user_columns = [col['name'] for col in inspector.get_columns('user')]
            if 'fullname' not in user_columns:
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE user ADD COLUMN fullname VARCHAR(200)"))
                    conn.commit()
            
            # Check Ticket table for resolved_at
            ticket_columns = [col['name'] for col in inspector.get_columns('ticket')]
            if 'resolved_at' not in ticket_columns:
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE ticket ADD COLUMN resolved_at DATETIME"))
                    conn.commit()
                    
        except Exception as e:
            app.logger.error(f"Error during automatic migration: {e}")

        # Cleanup unwanted default categories
        try:
            from app.models.settings import Category
            unwanted = ['TI', 'FINANCEIRO', 'RH', 'INFRAESTRUTURA', 'OUTRO', 'Financeiro', 'Infraestrutura', 'Outro']
            for cat_name in unwanted:
                cat = Category.query.filter(sa.func.lower(Category.name) == cat_name.lower()).first()
                if cat:
                    db.session.delete(cat)
            db.session.commit()
        except:
            pass

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    CORS(app) # Habilita CORS para todas as rotas

    # Ensure required directories exist
    os.makedirs(os.path.join(app.root_path, '..', 'instance'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'uploads'), exist_ok=True)


    # Initialize Flask extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # Run automatic migrations
    setup_database(app)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'

    # Register blueprints
    from .routes.main import main_bp
    from .routes.auth import auth_bp
    from .routes.tickets import tickets_bp
    from .routes.users import users_bp
    from .routes.settings import settings_bp
    from .routes.inventory import inventory_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(inventory_bp)

    return app

