from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_required, current_user
from app.extensions import db
from sqlalchemy import text
from app.models.settings import Category, AppSettings
from app.models.user import User
import ldap3
import secrets
import string
import zipfile
import io
import os
import shutil
from datetime import datetime
from flask import send_file, request



settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.route('/', methods=['GET'])
@login_required
def index():
    if current_user.role != 'admin':
        flash('Acesso negado.', 'error')
        return redirect(url_for('main.index'))
        
    categories = Category.query.all()
    app_settings = AppSettings.query.first()
    if not app_settings:
        app_settings = AppSettings()
        db.session.add(app_settings)
        db.session.commit()
        
    # Buscar usuários encontrados na sessão (se houver)
    ad_users_found = session.get('ad_users_found', [])
    
    # Verificar quais usuários já existem no sistema
    existing_usernames = set(User.query.with_entities(User.username).all())
    existing_usernames = {u[0] for u in existing_usernames}
    
    existing_emails = set(User.query.with_entities(User.email).all())
    existing_emails = {e[0] for e in existing_emails}
    
    # Marcar usuários que já existem
    for user in ad_users_found:
        user['exists'] = user['username'] in existing_usernames or user['email'] in existing_emails
    
    # Agrupar usuários por prefixo (ex: DNP001 -> DNP)
    grouped_users = {}
    for user in ad_users_found:
        prefix = user['username'][:3].upper() if user['username'] and len(user['username']) >= 3 else 'Outros'
        if prefix not in grouped_users:
            grouped_users[prefix] = []
        grouped_users[prefix].append(user)
        
    # Ordenar grupos e usuários dentro dos grupos
    sorted_groups = sorted(grouped_users.items())
    for prefix in grouped_users:
        grouped_users[prefix] = sorted(grouped_users[prefix], key=lambda x: x['display_name'])

    # Obter aba ativa da query string
    active_tab = request.args.get('tab', 'categories')
        
    return render_template('settings.html', 
                         categories=categories, 
                         settings=app_settings,
                         ad_users_found=ad_users_found,
                         grouped_ad_users=sorted_groups,
                         active_tab=active_tab,
                         now=datetime.utcnow())

@settings_bp.route('/categories', methods=['POST'])
@login_required
def create_category():
    if current_user.role != 'admin':
        return redirect(url_for('main.index'))
        
    name = request.form.get('name')
    if name:
        if Category.query.filter_by(name=name).first():
            flash('Categoria já existe.', 'error')
        else:
            new_cat = Category(name=name)
            db.session.add(new_cat)
            db.session.commit()
            flash('Categoria criada com sucesso.', 'success')
    return redirect(url_for('settings.index', tab='ad'))

@settings_bp.route('/categories/<int:id>/delete', methods=['POST'])
@login_required
def delete_category(id):
    if current_user.role != 'admin':
        return redirect(url_for('main.index'))
        
    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    flash('Categoria removida.', 'success')
    return redirect(url_for('settings.index', tab='ad'))

@settings_bp.route('/ad-config', methods=['POST'])
@login_required
def update_ad_config():
    if current_user.role != 'admin':
        return redirect(url_for('main.index'))
        
    app_settings = AppSettings.query.first()
    if not app_settings:
        app_settings = AppSettings()
        db.session.add(app_settings)
   
    app_settings.ad_server = request.form.get('ad_server', '').strip()
    app_settings.ad_domain = request.form.get('ad_domain', '').strip()
    app_settings.ad_base_dn = request.form.get('ad_base_dn', '').strip()
    user_dn_input = request.form.get('ad_user_dn', '').strip()
    app_settings.ad_user_dn = user_dn_input
    
    # Tratar senha: se campo foi preenchido, atualizar; se vazio e usuário foi removido, limpar senha
    password_input = request.form.get('ad_user_password', '').strip()
    if password_input:
        # Senha foi fornecida, atualizar
        app_settings.ad_user_password = password_input
    elif not user_dn_input:
        # Se usuário foi removido, limpar senha também
        app_settings.ad_user_password = None
    # Se campo está vazio mas usuário ainda existe, manter senha anterior (não atualizar)
    
    db.session.commit()
    flash('Configurações do AD salvas.', 'success')
    return redirect(url_for('settings.index', tab='ad'))

