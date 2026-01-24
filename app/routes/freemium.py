# app/routes/freemium.py
from flask import Blueprint, render_template
from flask_login import login_required, current_user

freemium_bp = Blueprint('freemium', __name__, url_prefix='/freemium')

@freemium_bp.route('/planos')
def planos():
    """Página de planos"""
    return render_template('freemium/planos.html')
