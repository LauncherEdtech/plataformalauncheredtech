from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Rota principal sem loop de redirect"""
    if current_user.is_authenticated:
        # Usuário logado - vai para dashboard
        return redirect(url_for('dashboard.index'))
    else:
        # Usuário não logado - mostra página inicial ou vai para login
        return redirect(url_for('auth.login'))

@main_bp.route('/home')
def home():
    """Página inicial pública"""
    return render_template('index.html')
