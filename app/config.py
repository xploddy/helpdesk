import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_secret_key_123'
    
    # Base directory of the application (app folder)
    _basedir = os.path.abspath(os.path.dirname(__file__))
    # Project root
    _rootdir = os.path.abspath(os.path.join(_basedir, os.pardir))
    
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        
        # Remove pgbouncer=true pois o psycopg2 não reconhece como opção de conexão válida
        if "pgbouncer=true" in db_url:
            db_url = db_url.replace("pgbouncer=true", "")
            db_url = db_url.replace("?&", "?").replace("&&", "&").strip("?&")

        if "sslmode=" not in db_url:
            separator = "&" if "?" in db_url else "?"
            db_url += f"{separator}sslmode=require"

    
    SQLALCHEMY_DATABASE_URI = db_url or 'sqlite:///' + os.path.join(_rootdir, 'instance', 'helpdesk.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configurações para Serverless / Supabase
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_timeout": 30,
    }

    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # 16MB max limit
