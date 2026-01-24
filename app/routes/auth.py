# app/routes/auth.py - VERSÃO ATUALIZADA PARA ACEITAR EMAIL OU CPF

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from app.models.user import User
from app import db
from sqlalchemy.exc import OperationalError, DatabaseError
import logging
import time

# Configurar logger
logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

def handle_database_error(operation="operação"):
    """Trata erros de conexão com o banco de dados"""
    logger.error(f"Erro de conexão com banco durante {operation}")
    flash('Erro temporário no sistema. Tente novamente em alguns instantes.', 'danger')

def safe_db_query(query_func, max_retries=3, delay=1):
    """Executa query com retry automático em caso de erro SSL"""
    for attempt in range(max_retries):
        try:
            return query_func()
        except (OperationalError, DatabaseError) as e:
            logger.warning(f"Tentativa {attempt + 1} falhou: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(delay * (attempt + 1))  # Backoff exponencial
                try:
                    db.session.rollback()
                except:
                    pass
            else:
                raise e

def buscar_usuario_por_email_ou_cpf(login_input):
    """Busca usuário por email ou CPF"""
    def buscar():
        login_input_clean = login_input.strip().lower()
        
        # Se contém @, é email
        if '@' in login_input_clean:
            return User.query.filter_by(email=login_input_clean).first()
        else:
            # É CPF - limpar formatação
            cpf_limpo = ''.join(filter(str.isdigit, login_input))
            
            if len(cpf_limpo) >= 11:
                # Tentar primeiro com CPF limpo
                user = User.query.filter_by(cpf=cpf_limpo).first()
                if user:
                    return user
                
                # Se não encontrar, tentar com CPF formatado original
                return User.query.filter_by(cpf=login_input).first()
            else:
                # Pode ser username se não for CPF válido
                return User.query.filter_by(username=login_input_clean).first()
    
    return safe_db_query(buscar)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Verificar se usuário já está autenticado
    try:
        if current_user.is_authenticated:
            # Tentar verificar se precisa mudar senha
            try:
                if current_user.needs_password_change():
                    return redirect(url_for('auth.change_password'))
            except (OperationalError, DatabaseError):
                handle_database_error("verificação de senha")
                pass  # Continuar normalmente se der erro
            return redirect(url_for('main.index'))
    except (OperationalError, DatabaseError):
        # Se der erro ao verificar autenticação, continuar para o login
        pass
    
    if request.method == 'POST':
        email_ou_cpf = request.form.get('email', '').strip()  # Campo aceita email OU CPF
        password = request.form.get('password', '').strip()
        
        # Validação básica
        if not email_ou_cpf or not password:
            flash('Por favor, preencha email/CPF e senha.', 'warning')
            return render_template('auth/login.html')
        
        try:
            # Buscar usuário por email OU CPF
            user = buscar_usuario_por_email_ou_cpf(email_ou_cpf)
            
            # Verificar credenciais
            if user and user.check_password(password):
                # Verificar se usuário está ativo
                if not user.is_active:
                    flash('Sua conta está temporariamente suspensa. Entre em contato com o suporte para mais informações.', 'danger')
                    return render_template('auth/login.html')
                
                # Fazer login do usuário
                try:
                    login_user(user, remember=request.form.get('remember', False))
                
                    # ✅ Atualizar sequência de dias (logo após login_user)
                    try:
                        user.atualizar_sequencia()
                    except Exception as e:
                        current_app.logger.error(
                            f"Erro ao atualizar sequência: {e}"
                        )

                    # Verificar se precisa mudar senha
                    try:
                        if user.needs_password_change():
                            flash('Como este é seu primeiro acesso, você precisa alterar sua senha.', 'warning')
                            return redirect(url_for('auth.change_password'))
                    except (OperationalError, DatabaseError):
                        logger.warning("Erro ao verificar necessidade de mudança de senha")
                        # Continuar mesmo com erro


                    #-------------ROLETA------------------------------------
                    #from app.models.roleta import RoletaPrimeiroAcesso
                    #roleta_check = RoletaPrimeiroAcesso.query.filter_by(user_id=user.id).first()
                    #if not roleta_check:
                        # Primeiro acesso - redirecionar para roleta
                     #   flash('Bem-vindo! Você tem direito a girar nossa roleta de prêmios!', 'success')
                     #   return redirect(url_for('roleta.primeiro_acesso'))
                    #---------------------------------------------------------



                   #---------------------------------------------------------
                    # Redirecionar para próxima página
                    next_page = request.args.get('next')
                    flash('Login realizado com sucesso!', 'success')
                    return redirect(next_page or url_for('main.index'))
                    
                except Exception as e:
                    logger.error(f"Erro ao fazer login: {e}")
                    flash('Erro interno durante login. Tente novamente.', 'danger')
                    return render_template('auth/login.html')
            else:
                # Credenciais inválidas - mensagem amigável para Kiwify
                if '@' in email_ou_cpf:
                    flash('Email ou senha inválidos.', 'warning')
                else:
                    flash('CPF ou senha inválidos. Se acabou de comprar, use seu CPF como senha inicial.', 'warning')
                
        except (OperationalError, DatabaseError) as e:
            logger.error(f"Erro de banco no login: {e}")
            handle_database_error("login")
            
        except Exception as e:
            logger.error(f"Erro inesperado no login: {e}")
            flash('Erro interno do sistema. Tente novamente.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    try:
        logout_user()
        flash('Logout realizado com sucesso.', 'success')
    except Exception as e:
        logger.error(f"Erro no logout: {e}")
        # Continuar com logout mesmo com erro
    return redirect(url_for('main.index'))

@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('main.index'))
    except (OperationalError, DatabaseError):
        pass  # Ignorar erro de verificação
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        nome_completo = request.form.get('nome_completo', '').strip()
        password = request.form.get('password', '').strip()
        cpf = request.form.get('cpf', '').strip()
        telefone = request.form.get('telefone', '').strip()

        # Validação básica
        if not all([username, email, nome_completo, password, telefone]):
            flash('Por favor, preencha todos os campos obrigatórios.', 'warning')
            return render_template('auth/registro.html')
        
        try:
            # Verificar se usuário já existe
            def verificar_usuario_existente():
                return User.query.filter((User.username == username) | 
                                       (User.email == email)).first()
            
            user_exists = safe_db_query(verificar_usuario_existente)
            
            if user_exists:
                flash('Nome de usuário ou email já cadastrado.', 'warning')
                return render_template('auth/registro.html')
            
            # Criar novo usuário
            user = User(
                username=username, 
                email=email, 
                nome_completo=nome_completo, 
                is_active=True,
                cpf=cpf,
                telefone=telefone,
                password_changed=True
            )
            user.set_password(password)
            
            # Salvar no banco com retry
            def salvar_usuario():
                db.session.add(user)
                db.session.commit()
                return True
            
            safe_db_query(salvar_usuario)
            
            flash('Cadastro realizado com sucesso! Faça login para continuar.', 'success')
            return redirect(url_for('auth.login'))
            
        except (OperationalError, DatabaseError) as e:
            logger.error(f"Erro de banco no registro: {e}")
            db.session.rollback()
            handle_database_error("cadastro")
            
        except Exception as e:
            logger.error(f"Erro inesperado no registro: {e}")
            db.session.rollback()
            flash('Erro interno durante cadastro. Tente novamente.', 'danger')
    
    return render_template('auth/registro.html')

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    try:
        # Verificar se realmente precisa mudar senha
        if not current_user.needs_password_change() and not request.args.get('force'):
            return redirect(url_for('main.index'))
    except (OperationalError, DatabaseError):
        logger.warning("Erro ao verificar necessidade de mudança de senha")
        # Continuar assumindo que precisa mudar
    
    if request.method == 'POST':
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # Validações básicas
        if not all([current_password, new_password, confirm_password]):
            flash('Por favor, preencha todos os campos.', 'danger')
            return render_template('auth/change_password.html')
        
        # Verificar senha atual
        try:
            if not current_user.check_password(current_password):
                flash('Senha atual incorreta.', 'danger')
                return render_template('auth/change_password.html')
        except Exception as e:
            logger.error(f"Erro ao verificar senha atual: {e}")
            flash('Erro ao verificar senha atual. Tente novamente.', 'danger')
            return render_template('auth/change_password.html')
        
        # Validar nova senha
        if len(new_password) < 6:
            flash('A nova senha deve ter pelo menos 6 caracteres.', 'danger')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('As senhas não coincidem.', 'danger')
            return render_template('auth/change_password.html')
        
        # Verificar se não é igual ao CPF
        try:
            if hasattr(current_user, 'cpf') and current_user.cpf and new_password == current_user.cpf:
                flash('A nova senha não pode ser igual ao seu CPF.', 'danger')
                return render_template('auth/change_password.html')
        except (OperationalError, DatabaseError):
            logger.warning("Erro ao verificar CPF")
            # Continuar sem verificação de CPF
        
        # Atualizar senha
        try:
            def atualizar_senha():
                current_user.set_password(new_password)
                current_user.password_changed = True
                db.session.commit()
                return True
            
            safe_db_query(atualizar_senha)
            
            flash('Senha alterada com sucesso!', 'success')
            return redirect(url_for('main.index'))
            
        except (OperationalError, DatabaseError) as e:
            logger.error(f"Erro de banco ao alterar senha: {e}")
            db.session.rollback()
            handle_database_error("alteração de senha")
            
        except Exception as e:
            logger.error(f"Erro inesperado ao alterar senha: {e}")
            db.session.rollback()
            flash('Erro interno ao alterar senha. Tente novamente.', 'danger')
    
    try:
        forced = current_user.needs_password_change()
    except (OperationalError, DatabaseError):
        forced = True  # Assumir que precisa mudar se der erro
        
    return render_template('auth/change_password.html', forced=forced)

# ====================================================
# 📧 ROTA: RECUPERAÇÃO DE SENHA (VERSÃO COMPLETA)
# ====================================================
@auth_bp.route('/recuperar-senha', methods=['GET', 'POST'])
def recuperar_senha():
    """Rota para usuários que esqueceram a senha"""
    if request.method == 'POST':
        email_ou_cpf = request.form.get('email', '').strip()
        
        if not email_ou_cpf:
            flash('Por favor, informe seu email ou CPF.', 'warning')
            return render_template('auth/recuperar_senha.html')
        
        try:
            # Buscar usuário
            user = buscar_usuario_por_email_ou_cpf(email_ou_cpf)
            
            if user:
                # ========================================
                # 🔑 GERAR TOKEN E ENVIAR EMAIL
                # ========================================
                token = user.generate_reset_token()
                
                if token:
                    # Importar serviço de email
                    from app.services.email_service import EmailService
                    
                    # Enviar email com link de reset
                    sucesso, mensagem = EmailService.enviar_email_reset_senha(
                        user.email,
                        user.nome_completo or user.email.split('@')[0],
                        token
                    )
                    
                    if sucesso:
                        logger.info(f"📧 Email de reset enviado para {user.email}")
                    else:
                        logger.error(f"❌ Falha ao enviar email: {mensagem}")
                else:
                    logger.error(f"❌ Falha ao gerar token para {user.email}")
            
            # Sempre mostrar mesma mensagem (segurança)
            flash('✅ Se o email/CPF estiver cadastrado, você receberá um link para redefinir sua senha. Verifique sua caixa de entrada e spam.', 'info')
            
        except Exception as e:
            logger.error(f"Erro na recuperação de senha: {e}")
            flash('Erro temporário. Tente novamente em alguns instantes.', 'danger')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/recuperar_senha.html')


# ====================================================
# 🔐 ROTA: RESET DE SENHA COM TOKEN (NOVA)
# ====================================================
@auth_bp.route('/reset-senha/<token>', methods=['GET', 'POST'])
def reset_senha(token):
    """Rota para redefinir senha usando token"""
    
    # Buscar usuário pelo token
    user = User.find_by_reset_token(token)
    
    if not user:
        flash('❌ Link inválido ou expirado. Solicite um novo link de recuperação.', 'danger')
        return redirect(url_for('auth.recuperar_senha'))
    
    # Validar token
    if not user.validate_reset_token(token):
        flash('⏰ Este link expirou. Por segurança, os links são válidos por apenas 30 minutos. Solicite um novo link.', 'warning')
        return redirect(url_for('auth.recuperar_senha'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # Validações
        if not all([new_password, confirm_password]):
            flash('Por favor, preencha todos os campos.', 'danger')
            return render_template('auth/reset_senha.html', token=token)
        
        if len(new_password) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'danger')
            return render_template('auth/reset_senha.html', token=token)
        
        if new_password != confirm_password:
            flash('As senhas não coincidem.', 'danger')
            return render_template('auth/reset_senha.html', token=token)
        
        # Verificar se não é igual ao CPF
        try:
            if hasattr(user, 'cpf') and user.cpf:
                cpf_limpo = ''.join(filter(str.isdigit, user.cpf))
                if new_password == cpf_limpo:
                    flash('A nova senha não pode ser igual ao seu CPF.', 'danger')
                    return render_template('auth/reset_senha.html', token=token)
        except Exception as e:
            logger.warning(f"Erro ao verificar CPF: {e}")
        
        try:
            # Definir nova senha
            user.set_password(new_password)
            user.password_changed = True
            user.clear_reset_token()
            
            db.session.commit()
            
            logger.info(f"✅ Senha redefinida com sucesso para {user.email}")
            flash('✅ Senha alterada com sucesso! Faça login com sua nova senha.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            logger.error(f"Erro ao redefinir senha: {e}")
            db.session.rollback()
            flash('Erro ao redefinir senha. Tente novamente.', 'danger')
    
    return render_template('auth/reset_senha.html', token=token)


# Handler de erro para toda a aplicação
@auth_bp.app_errorhandler(500)
def handle_internal_error(error):
    """Trata erros 500 de forma amigável"""
    logger.error(f"Erro interno: {error}")
    db.session.rollback()
    flash('Ocorreu um erro interno. Tente novamente em alguns instantes.', 'danger')
    return render_template('auth/login.html'), 500
