from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user
from flask import current_app

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return render_template('home.html')

@main_bp.route('/sobre')
def sobre():
    return render_template('sobre.html')

@main_bp.route('/modulos')
def modulos():
    return render_template('modulos.html')