@settings_bp.route('/sla-config', methods=['POST'])
@login_required
def update_sla_config():
    if current_user.role != 'admin':
        return redirect(url_for('main.index'))
    
    app_settings = AppSettings.query.first()
    if not app_settings:
        app_settings = AppSettings()
        db.session.add(app_settings)
    
    try:
        app_settings.sla_hours_baixa = int(request.form.get('sla_hours_baixa', 48))
        app_settings.sla_hours_media = int(request.form.get('sla_hours_media', 24))
        app_settings.sla_hours_alta = int(request.form.get('sla_hours_alta', 8))
        app_settings.sla_hours_critica = int(request.form.get('sla_hours_critica', 4))
        
        db.session.commit()
        flash('Configurações de SLA salvas.', 'success')
    except ValueError:
        flash('Valores inválidos para SLA (use apenas números inteiros).', 'error')
        
    return redirect(url_for('settings.index', tab='sla'))

def _get_ad_connection(app_settings):
    """Helper function to create LDAP connection to AD"""
    if not app_settings or not app_settings.ad_server:
        raise ValueError('Servidor AD não configurado')
    
    # Criar servidor LDAP
    server = ldap3.Server(app_settings.ad_server, get_info=ldap3.ALL)
    
    # Preparar credenciais de bind
    user = None
    password = None
    authentication = ldap3.ANONYMOUS
    
    # Se usuário foi fornecido, preparar autenticação
    if app_settings.ad_user_dn and app_settings.ad_user_dn.strip():
        user = app_settings.ad_user_dn.strip()
        password = app_settings.ad_user_password
        
        # Se não há senha salva ou senha está vazia, não usar autenticação
        if not password or not str(password).strip():
            # Se usuário foi fornecido mas sem senha, usar conexão anônima
            user = None
            authentication = ldap3.ANONYMOUS
        else:
            password = str(password).strip()
            authentication = ldap3.SIMPLE
            
            # Se o usuário está apenas como username (sem @ e sem DN), tentar construir UPN
            if '@' not in user and ',' not in user and app_settings.ad_domain:
                # Construir formato UPN automaticamente
                user = f'{user}@{app_settings.ad_domain}'
    
    # Criar conexão
    conn = ldap3.Connection(
        server,
        user=user,
        password=password if password else None,
        authentication=authentication,
        auto_bind=True,
        raise_exceptions=False
    )
    
    # Verificar se a conexão foi bem-sucedida
    if not conn.bound:
        error_msg = conn.result.get('description', 'Erro desconhecido')
        error_code = conn.result.get('result', '')
        
        # Mensagens de erro mais amigáveis
        if 'invalidCredentials' in str(error_msg) or error_code == 49:
            if user and password:
                # Tentar formatos alternativos se ainda não tentamos
                if '@' in user:
                    # Já tentamos UPN, tentar DN se possível
                    suggested_format = f'CN={user.split("@")[0]},CN=Users,{app_settings.ad_base_dn or ""}'
                else:
                    # Tentar UPN se tiver domínio
                    if app_settings.ad_domain:
                        suggested_format = f'{user}@{app_settings.ad_domain}'
                    else:
                        suggested_format = f'CN={user},CN=Users,DC=...'
                
                raise ConnectionError(
                    f'Credenciais inválidas. Verifique:\n'
                    f'- Usuário: {user}\n'
                    f'- Se a senha está correta\n'
                    f'- Se a conta não está bloqueada ou desabilitada\n'
                    f'- Tente usar formato UPN: {suggested_format if "@" not in user else "ou formato DN completo"}'
                )
            elif user and not password:
                raise ConnectionError(
                    'Usuário fornecido mas senha está vazia. '
                    'Forneça a senha ou deixe ambos vazios para conexão anônima.'
                )
            else:
                raise ConnectionError('Falha na autenticação. O servidor pode não permitir conexão anônima.')
        else:
            conn.unbind()
            raise ConnectionError(f'Falha ao conectar ao AD: {error_msg} (código: {error_code})')
    
    return conn

