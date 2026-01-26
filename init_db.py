"""
Script de inicialização definitiva do Banco de Dados.
Este script cria as tabelas, realiza migrações necessárias e cria o usuário administrador inicial.
"""
import os
from app import create_app, db
from app.models.user import User
from app.models.settings import Item, Category, AppSettings
from app.models.ticket import Ticket, Attachment, Comment, TicketItem
from sqlalchemy import text, inspect

def setup_db():
    app = create_app()
    with app.app_context():
        print("Verificando banco de dados...")
        
        # 1. Garantir que todas as tabelas existam
        db.create_all()
        print("✓ Tabelas verificadas/criadas.")
        
        # 2. Verificar colunas faltantes (Migrações manuais)
        inspector = inspect(db.engine)
        
        # Tabela User -> fullname
        user_cols = [col['name'] for col in inspector.get_columns('user')]
        if 'fullname' not in user_cols:
            print("Adicionando coluna 'fullname' à tabela 'user'...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE user ADD COLUMN fullname VARCHAR(200)"))
                conn.commit()
            print("✓ Coluna 'fullname' adicionada.")

        # Tabela Ticket -> resolved_at
        ticket_cols = [col['name'] for col in inspector.get_columns('ticket')]
        if 'resolved_at' not in ticket_cols:
            print("Adicionando coluna 'resolved_at' à tabela 'ticket'...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE ticket ADD COLUMN resolved_at DATETIME"))
                conn.commit()
            print("✓ Coluna 'resolved_at' adicionada.")

        # 3. Criar usuário administrador padrão se não existir
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("Criando usuário administrador padrão...")
            admin = User(
                username='admin',
                email='admin@example.com',
                fullname='Administrador do Sistema',
                role='admin'
            )
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()
            print("✓ Usuário 'admin' criado com sucesso! (Senha: admin)")
        else:
            print("✓ Usuário 'admin' já existe.")

        # 4. Criar categorias padrão se estiver vazio
        if Category.query.count() == 0:
            print("Criando categorias padrão...")
            categories = ['Hardware', 'Software', 'Redes', 'Financeiro', 'RH']
            for name in categories:
                db.session.add(Category(name=name))
            db.session.commit()
            print(f"✓ {len(categories)} categorias criadas.")

        # 5. Criar configurações iniciais se não existir
        if AppSettings.query.count() == 0:
            print("Criando configurações iniciais...")
            db.session.add(AppSettings())
            db.session.commit()
            print("✓ Configurações iniciais criadas.")

        print("\n🚀 Banco de dados pronto para uso!")

if __name__ == '__main__':
    setup_db()
