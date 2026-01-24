from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, User

#linha abixo modificado por conta do sheets
from sheets import add_user_to_sheet

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')  # Novo campo
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já existe.','error'  ) #'error' editado
            return redirect(url_for('auth_bp.register'))
        
        new_user = User(username=username, email=email, phone=phone)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()


	
   	#Linha abixo modificada Após salvar novo usuário
        #add_user_to_sheet(new_user)
        add_user_to_sheet(new_user)  # <- Agora será executado
        flash('Registro realizado com sucesso!', 'success') #'success' editado
        return redirect(url_for('auth_bp.login'))
    
	#Linha abixo modificada Após salvar novo usuário
	#add_user_to_sheet(new_user)

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
#        username = request.form.get('username')
        username_or_email = request.form.get('username')  # o campo pode aceitar email ou username
        password = request.form.get('password')
        
 #      user = User.query.filter_by(username=username).first()
    
        user = User.query.filter(
   	    (User.username == username_or_email) | (User.email == username_or_email)
	).first()

    
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciais inválidas.', 'error') #, 'error' editado
    
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('auth_bp.login'))
