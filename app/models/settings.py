from app.extensions import db

class AppSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ad_server = db.Column(db.String(128), nullable=True)
    ad_domain = db.Column(db.String(128), nullable=True)
    ad_base_dn = db.Column(db.String(128), nullable=True)
    ad_user_dn = db.Column(db.String(128), nullable=True) # User to bind with (usually required for AD)
    ad_user_password = db.Column(db.String(128), nullable=True) # Password for bind user
    
    # SLA Settings (in hours)
    sla_hours_baixa = db.Column(db.Integer, default=48)
    sla_hours_media = db.Column(db.Integer, default=24)
    sla_hours_alta = db.Column(db.Integer, default=8)
    sla_hours_critica = db.Column(db.Integer, default=4)
    theme = db.Column(db.String(20), default='light')

    def __repr__(self):
        return '<AppSettings>'

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False)  # Categoria do item (ex: Hardware, Software, Peças)
    quantity = db.Column(db.Integer, default=0)  # Quantidade em estoque
    min_quantity = db.Column(db.Integer, default=0)  # Quantidade mínima para alerta
    unit_cost = db.Column(db.Float, default=0.0)  # Custo unitário
    location = db.Column(db.String(100), nullable=True)  # Localização física
    supplier = db.Column(db.String(100), nullable=True)  # Fornecedor
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Relacionamento com tickets (itens usados em chamados)
    ticket_items = db.relationship('TicketItem', back_populates='item', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Item {self.name}>'
    
    @property
    def is_low_stock(self):
        """Verifica se o item está com estoque baixo"""
        return self.quantity <= self.min_quantity
    
    @property
    def total_value(self):
        """Calcula o valor total do estoque"""
        return self.quantity * self.unit_cost
