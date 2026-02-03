from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.settings import Category
from flask_login import login_required, current_user
from app.models.ticket import Ticket, Comment, Attachment, TicketItem
from app.models.user import User
from app.extensions import db
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from flask import current_app, send_from_directory
from sqlalchemy import or_, cast, String

tickets_bp = Blueprint('tickets', __name__)

@tickets_bp.route('/tickets/create', methods=['GET', 'POST'])
@login_required
def create_ticket():
    if request.method == 'POST':
        title = request.form['title']
        category_name = request.form['category']
        priority = request.form['priority']
        description = request.form['description']
        
        # User and Observers assignment (only for admins)
        user_id = current_user.id
        if current_user.role == 'admin':
            selected_user_id = request.form.get('user_id')
            if selected_user_id:
                user_id = int(selected_user_id)
        
        observer_ids = request.form.getlist('observer_ids')
        
        # SLA Calculation
        from app.models.settings import AppSettings
        from datetime import timedelta
        
        app_settings = AppSettings.query.first()
        sla_hours = 24 # Default
        if app_settings:
            p_clean = priority.lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')
            if 'baixa' in p_clean: sla_hours = app_settings.sla_hours_baixa or 48
            elif 'media' in p_clean: sla_hours = app_settings.sla_hours_media or 24
            elif 'alta' in p_clean: sla_hours = app_settings.sla_hours_alta or 8
            elif 'critica' in p_clean or 'urgente' in p_clean: sla_hours = app_settings.sla_hours_critica or 4
            
        due_at = datetime.utcnow() + timedelta(hours=sla_hours)


        ticket = Ticket(
            title=title,
            category=category_name,
            priority=priority,
            description=description,
            user_id=user_id,
            due_at=due_at
        )
        
        # Add observers
        if observer_ids:
            observer_users = User.query.filter(User.id.in_([int(id) for id in observer_ids])).all()
            ticket.observers.extend(observer_users)

        db.session.add(ticket)
        db.session.commit() # Commit first to get ticket ID

        # Handle attachment (Multiple)
        files = request.files.getlist('attachment')
        for file in files:
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                # Timestamp to avoid collisions
                unique_filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
                
                attachment = Attachment(
                    filename=unique_filename,
                    original_filename=filename,
                    ticket_id=ticket.id
                )
                db.session.add(attachment)
        db.session.commit()

        flash('Chamado criado com sucesso!', 'success')
        return redirect(url_for('main.index'))
    
    categories = Category.query.all()
    # Fallback if no categories exist
    if not categories:
        categories = [] # Let the user create their own
    
    # Get all users for admin to select (as author or observer)
    users = User.query.all()
    users.sort(key=lambda u: (u.fullname or u.username).lower())
    
    # Prepare users for JSON serialization (needed for Alpine.js search)
    users_json = []
    for u in users:
        users_json.append({
            'id': u.id,
            'username': u.username,
            'fullname': u.fullname or u.username
        })
        
    return render_template('tickets/create.html', 
                          categories=categories, 
                          users=users,
                          users_json=users_json)


@tickets_bp.route('/tickets/<int:id>/delete', methods=['POST'])
@login_required
def delete_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    if current_user.role != 'admin':
        if ticket.user_id != current_user.id:
            flash('Você não tem permissão para excluir este chamado.', 'danger')
            return redirect(url_for('tickets.view_ticket', id=id))
        
        if ticket.assigned_to_id is not None or ticket.status in ['Resolvido', 'Fechado', 'Em andamento']:
            flash('Este chamado não pode ser excluído pois já está em atendimento ou resolvido.', 'warning')
            return redirect(url_for('tickets.view_ticket', id=id))
        
    db.session.delete(ticket)
    db.session.commit()
    flash('Chamado excluído com sucesso.', 'success')
    return redirect(url_for('tickets.list_tickets'))

