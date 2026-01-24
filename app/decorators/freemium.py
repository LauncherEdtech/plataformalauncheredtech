"""
Decorators para verificar limites freemium - VERSÃO ESTÁVEL (sem redirecionamento em loop)
Mostra modal sem travar a navegação.
"""
from functools import wraps
from flask import jsonify, request, render_template
from flask_login import current_user
import logging

logger = logging.getLogger(__name__)

# 🔹 Função genérica de bloqueio
def _resposta_bloqueio(tipo, mensagem):
    """Garante retorno adequado sem redirecionamento."""
    logger.info(f"[FREEMIUM] Bloqueio: tipo={tipo}, user_id={getattr(current_user, 'id', None)}")

    # AJAX / fetch → retorna JSON
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': False,
            'show_modal': True,
            'tipo_limite': tipo,
            'message': mensagem
        }), 403

    # Requisição normal → renderiza página simples que chama o modal
    return render_template('freemium/bloqueio.html', tipo=tipo, mensagem=mensagem), 403


# ------------------- DECORATORS -------------------

def requer_aula_disponivel(f):
    """Decorator para verificar se pode assistir aula"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        pode, mensagem = current_user.pode_assistir_aula
        if not pode:
            return _resposta_bloqueio('aula', mensagem)
        return f(*args, **kwargs)
    return decorated_function


def requer_simulado_disponivel(f):
    """Decorator para verificar se pode fazer simulado"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        pode, mensagem = current_user.pode_fazer_simulado
        if not pode:
            return _resposta_bloqueio('simulado', mensagem)
        return f(*args, **kwargs)
    return decorated_function


def requer_redacao_disponivel(f):
    """Decorator para verificar se pode fazer redação"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        pode, mensagem = current_user.pode_fazer_redacao
        if not pode:
            return _resposta_bloqueio('redacao', mensagem)
        return f(*args, **kwargs)
    return decorated_function


# ------------------- CHECK AUXILIAR -------------------

def check_freemium_limit(tipo_limite):
    """Função auxiliar para verificar limites programaticamente"""
    if tipo_limite == 'redacao':
        return current_user.pode_fazer_redacao
    elif tipo_limite == 'simulado':
        return current_user.pode_fazer_simulado
    elif tipo_limite == 'aula':
        return current_user.pode_assistir_aula
    else:
        return False, "Tipo de limite inválido"
