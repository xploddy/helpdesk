from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Iniciando migração manual do banco de dados...")
    
    # 1. Adicionar colunas SLA na tabela app_settings
    # SQLite não suporta IF NOT EXISTS no ADD COLUMN, então embrulhamos em try/except
    try:
        db.session.execute(text("ALTER TABLE app_settings ADD COLUMN sla_hours_baixa INTEGER DEFAULT 48"))
        print("Coluna sla_hours_baixa adicionada.")
    except Exception as e:
        print(f"Nota: Coluna sla_hours_baixa provavelmente já existe ({str(e)})")

    try:
        db.session.execute(text("ALTER TABLE app_settings ADD COLUMN sla_hours_media INTEGER DEFAULT 24"))
        print("Coluna sla_hours_media adicionada.")
    except Exception as e:
        print(f"Nota: Coluna sla_hours_media provavelmente já existe ({str(e)})")

    try:
        db.session.execute(text("ALTER TABLE app_settings ADD COLUMN sla_hours_alta INTEGER DEFAULT 8"))
        print("Coluna sla_hours_alta adicionada.")
    except Exception as e:
        print(f"Nota: Coluna sla_hours_alta provavelmente já existe ({str(e)})")

    try:
        db.session.execute(text("ALTER TABLE app_settings ADD COLUMN sla_hours_critica INTEGER DEFAULT 4"))
        print("Coluna sla_hours_critica adicionada.")
    except Exception as e:
        print(f"Nota: Coluna sla_hours_critica provavelmente já existe ({str(e)})")

    # 2. Adicionar colunas due_at e assigned_by_id na tabela ticket
    try:
        db.session.execute(text("ALTER TABLE ticket ADD COLUMN due_at DATETIME"))
        print("Coluna due_at adicionada.")
    except Exception as e:
        print(f"Nota: Coluna due_at provavelmente já existe ({str(e)})")

    try:
        db.session.execute(text("ALTER TABLE ticket ADD COLUMN assigned_by_id INTEGER REFERENCES users(id)"))
        print("Coluna assigned_by_id adicionada.")
    except Exception as e:
        print(f"Nota: Coluna assigned_by_id provavelmente já existe ({str(e)})")

    # 3. Adicionar coluna theme na tabela users
    try:
        db.session.execute(text("ALTER TABLE users ADD COLUMN theme VARCHAR(20) DEFAULT 'light'"))
        print("Coluna theme adicionada na tabela users.")
    except Exception as e:
        try:
            # Tentar na tabela 'user' caso o nome seja esse no banco remoto
            db.session.execute(text("ALTER TABLE \"user\" ADD COLUMN theme VARCHAR(20) DEFAULT 'light'"))
            print("Coluna theme adicionada na tabela user.")
        except Exception as e2:
            print(f"Nota: Coluna theme provavelmente já existe ({str(e2)})")

    db.session.commit()
    print("Migração concluída.")