def _search_ad_users(app_settings, search_term=None):
    """Busca usuários no Active Directory"""
    conn = None
    try:
        conn = _get_ad_connection(app_settings)
        
        # Priorizar Base DN configurado pelo usuário
        base_dn = app_settings.ad_base_dn or ''
        
        # Se não houver Base DN, tentar construir a partir do domínio
        if not base_dn and app_settings.ad_domain:
            base_dn = ','.join([f'DC={part}' for part in app_settings.ad_domain.split('.')])
            
        if not base_dn:
            raise ValueError('Base DN não configurado. Por favor, configure o Base DN ou o Domínio nas configurações do AD.')
        
        # Filtro para buscar usuários (pessoas com conta habilitada e que não sejam contas de computador)
        # !(sAMAccountName=*$) exclui contas de máquina via LDAP
        base_active_filter = '(&(objectCategory=person)(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2))(!(sAMAccountName=*$)))'
        
        if search_term:
            search_filter = f'(&{base_active_filter}(|(displayName=*{search_term}*)(sAMAccountName=*{search_term}*)(mail=*{search_term}*)))'
        else:
            search_filter = base_active_filter
        
        # Atributos a serem retornados
        attributes = ['sAMAccountName', 'mail', 'cn', 'displayName', 'userPrincipalName', 'givenName', 'sn', 'userAccountControl']

        
        # Realizar busca
        success = conn.search(
            search_base=base_dn,
            search_filter=search_filter,
            search_scope=ldap3.SUBTREE,
            attributes=attributes,
            size_limit=1000
        )
        
        if not success:
            error_msg = conn.result.get('description', 'Erro desconhecido na busca')
            error_code = conn.result.get('result', '')
            raise ConnectionError(f'Falha ao buscar usuários: {error_msg} (código: {error_code})')
        
        users = []
        for entry in conn.entries:
            try:
                # Extrair informações do usuário
                username = str(entry.sAMAccountName) if hasattr(entry, 'sAMAccountName') and entry.sAMAccountName else None
                
                # IGNORAR se não houver username ou se for conta de máquina (termina com $) ou contiver $
                if not username or '$' in username:
                    continue

                email = str(entry.mail) if hasattr(entry, 'mail') and entry.mail else None
                first_name = str(entry.givenName) if hasattr(entry, 'givenName') and entry.givenName else ''
                last_name = str(entry.sn) if hasattr(entry, 'sn') and entry.sn else ''
                user_account_control = int(str(entry.userAccountControl)) if hasattr(entry, 'userAccountControl') and entry.userAccountControl else 0

                # Verificar se a conta está ativa (bit ACCOUNTDISABLE não está definido)
                # No AD, o bit 2 (valor 2) do userAccountControl indica conta desativada
                if user_account_control & 2:
                    continue


                full_name = f'{first_name} {last_name}'.strip()
                if not full_name:
                    full_name = str(entry.displayName) if hasattr(entry, 'displayName') and entry.displayName else str(entry.cn) if hasattr(entry, 'cn') and entry.cn else username or ''
                
                upn = str(entry.userPrincipalName) if hasattr(entry, 'userPrincipalName') and entry.userPrincipalName else None
                
                if not email and upn:
                    email = upn
                
                if not email:
                    if app_settings.ad_domain:
                        email = f'{username}@{app_settings.ad_domain}'
                    else:
                        email = f'{username}@local'
                
                if username:
                    users.append({
                        'username': username,
                        'email': email,
                        'display_name': full_name,
                        'first_name': first_name,
                        'last_name': last_name,
                        'dn': str(entry.entry_dn) if hasattr(entry, 'entry_dn') else ''
                    })
            except Exception as e:
                continue
        
        return users
        
    finally:
        if conn:
            try:
                conn.unbind()
            except:
                pass

@settings_bp.route('/ad-clear-search', methods=['POST'])
@login_required
def clear_ad_search():
    """Limpa os resultados da busca do AD da sessão"""
    session.pop('ad_users_found', None)
    flash('Busca limpa com sucesso.', 'info')
    return redirect(url_for('settings.index', tab='ad'))


