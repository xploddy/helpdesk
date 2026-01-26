import os
_basedir = os.path.abspath(os.path.dirname(__file__))
_rootdir = os.path.abspath(os.path.join(_basedir, os.pardir))
db_path = os.path.join(_rootdir, 'instance', 'helpdesk.db')
print("DB path:", db_path)
print("Exists:", os.path.exists(db_path))