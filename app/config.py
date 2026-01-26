import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_secret_key_123'
    
    # Base directory of the application (app folder)
    _basedir = os.path.abspath(os.path.dirname(__file__))
    # Project root
    _rootdir = os.path.abspath(os.path.join(_basedir, os.pardir))
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(_rootdir, 'instance', 'helpdesk.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # 16MB max limit