@settings_bp.route('/ad-sync', methods=['POST'])
@login_required
def sync_ad():
    """Busca usuários do AD e mostra para importação"""
    if current_user.role != 'admin':
        return redirect(url_for('main.index'))

    app_settings = AppSettings.query.first()
    if not app_settings or not app_settings.ad_server:
        flash('Configure o servidor AD primeiro.', 'error')
        return redirect(url_for('settings.index', tab='ad'))

    try:
        session.pop('ad_users_found', None) # Limpar busca anterior
        
        search_query = request.form.get('search_query', '').strip()
        users = _search_ad_users(app_settings, search_term=search_query if search_query else None)
        
        if not users:
            flash('Nenhum usuário ativo encontrado no AD. Possíveis causas:\n- Base DN incorreto\n- Filtro muito restritivo\n- Nenhum usuário habilitado no servidor\n- Permissões insuficientes para buscar usuários', 'warning')
            return redirect(url_for('settings.index', tab='ad'))
        
        # Armazenar usuários encontrados na sessão para importação manual
        session['ad_users_found'] = users
        
        flash(f'✅ SUCESSO! {len(users)} usuário(s) ativo(s) encontrado(s) no AD. Selecione para importar.', 'success')
        
    except Exception as e:
        # Limpar sessão em caso de erro
        session.pop('ad_users_found', None)
        flash(f'Erro ao buscar usuários no AD: {str(e)}', 'error')

    return redirect(url_for('settings.index', tab='ad'))

@settings_bp.route('/ad-import-single', methods=['POST'])
@login_required
def import_single_ad_user():
    if current_user.role != 'admin':
        flash('Acesso negado. Apenas administradores podem importar usuários.', 'danger')
        return redirect(url_for('main.index'))

    username_to_import = request.form.get('username')
    if not username_to_import:
        flash('Nome de usuário não fornecido para importação.', 'error')
        return redirect(url_for('settings.index', tab='ad'))

    ad_users_found = session.get('ad_users_found', [])
    user_data_to_import = next((user for user in ad_users_found if user['username'] == username_to_import), None)

    if not user_data_to_import:
        flash(f'Usuário "{username_to_import}" não encontrado na última busca do AD ou já importado.', 'error')
        return redirect(url_for('settings.index', tab='ad'))

    try:
        username = user_data_to_import['username']
        email = user_data_to_import['email']
        display_name = user_data_to_import['display_name']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash(f'Usuário "{username}" já existe no sistema.', 'warning')
            return redirect(url_for('settings.index', tab='ad'))

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash(f'E-mail "{email}" já cadastrado para outro usuário.', 'warning')
            return redirect(url_for('settings.index', tab='ad'))

        new_user = User(
            username=username,
            email=email,
            fullname=display_name, # Adicionar o fullname ao novo usuário
            role='user'
        )
        # Usar o username como senha inicial (usuários podem alterar depois)
        new_user.set_password(username)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash(f'Usuário "{display_name}" ({username}) importado com sucesso! Senha inicial: {username}', 'success')
        
        session['ad_users_found'] = [user for user in ad_users_found if user['username'] != username_to_import]

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao importar usuário "{username_to_import}": {str(e)}', 'error')

    return redirect(url_for('settings.index', tab='ad'))

@settings_bp.route('/ad-import-all', methods=['POST'])
@login_required
def import_all_ad_users():
    if current_user.role != 'admin':
        flash('Acesso negado. Apenas administradores podem importar usuários.', 'danger')
        return redirect(url_for('main.index'))

    ad_users_found = session.get('ad_users_found', [])
    if not ad_users_found:
        flash('Nenhum usuário encontrado na sessão para importar.', 'warning')
        return redirect(url_for('settings.index', tab='ad'))

    imported_count = 0
    skipped_count = 0
    errors = []

    for user_data_to_import in ad_users_found:
        try:
            username = user_data_to_import['username']
            email = user_data_to_import['email']
            display_name = user_data_to_import['display_name']

            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                skipped_count += 1
                continue

            existing_email = User.query.filter_by(email=email).first()
            if existing_email:
                skipped_count += 1
                continue

            new_user = User(
                username=username,
                email=email,
                fullname=display_name,
                role='user'
            )
            # Usar o username como senha inicial (usuários podem alterar depois)
            new_user.set_password(username)

            db.session.add(new_user)
            imported_count += 1
             
        except Exception as e:
            errors.append(f'{user_data_to_import.get("username", "desconhecido")}: {str(e)}')
            skipped_count += 1

    try:
        db.session.commit()
        if imported_count > 0:
            flash(f'✅ SUCESSO! {imported_count} usuário(s) importado(s) do AD com senha inicial igual ao username!', 'success')
        if skipped_count > 0:
            flash(f'{skipped_count} usuário(s) ignorado(s) (já existem no sistema ou com erro).', 'warning')
        if errors:
            flash(f'Erros na importação de alguns usuários: {"; ".join(errors[:3])}', 'error')
        
        # Limpar a sessão após a importação de todos
        session.pop('ad_users_found', None)
             
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao importar todos os usuários: {str(e)}', 'error')

    return redirect(url_for('settings.index', tab='ad'))

