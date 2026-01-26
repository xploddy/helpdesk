from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app.models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and not request.is_json:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.form.get('username')
            password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        
        if user is None or not user.check_password(password):
            if request.is_json:
                return {'message': 'Usuário ou senha inválidos'}, 401
            flash('Usuário ou senha inválidos', 'error')
            return redirect(url_for('auth.login'))
        
        login_user(user)
        
        if request.is_json:
            return {
                'message': 'Login realizado com sucesso',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'role': user.role,
                    'fullname': user.fullname
                }
            }, 200

        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('main.index')
        return redirect(next_page)
        
    return render_template('auth/login.html', title='Sign In')

@auth_bp.route('/logout')
def logout():
    logout_user()
    if request.is_json:
        return {'message': 'Logout realizado com sucesso'}, 200
    return redirect(url_for('auth.login'))

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    return {
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'role': current_user.role,
            'fullname': current_user.fullname
        }
    }, 200

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        
        if not current_user.check_password(current_password):
            flash('Senha atual incorreta.', 'error')
            return redirect(url_for('auth.change_password'))
            
        current_user.set_password(new_password)
        from app.extensions import db
        db.session.commit()
        flash('Senha alterada com sucesso.', 'success')
        return redirect(url_for('main.index'))
        
    return render_template('auth/change_password.html')