@tickets_bp.route('/tickets')
@login_required
def list_tickets():
    query = Ticket.query
    
    # Permission check or filtering
    if current_user.role != 'admin':
        # Show tickets created by user OR assigned to user OR where user is observer
        query = query.filter(
            or_(
                Ticket.user_id == current_user.id,
                Ticket.assigned_to_id == current_user.id,
                Ticket.observers.any(User.id == current_user.id)
            )
        )

    # Search Filters
    q = request.args.get('q')
    status = request.args.get('status')
    priority = request.args.get('priority')

    if q:
        query = query.filter(or_(
            Ticket.title.ilike(f'%{q}%'),
            Ticket.description.ilike(f'%{q}%'),
            cast(Ticket.id, String).ilike(f'%{q}%')
        ))
    
    if status and status != 'Todos':
        query = query.filter_by(status=status)
        
    if priority and priority != 'Todas':
        query = query.filter_by(priority=priority)

    # Pagination
    page = request.args.get('page', 1, type=int)
    tickets = query.order_by(Ticket.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    
    return render_template('tickets/list.html', tickets=tickets)

@tickets_bp.route('/tickets/<int:id>')
@login_required
def view_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    # Observer check
    is_observer = current_user in ticket.observers
    
    if current_user.role != 'admin' and ticket.user_id != current_user.id and not is_observer:
        flash('Você não tem permissão para visualizar este chamado.', 'danger')
        return redirect(url_for('tickets.list_tickets'))
    
    technicians = User.query.filter((User.role == 'admin') | (User.is_technician == True)).all()
    used_items = TicketItem.query.filter_by(ticket_id=id).all()
    
    users = User.query.all()
    users.sort(key=lambda u: (u.fullname or u.username).lower())
    
    available_items = []
    if current_user.role == 'admin':
        from app.models.settings import Item
        available_items = Item.query.filter(Item.quantity > 0).order_by(Item.category, Item.name).all()
    
    # Prepare users for JSON serialization (needed for Alpine.js search)
    users_json = []
    for u in users:
        users_json.append({
            'id': u.id,
            'username': u.username,
            'fullname': u.fullname or u.username
        })
    
    return render_template('tickets/view.html', 
                         ticket=ticket, 
                         technicians=technicians, 
                         users=users,
                         users_json=users_json,
                         used_items=used_items,
                         available_items=available_items,
                         now=datetime.utcnow())


@tickets_bp.route('/tickets/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    if current_user.role != 'admin' and ticket.user_id != current_user.id:
        flash('Você não tem permissão para editar este chamado.', 'danger')
        return redirect(url_for('tickets.view_ticket', id=id))

    if request.method == 'POST':
        priority = request.form['priority']
        # Recalculate SLA if priority changed
        if ticket.priority != priority:
             from app.models.settings import AppSettings
             from datetime import timedelta
             app_settings = AppSettings.query.first()
             sla_hours = 24
             if app_settings:
                p_clean = priority.lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')
                if 'baixa' in p_clean: sla_hours = app_settings.sla_hours_baixa or 48
                elif 'media' in p_clean: sla_hours = app_settings.sla_hours_media or 24
                elif 'alta' in p_clean: sla_hours = app_settings.sla_hours_alta or 8
                elif 'critica' in p_clean or 'urgente' in p_clean: sla_hours = app_settings.sla_hours_critica or 4
             
             # Calculate from CREATION date or NOW? Usually from creation, but if changed late?
             # Let's keep it simple: update due date based on NOW if priority changes, OR recalculate from created_at
             # Better: Recalculate from Created At to respect original timeline
             ticket.due_at = ticket.created_at + timedelta(hours=sla_hours)

        ticket.title = request.form['title']
        ticket.category = request.form['category']
        ticket.priority = priority
        ticket.description = request.form['description']
        
        # User assignment (only for admins)
        if current_user.role == 'admin':
            selected_user_id = request.form.get('user_id')
            if selected_user_id:
                ticket.user_id = int(selected_user_id)
        
        # Observers assignment
        observer_ids = request.form.getlist('observer_ids')
        ticket.observers = [] # Clear existing
        if observer_ids:
            observer_users = User.query.filter(User.id.in_([int(id) for id in observer_ids])).all()
            ticket.observers.extend(observer_users)
        
        # Handle attachment (Multiple)
        files = request.files.getlist('attachment')
        for file in files:
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                unique_filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
                
                attachment = Attachment(
                    filename=unique_filename,
                    original_filename=filename,
                    ticket_id=ticket.id
                )
                db.session.add(attachment)

        ticket.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Chamado atualizado com sucesso!', 'success')
        return redirect(url_for('tickets.view_ticket', id=id))

    # Get all users for selection
    users = User.query.all()
    users.sort(key=lambda u: (u.fullname or u.username).lower())
    
    categories = Category.query.all()
    # Prepare users for JSON serialization (needed for Alpine.js search)
    users_json = []
    for u in users:
        users_json.append({
            'id': u.id,
            'username': u.username,
            'fullname': u.fullname or u.username
        })
        
    return render_template('tickets/edit.html', 
                          ticket=ticket, 
                          users=users, 
                          users_json=users_json,
                          categories=categories)


@tickets_bp.route('/uploads/<filename>')
@login_required
def download_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@tickets_bp.route('/tickets/<int:id>/status', methods=['POST'])
@login_required
def update_status(id):
    if current_user.role != 'admin':
        flash('Apenas administradores podem alterar o status.', 'danger')
        return redirect(url_for('tickets.view_ticket', id=id))
    
    ticket = Ticket.query.get_or_404(id)
    new_status = request.form['status']
    ticket.status = new_status
    
    if new_status in ['Resolvido', 'Fechado']:
        ticket.resolved_at = datetime.utcnow()
    else:
        ticket.resolved_at = None
        
    db.session.commit()
    flash('Status atualizado com sucesso!', 'success')
    return redirect(url_for('tickets.view_ticket', id=id))

@tickets_bp.route('/tickets/<int:id>/resolve', methods=['GET', 'POST'])
@login_required
def resolve_ticket(id):
    if current_user.role != 'admin':
        flash('Apenas administradores podem resolver chamados.', 'danger')
        return redirect(url_for('tickets.view_ticket', id=id))
    
    ticket = Ticket.query.get_or_404(id)
    from app.models.settings import Item
    
    if request.method == 'POST':
        # Atualizar status
        ticket.status = 'Resolvido'
        ticket.resolved_at = datetime.utcnow()
        
        # Processar itens usados
        used_items = request.form.getlist('used_items[]')
        quantities = request.form.getlist('quantities[]')
        notes_list = request.form.getlist('notes[]')
        
        for i, item_id in enumerate(used_items):
            if item_id and quantities[i]:
                item = Item.query.get(int(item_id))
                if item:
                    quantity_used = int(quantities[i])
                    
                    # Verificar se há estoque suficiente
                    if item.quantity >= quantity_used:
                        # Criar registro de item usado
                        ticket_item = TicketItem(
                            ticket_id=ticket.id,
                            item_id=int(item_id),
                            quantity_used=quantity_used,
                            notes=notes_list[i] if i < len(notes_list) else None
                        )
                        db.session.add(ticket_item)
                        
                        # Atualizar quantidade em estoque
                        item.quantity -= quantity_used
                        db.session.add(item)
                    else:
                        flash(f'Estoque insuficiente para o item "{item.name}". Disponível: {item.quantity}', 'warning')
        
        db.session.commit()
        flash('Chamado resolvido com sucesso!', 'success')
        return redirect(url_for('tickets.view_ticket', id=id))
    
    # GET request - mostrar formulário de resolução
    available_items = Item.query.filter(Item.quantity > 0).order_by(Item.category, Item.name).all()
    
    return render_template('tickets/resolve.html', ticket=ticket, available_items=available_items)

@tickets_bp.route('/tickets/<int:id>/comment', methods=['POST'])
@login_required
def add_comment(id):
    ticket = Ticket.query.get_or_404(id)
    content = request.form.get('content')
    
    if not content:
        flash('O comentário não pode estar vazio.', 'warning')
        return redirect(url_for('tickets.view_ticket', id=id))

    comment = Comment(content=content, user_id=current_user.id, ticket_id=ticket.id)
    db.session.add(comment)
    ticket.updated_at = datetime.utcnow() # Update ticket timestamp
    db.session.commit()
    flash('Comentário adicionado.', 'success')
    return redirect(url_for('tickets.view_ticket', id=id))
@tickets_bp.route('/tickets/<int:id>/assign', methods=['POST'])
@login_required
def assign_technician(id):
    if current_user.role != 'admin':
        flash('Apenas administradores podem atribuir técnicos.', 'danger')
        return redirect(url_for('tickets.view_ticket', id=id))
    
    ticket = Ticket.query.get_or_404(id)
    technician_id = request.form.get('technician_id')
    
    if technician_id:
        ticket.assigned_to_id = int(technician_id)
        ticket.assigned_by_id = current_user.id # Track who assigned
        db.session.commit()
        flash('Técnico atribuído com sucesso!', 'success')
    else:
        flash('Por favor, selecione um técnico.', 'warning')
        
    return redirect(url_for('tickets.view_ticket', id=id))
@tickets_bp.route('/tickets/<int:id>/reopen', methods=['POST'])
@login_required
def reopen_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    
    # Only the author or an admin can reopen
    if current_user.role != 'admin' and ticket.user_id != current_user.id:
        flash('Você não tem permissão para reabrir este chamado.', 'danger')
        return redirect(url_for('tickets.view_ticket', id=id))
    
    if ticket.status not in ['Resolvido', 'Fechado']:
        flash('Este chamado não pode ser reaberto pois não está resolvido ou fechado.', 'warning')
        return redirect(url_for('tickets.view_ticket', id=id))
    
    ticket.status = 'Aberto'
    ticket.resolved_at = None
    ticket.updated_at = datetime.utcnow()
    
    # Add a system comment about reopening
    reopen_comment = Comment(
        content=f"Chamado reaberto pelo usuário {current_user.username}.",
        user_id=current_user.id,
        ticket_id=ticket.id
    )
    db.session.add(reopen_comment)
    
    db.session.commit()
    flash('Chamado reaberto com sucesso.', 'success')
    return redirect(url_for('tickets.view_ticket', id=id))

@tickets_bp.route('/tickets/<int:id>/add-item', methods=['POST'])
@login_required
def add_ticket_item(id):
    if current_user.role != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('tickets.view_ticket', id=id))
    
    ticket = Ticket.query.get_or_404(id)
    item_id = request.form.get('item_id')
    quantity = int(request.form.get('quantity', 1))
    notes = request.form.get('notes', '')
    
    from app.models.settings import Item
    item = Item.query.get_or_404(item_id)
    
    if item.quantity >= quantity:
        ticket_item = TicketItem(
            ticket_id=ticket.id,
            item_id=item.id,
            quantity_used=quantity,
            notes=notes
        )
        item.quantity -= quantity
        db.session.add(ticket_item)
        db.session.commit()
        flash(f'Item "{item.name}" adicionado ao chamado.', 'success')
    else:
        flash(f'Estoque insuficiente para "{item.name}".', 'error')
        
    return redirect(url_for('tickets.view_ticket', id=id))

@tickets_bp.route('/ticket-item/<int:item_id>/delete', methods=['POST'])
@login_required
def remove_ticket_item(item_id):
    if current_user.role != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    ticket_item = TicketItem.query.get_or_404(item_id)
    ticket_id = ticket_item.ticket_id
    
    # Restore stock
    from app.models.settings import Item
    item = Item.query.get(ticket_item.item_id)
    if item:
        item.quantity += ticket_item.quantity_used
        
    db.session.delete(ticket_item)
    db.session.commit()
    
    flash('Item removido do chamado e estoque restaurado.', 'success')
    return redirect(url_for('tickets.view_ticket', id=ticket_id))

@tickets_bp.route('/comment/<int:comment_id>/edit', methods=['POST'])
@login_required
def edit_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if current_user.id != comment.user_id and current_user.role != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('tickets.view_ticket', id=comment.ticket_id))
    
    content = request.form.get('content')
    if content:
        comment.content = content
        db.session.commit()
        flash('Comentário atualizado.', 'success')
    return redirect(url_for('tickets.view_ticket', id=comment.ticket_id))