@settings_bp.route('/ad-bulk-import', methods=['POST'])
@login_required
def bulk_import_ad_users():
    """Busca e importa todos os usuários ativos do AD de uma vez"""
    if current_user.role != 'admin':
        return redirect(url_for('main.index'))

    app_settings = AppSettings.query.first()
    if not app_settings or not app_settings.ad_server:
        flash('Configure o servidor AD primeiro.', 'error')
        return redirect(url_for('settings.index', tab='ad'))

    try:
        # Busca TODOS os usuários ativos (search_term=None)
        ad_users = _search_ad_users(app_settings, search_term=None)
        
        if not ad_users:
            flash('Nenhum usuário ativo encontrado para importar.', 'warning')
            return redirect(url_for('settings.index', tab='ad'))

        imported_count = 0
        skipped_count = 0
        
        for user_data in ad_users:
            username = user_data['username']
            email = user_data['email']
            display_name = user_data['display_name']

            # Verifica se já existe
            if User.query.filter((User.username == username) | (User.email == email)).first():
                skipped_count += 1
                continue

            try:
                new_user = User(
                    username=username,
                    email=email,
                    fullname=display_name,
                    role='user'
                )
                new_user.set_password(username)
                db.session.add(new_user)
                imported_count += 1
            except:
                skipped_count += 1

        db.session.commit()
        flash(f'✅ SUCESSO! {imported_count} usuários importados. {skipped_count} já existiam ou foram ignorados.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro na importação em massa: {str(e)}', 'error')

    return redirect(url_for('settings.index', tab='ad'))

