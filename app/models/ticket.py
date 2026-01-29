from app.extensions import db
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False) # TI, Financeiro, RH, Infraestrutura
    priority = db.Column(db.String(20), default='Media') # Baixa, Media, Alta, Critica
    status = db.Column(db.String(20), default='Aberto') # Aberto, Em andamento, Aguardando, Resolvido, Fechado
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    due_at = db.Column(db.DateTime, nullable=True) # Prazo final (SLA)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    assigned_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Quem atribuiu
    observer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    author = db.relationship('User', foreign_keys=[user_id], backref=db.backref('tickets_created', lazy='dynamic'))
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref=db.backref('tickets_assigned', lazy='dynamic'))
    assigned_by = db.relationship('User', foreign_keys=[assigned_by_id], backref='tickets_delegated')
    observer = db.relationship('User', foreign_keys=[observer_id], backref='tickets_as_observer')

    comments = db.relationship('Comment', backref='ticket', lazy='dynamic', cascade="all, delete-orphan")
    attachments = db.relationship('Attachment', backref='ticket', lazy='dynamic', cascade="all, delete-orphan")
    used_items = db.relationship('TicketItem', back_populates='ticket', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Ticket {self.id}: {self.title}>'

class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)

    def __repr__(self):
        return f'<Attachment {self.filename}>'

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    
    def __repr__(self):
        return f'<Comment {self.content[:20]}...>'

class TicketItem(db.Model):
    """Relacionamento entre tickets e itens usados na resolução"""
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    quantity_used = db.Column(db.Integer, default=1)  # Quantidade usada
    used_at = db.Column(db.DateTime, default=datetime.utcnow)  # Quando foi usado
    notes = db.Column(db.Text, nullable=True)  # Observações sobre o uso
    
    # Relacionamentos
    ticket = db.relationship('Ticket', back_populates='used_items')
    item = db.relationship('Item', back_populates='ticket_items')
    
    @hybrid_property
    def total_cost(self):
        """Calcula o custo total baseado na quantidade usada e custo unitário do item"""
        return self.quantity_used * self.item.unit_cost
    
    def __repr__(self):
        return f'<TicketItem ticket:{self.ticket_id} item:{self.item_id} qty:{self.quantity_used}>'
