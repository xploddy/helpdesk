from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.user import User
from app.extensions import db

users_bp = Blueprint('users', __name__)

@users_bp.before_request
@login_required
def admin_required():
    if current_user.role != 'admin':
        flash('Acesso negado. Apenas administradores podem acessar esta página.', 'danger')
        return redirect(url_for('main.index'))

@users_bp.route('/users')
def list_users():
    search_query = request.args.get('search_query', '').strip()

    if search_query:
        users = User.query.filter(
            User.username.ilike(f'%{search_query}%') | 
            User.email.ilike(f'%{search_query}%') |
            User.fullname.ilike(f'%{search_query}%')
        ).all()
    else:
        users = User.query.all()
    
    # Agrupar usuários por prefixo (ex: DNP001 -> DNP)
    grouped_users = {}
    for user in users:
        prefix = user.username[:3].upper() if user.username and len(user.username) >= 3 else 'Outros'
        if prefix not in grouped_users:
            grouped_users[prefix] = []
        grouped_users[prefix].append(user)
        
    # Ordenar grupos e usuários dentro dos grupos
    sorted_groups = sorted(grouped_users.items())
    for prefix in grouped_users:
        grouped_users[prefix] = sorted(grouped_users[prefix], key=lambda x: x.username)

    # Stats for summary cards
    total_users = User.query.count()
    admin_count = User.query.filter_by(role='admin').count()
    regular_count = User.query.filter_by(role='user').count()

    return render_template('users/list.html', 
                          users=users, 
                          grouped_users=sorted_groups, 
                          search_query=search_query,
                          stats={'total': total_users, 'admins': admin_count, 'regulars': regular_count})

@users_bp.route('/users/create', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        fullname = request.form.get('fullname', '').strip() or None
        password = request.form['password']
        role = request.form['role']
        
        is_technician = 'is_technician' in request.form
        
        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já existe.', 'error')
            return redirect(url_for('users.create_user'))
        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado.', 'error')
            return redirect(url_for('users.create_user'))
            
        user = User(username=username, email=email, fullname=fullname, role=role, is_technician=is_technician)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Usuário criado com sucesso!', 'success')
        return redirect(url_for('users.list_users'))
        
    return render_template('users/edit.html', title="Novo Usuário")

@users_bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
def edit_user(id):
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        user.fullname = request.form.get('fullname', '').strip() or None
        user.role = request.form['role']
        user.is_technician = 'is_technician' in request.form
        
        if request.form['password']:
            user.set_password(request.form['password'])
            
        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('users.list_users'))
        
    return render_template('users/edit.html', user=user, title="Editar Usuário")

@users_bp.route('/users/<int:id>/delete', methods=['POST'])
def delete_user(id):
    from app.models.ticket import Ticket, Comment
    
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('Você não pode excluir a si mesmo.', 'warning')
        return redirect(url_for('users.list_users'))
    
    # Verificar relacionamentos antes de deletar
    tickets_count = Ticket.query.filter_by(user_id=user.id).count()
    tickets_assigned_count = Ticket.query.filter_by(assigned_to_id=user.id).count()
    comments_count = Comment.query.filter_by(user_id=user.id).count()
    
    # Se houver tickets criados pelo usuário, não permitir exclusão
    if tickets_count > 0:
        flash(f'Não é possível excluir este usuário pois ele possui {tickets_count} ticket(s) criado(s).', 'error')
        return redirect(url_for('users.list_users'))
    
    try:
        # Remover atribuições de tickets (apenas assigned_to_id, não deletar tickets)
        if tickets_assigned_count > 0:
            Ticket.query.filter_by(assigned_to_id=user.id).update({'assigned_to_id': None})
            db.session.commit()
        
        # Deletar comentários do usuário ANTES de deletar o usuário
        if comments_count > 0:
            Comment.query.filter_by(user_id=user.id).delete()
            db.session.commit()
        
        # Agora pode deletar o usuário
        db.session.delete(user)
        db.session.commit()
        flash('Usuário excluído com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir usuário: {str(e)}', 'error')
    
    return redirect(url_for('users.list_users'))

@users_bp.route('/users/delete_all_non_admin', methods=['POST'])
@login_required
def delete_all_non_admin_users():
    if current_user.role != 'admin':
        flash('Acesso negado. Apenas administradores podem usar esta função.', 'danger')
        return redirect(url_for('main.index'))
    
    from app.models.ticket import Ticket, Comment

    try:
        # Obter todos os usuários que não são administradores
        non_admin_users = User.query.filter(User.role != 'admin').all()
        
        deleted_count = 0
        for user_to_delete in non_admin_users:
            # Verificar se o usuário possui tickets criados (para evitar quebra de histórico)
            if user_to_delete.tickets_created.count() > 0:
                flash(f'Não foi possível excluir o usuário {user_to_delete.username} porque ele possui tickets criados.', 'warning')
                continue
                
            # Desassociar tickets atribuídos a este usuário
            Ticket.query.filter_by(assigned_to_id=user_to_delete.id).update({'assigned_to_id': None})
            
            # Deletar comentários do usuário
            Comment.query.filter_by(user_id=user_to_delete.id).delete()

            db.session.delete(user_to_delete)
            deleted_count += 1

        db.session.commit()
        flash(f'{deleted_count} usuários não-administradores foram excluídos com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir usuários não-administradores: {str(e)}', 'error')

    return redirect(url_for('users.list_users'))
