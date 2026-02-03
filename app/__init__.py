import os
from flask import Flask
from .config import Config
from .extensions import db, login_manager, migrate
from flask_cors import CORS
import sqlalchemy as sa
from sqlalchemy import text

def setup_database(app):
    with app.app_context():
        try:
            # Testa conexão básica antes de tudo
            db.session.execute(text('SELECT 1'))
            
            # Cria as tabelas se não existirem
            db.create_all()
            
            # Cria administrador padrão
            from app.models.user import User
            if not User.query.first():
                admin_user = User(username='admin', email='admin@local', role='admin', fullname='Administrador')
                admin_user.set_password('admin')
                db.session.add(admin_user)
                db.session.commit()
                app.logger.info("Admin padrão criado com sucesso.")
        except Exception as e:
            app.logger.error(f"Erro crítico no banco de dados: {e}")

def reset_sequences(app):
    """Reseta as sequências de ID no Postgres para evitar erro de violação de ID único após migração"""
    with app.app_context():
        if db.engine.name == 'postgresql':
            try:
                # Busca todas as tabelas e reseta a sequência pro valor máximo do ID + 1
                inspector = sa.inspect(db.engine)
                for table_name in inspector.get_table_names():
                    # Ignora tabelas sem coluna id
                    columns = [col['name'] for col in inspector.get_columns(table_name)]
                    if 'id' in columns:
                        db.session.execute(text(f"SELECT setval(pg_get_serial_sequence('\"{table_name}\"', 'id'), coalesce(max(id), 0) + 1, false) FROM \"{table_name}\""))
                db.session.commit()
                app.logger.info("Sequências de ID resetadas com sucesso.")
            except Exception as e:
                app.logger.error(f"Erro ao resetar sequências: {e}")

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    CORS(app) # Habilita CORS para todas as rotas

    # Ensure required directories exist (ignora erro se o FS for Read-Only como na Vercel)
    try:
        os.makedirs(os.path.join(app.root_path, '..', 'instance'), exist_ok=True)
        os.makedirs(os.path.join(app.root_path, 'uploads'), exist_ok=True)
    except:
        pass


    # Initialize Flask extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # Run automatic migrations
    setup_database(app)
    
    # Reseta sequências no Postgres após o setup
    reset_sequences(app)
    # Configurações do Login Manager
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