@settings_bp.route('/backup', methods=['GET'])
@login_required
def export_backup():
    if current_user.role != 'admin':
        flash('Acesso negado.', 'error')
        return redirect(url_for('main.index'))

        
    # Caminhos
    root_dir = os.path.abspath(os.path.join(current_app.root_path, os.pardir))
    instance_path = os.path.join(root_dir, 'instance')
    uploads_path = current_app.config['UPLOAD_FOLDER']
    
    # Criar ZIP em memória
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Adicionar banco de dados
        if os.path.exists(instance_path):
            for root, dirs, files in os.walk(instance_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.join('instance', file)
                    zf.write(file_path, arcname)
        
        # Adicionar uploads
        if os.path.exists(uploads_path):
            for root, dirs, files in os.walk(uploads_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.join('app/uploads', file)
                    zf.write(file_path, arcname)
                    
    memory_file.seek(0)
    filename = f"helpdesk_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=filename
    )

@settings_bp.route('/restore', methods=['POST'])
@login_required
def restore_backup():
    if current_user.role != 'admin':
        flash('Acesso negado.', 'error')
        return redirect(url_for('main.index'))
        
    file = request.files.get('backup_file')
    if not file or not file.filename.endswith('.zip'):
        flash('Por favor, selecione um arquivo .ZIP de backup válido.', 'error')
        return redirect(url_for('settings.index', tab='backup'))
        
    restore_db = request.form.get('restore_db') == 'on'
    restore_uploads = request.form.get('restore_uploads') == 'on'
    
    if not restore_db and not restore_uploads:
        flash('Selecione ao menos um item para restaurar (Banco de Dados ou Anexos).', 'warning')
        return redirect(url_for('settings.index', tab='backup'))
        
    try:
        import tempfile
        import sqlite3
        from app.models.user import User
        from app.models.ticket import Ticket, Attachment, Comment, TicketItem
        from app.models.settings import Category, AppSettings, Item

        temp_extract_path = os.path.join(tempfile.gettempdir(), 'temp_restore')
        
        if os.path.exists(temp_extract_path):
            shutil.rmtree(temp_extract_path)
        os.makedirs(temp_extract_path, exist_ok=True)
        
        with zipfile.ZipFile(file, 'r') as zf:
            zf.extractall(temp_extract_path)
            
        if restore_db:
            db_source = os.path.join(temp_extract_path, 'instance', 'helpdesk.db')
            if os.path.exists(db_source):
                # Se o banco atual for Postgres (Supabase), fazemos a migração de dados
                if db.engine.name == 'postgresql':
                    flash('Detectado banco de dados remoto. Iniciando migração de dados do SQLite...', 'info')
                    
                    # Conectar ao SQLite temporário
                    sqlite_conn = sqlite3.connect(db_source)
                    sqlite_conn.row_factory = sqlite3.Row
                    cursor = sqlite_conn.cursor()

                    def get_rows(table_name):
                        try:
                            cursor.execute(f"SELECT * FROM {table_name}")
                            return cursor.fetchall()
                        except:
                            return []

                    # 1. Limpar dados atuais (Muito mais rápido que drop_all no Postgres)
                    db.session.execute(text('TRUNCATE TABLE users, ticket, comment, attachment, category, item, ticket_item, app_settings RESTART IDENTITY CASCADE'))
                    db.session.commit()
                    
                    # Garante que a estrutura básica existe (caso alguma tabela falte)
                    db.create_all()

                    # 2. Migrar Categorias
                    for row in get_rows('category'):
                        db.session.add(Category(id=row['id'], name=row['name']))
                    db.session.commit()

                    # 3. Migrar Usuários (Ajustando nome da tabela de 'user' para 'users')
                    for row in get_rows('user'):
                        u = User(id=row['id'], username=row['username'], email=row['email'], 
                                 fullname=row['fullname'], password_hash=row['password_hash'], 
                                 role=row['role'])
                        db.session.add(u)
                    db.session.commit()
                    
                    # 4. Migrar Itens do Inventário
                    for row in get_rows('item'):
                        it = Item(id=row['id'], name=row['name'], description=row['description'],
                                  category=row['category'], quantity=row['quantity'], 
                                  min_quantity=row['min_quantity'], unit_cost=row['unit_cost'],
                                  location=row['location'], supplier=row['supplier'])
                        db.session.add(it)
                    db.session.commit()

                    # 5. Migrar Tickets (Chamados)
                    for row in get_rows('ticket'):
                        t = Ticket(id=row['id'], title=row['title'], description=row['description'],
                                   category=row['category'], priority=row['priority'], status=row['status'],
                                   created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                                   user_id=row['user_id'], assigned_to_id=row['assigned_to_id'])
                        db.session.add(t)
                    db.session.commit()

                    # 6. Migrar Itens Usados, Comentários e Anexos
                    for row in get_rows('ticket_item'):
                        db.session.add(TicketItem(id=row['id'], ticket_id=row['ticket_id'], item_id=row['item_id'], quantity_used=row['quantity_used']))
                    for row in get_rows('comment'):
                        db.session.add(Comment(id=row['id'], content=row['content'], user_id=row['user_id'], ticket_id=row['ticket_id']))
                    for row in get_rows('attachment'):
                        db.session.add(Attachment(id=row['id'], filename=row['filename'], original_filename=row['original_filename'], ticket_id=row['ticket_id']))
                    
                    db.session.commit()
                    sqlite_conn.close()
                    flash('Migração de dados SQLite para Supabase concluída com sucesso!', 'success')
                else:
                    # Se for banco local, apenas copia o arquivo (comportamento antigo)
                    db_dest = os.path.join(os.path.abspath(os.path.join(current_app.root_path, os.pardir)), 'instance', 'helpdesk.db')
                    db.session.remove()
                    db.engine.dispose()
                    shutil.copy2(db_source, db_dest)
                    flash('Banco de Dados SQLite restaurado.', 'success')
            else:
                flash('Arquivo de banco de dados não encontrado no ZIP.', 'error')
                
        if restore_uploads:
            # Lógica de uploads continua a mesma (armazenamento temporário na Vercel)
            uploads_source = os.path.join(temp_extract_path, 'app', 'uploads')
            uploads_dest = current_app.config['UPLOAD_FOLDER']
            if os.path.exists(uploads_source):
                if os.path.exists(uploads_dest): shutil.rmtree(uploads_dest)
                shutil.copytree(uploads_source, uploads_dest)
                flash('Anexos restaurados temporariamente.', 'success')
                
        shutil.rmtree(temp_extract_path)
    except Exception as e:
        db.session.rollback()
        flash(f'Erro durante a restauração/migração: {str(e)}', 'error')
        
    return redirect(url_for('settings.index', tab='backup'))

        
    return redirect(url_for('settings.index', tab='backup'))

@settings_bp.route('/ad-import', methods=['POST'])


@login_required
def import_ad_users():
    return redirect(url_for('settings.index', tab='ad')) # Rota desabilitada, importação é automática
