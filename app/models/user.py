from app.extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    fullname = db.Column(db.String(200), nullable=True)  # Full name from AD or manual input
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user') # 'admin', 'user'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships managed in Ticket model to avoid circular import/mapper issues
    # tickets_created = db.relationship('Ticket', backref='author', lazy='dynamic', foreign_keys='Ticket.user_id', cascade='all, delete-orphan')
    # tickets_assigned = db.relationship('Ticket', backref='assigned_to', lazy='dynamic', foreign_keys='Ticket.assigned_to_id')
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