@tickets_bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    ticket_id = comment.ticket_id
    if current_user.id != comment.user_id and current_user.role != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('tickets.view_ticket', id=ticket_id))
    
    db.session.delete(comment)
    db.session.commit()
    flash('Comentário removido.', 'success')
    return redirect(url_for('tickets.view_ticket', id=ticket_id))

@tickets_bp.route('/tickets/<int:id>/observers/add', methods=['POST'])
@login_required
def add_observer(id):
    if current_user.role != 'admin':
        flash('Apenas administradores podem gerenciar observadores.', 'danger')
        return redirect(url_for('tickets.view_ticket', id=id))
        
    ticket = Ticket.query.get_or_404(id)
    user_id = request.form.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        if user and user not in ticket.observers:
            ticket.observers.append(user)
            db.session.commit()
            flash(f'{user.fullname or user.username} adicionado como observador.', 'success')
    return redirect(url_for('tickets.view_ticket', id=id))

@tickets_bp.route('/tickets/<int:id>/observers/remove/<int:user_id>', methods=['POST'])
@login_required
def remove_observer(id, user_id):
    if current_user.role != 'admin':
        flash('Apenas administradores podem gerenciar observadores.', 'danger')
        return redirect(url_for('tickets.view_ticket', id=id))
        
    ticket = Ticket.query.get_or_404(id)
    user = User.query.get_or_404(user_id)
    if user in ticket.observers:
        ticket.observers.remove(user)
        db.session.commit()
        flash(f'{user.fullname or user.username} removido dos observadores.', 'success')
    return redirect(url_for('tickets.view_ticket', id=id))
