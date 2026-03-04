# app/routes/onboarding.py
"""
Rotas API para controle do sistema de onboarding
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
import logging

logger = logging.getLogger(__name__)

onboarding_bp = Blueprint('onboarding', __name__, url_prefix='/api/onboarding')

# Importar funções do serviço
from app.services.onboarding_service import (
    iniciar_onboarding,
    obter_etapa_atual,
    avancar_etapa,
    ativar_tour_completo,
    verificar_onboarding_ativo,
    pular_onboarding,
    finalizar_onboarding_permanente
)


@onboarding_bp.route('/status', methods=['GET'])
@login_required
def status():
    """
    Retorna o status do onboarding do usuário atual
    
    Response:
        {
            "ativo": bool,
            "etapa_atual": int,
            "dados_etapa": {...}
        }
    """
    try:
        logger.info(f"📊 Verificando status do onboarding para user_id={current_user.id}")
        
        ativo = verificar_onboarding_ativo(current_user.id)
        logger.info(f"✅ Onboarding ativo: {ativo}")
        
        if not ativo:
            return jsonify({
                'ativo': False,
                'mensagem': 'Onboarding não ativo'
            })
        
        dados_etapa = obter_etapa_atual(current_user.id)
        logger.info(f"📍 Dados da etapa: {dados_etapa.get('status', 'unknown')}")
        
        return jsonify({
            'ativo': True,
            **dados_etapa
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter status: {e}", exc_info=True)
        return jsonify({
            'status': 'erro',
            'mensagem': str(e)
        }), 500


@onboarding_bp.route('/iniciar', methods=['POST'])
@login_required
def iniciar():
    """
    Inicia o onboarding para o usuário atual
    
    Response:
        {
            "status": "iniciado",
            "etapa": 1,
            "dados_etapa": {...}
        }
    """
    try:
        resultado = iniciar_onboarding(current_user.id)
        
        if resultado['status'] == 'erro':
            return jsonify(resultado), 400
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao iniciar onboarding: {e}")
        return jsonify({
            'status': 'erro',
            'mensagem': str(e)
        }), 500


@onboarding_bp.route('/avancar', methods=['POST'])
@login_required
def avancar():
    """
    Avança para a próxima etapa após completar uma ação
    
    Request Body:
        {
            "acao": "nome_da_acao"
        }
    
    Response:
        {
            "status": "ativo" | "basico_finalizado" | "tour_completo_finalizado",
            "etapa": int,
            "dados_etapa": {...},
            "recompensa": {...}
        }
    """
    try:
        data = request.get_json()
        acao = data.get('acao')
        
        if not acao:
            return jsonify({
                'status': 'erro',
                'mensagem': 'Ação não especificada'
            }), 400
        
        resultado = avancar_etapa(current_user.id, acao)
        
        if resultado['status'] == 'erro':
            return jsonify(resultado), 400
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao avançar etapa: {e}")
        return jsonify({
            'status': 'erro',
            'mensagem': str(e)
        }), 500


@onboarding_bp.route('/ativar-tour-completo', methods=['POST'])
@login_required
def ativar_tour():
    """
    Ativa o tour completo após o usuário escolher fazer
    
    Response:
        {
            "status": "ativo",
            "etapa": 6,
            "dados_etapa": {...}
        }
    """
    try:
        resultado = ativar_tour_completo(current_user.id)
        
        if resultado['status'] == 'erro':
            return jsonify(resultado), 400
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao ativar tour completo: {e}")
        return jsonify({
            'status': 'erro',
            'mensagem': str(e)
        }), 500


@onboarding_bp.route('/pular', methods=['POST'])
@login_required
def pular():
    """
    Adia o onboarding por 7 dias
    ✅ NÃO finaliza permanentemente
    """
    try:
        data = request.get_json() or {}
        dias = data.get('dias', 7)  # Padrão: 7 dias
        
        resultado = pular_onboarding(current_user.id, dias_adiar=dias)
        
        if resultado['status'] == 'erro':
            return jsonify(resultado), 400
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao pular onboarding: {e}")
        return jsonify({
            'status': 'erro',
            'mensagem': str(e)
        }), 500

# ==================== ROTAS PARA DETECÇÃO DE AÇÕES ====================

@onboarding_bp.route('/detectar/cronograma-criado', methods=['POST'])
@login_required
def detectar_cronograma():
    """
    Endpoint chamado quando um cronograma é criado
    Avança automaticamente a etapa se o usuário estiver no onboarding
    """
    try:
        if not verificar_onboarding_ativo(current_user.id):
            return jsonify({'onboarding_ativo': False})
        
        resultado = avancar_etapa(current_user.id, 'criar_cronograma')
        
        return jsonify({
            'onboarding_ativo': True,
            **resultado
        })
        
    except Exception as e:
        logger.error(f"Erro ao detectar cronograma criado: {e}")
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@onboarding_bp.route('/detectar/aula-assistida', methods=['POST'])
@login_required
def detectar_aula():
    """
    Endpoint chamado quando o usuário assiste 2min de uma aula
    """
    try:
        if not verificar_onboarding_ativo(current_user.id):
            return jsonify({'onboarding_ativo': False})
        
        resultado = avancar_etapa(current_user.id, 'assistir_aula')
        
        return jsonify({
            'onboarding_ativo': True,
            **resultado
        })
        
    except Exception as e:
        logger.error(f"Erro ao detectar aula assistida: {e}")
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@onboarding_bp.route('/detectar/diagnostico-concluido', methods=['POST'])
@login_required
def detectar_diagnostico():
    """
    Endpoint chamado quando o diagnóstico é concluído
    """
    try:
        if not verificar_onboarding_ativo(current_user.id):
            return jsonify({'onboarding_ativo': False})
        
        resultado = avancar_etapa(current_user.id, 'concluir_diagnostico')
        
        return jsonify({
            'onboarding_ativo': True,
            **resultado
        })
        
    except Exception as e:
        logger.error(f"Erro ao detectar diagnóstico concluído: {e}")
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@onboarding_bp.route('/detectar/post-criado', methods=['POST'])
@login_required
def detectar_post():
    """
    Endpoint chamado quando um post é criado no HelpZone
    """
    try:
        if not verificar_onboarding_ativo(current_user.id):
            return jsonify({'onboarding_ativo': False})
        
        resultado = avancar_etapa(current_user.id, 'criar_post')
        
        return jsonify({
            'onboarding_ativo': True,
            **resultado
        })
        
    except Exception as e:
        logger.error(f"Erro ao detectar post criado: {e}")
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500



@onboarding_bp.route('/finalizar-permanente', methods=['POST'])
@login_required
def finalizar_permanente():
    """
    Finaliza o onboarding PERMANENTEMENTE
    Usado no botão "Começar a Estudar" da etapa 5
    """
    try:
        resultado = finalizar_onboarding_permanente(current_user.id)
        
        if resultado['status'] == 'erro':
            return jsonify(resultado), 400
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao finalizar onboarding: {e}")
        return jsonify({
            'status': 'erro',
            'mensagem': str(e)
        }), 500
