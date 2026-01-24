# app/routes/api_freemium.py

# ========================================
# CONTROLE FREEMIUM - MODO CAMPANHA
# ========================================
FREEMIUM_ATIVO = False

"""
API endpoints para verificar status freemium do usuário
VERSÃO CORRIGIDA com logs detalhados e tratamento de erro robusto
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
import logging
import traceback

logger = logging.getLogger(__name__)

api_freemium_bp = Blueprint('api_freemium', __name__, url_prefix='/api/freemium')

@api_freemium_bp.route('/status', methods=['GET'])
@login_required
def status():
    """
    Retorna o status atual do plano e limites do usuário
    Usado para verificações via JavaScript/AJAX
    """
    try:
        logger.info(f"[FREEMIUM] Verificando status para usuário {current_user.id}")
        
        pode_redacao, msg_redacao = current_user.pode_fazer_redacao
        pode_simulado, msg_simulado = current_user.pode_fazer_simulado
        pode_aula, msg_aula = current_user.pode_assistir_aula
        
        status_data = {
            'success': True,
            'tem_plano_ativo': current_user.tem_plano_ativo,
            'plano_ativo': current_user.plano_ativo,
            'status_plano': current_user.status_plano_display,
            
            # Limites e status
            'pode_fazer_redacao': pode_redacao,
            'pode_fazer_simulado': pode_simulado,
            'pode_assistir_aula': pode_aula,
            
            # Contadores
            'redacoes_restantes': current_user.redacoes_gratuitas_restantes,
            'simulados_restantes': current_user.simulados_gratuitos_restantes,
            'aulas_restantes': current_user.aulas_gratuitas_restantes,
            
            # Mensagens
            'mensagem_redacao': msg_redacao,
            'mensagem_simulado': msg_simulado,
            'mensagem_aula': msg_aula,
            
            # Roleta
            'pode_resgatar_roleta': current_user.pode_resgatar_roleta,
            
            # Links de upgrade
            'links': {
                'plano_mensal': 'https://pay.kiwify.com.br/jCQpKD3',
                'plano_anual': 'https://pay.kiwify.com.br/SVj90JQ',
                'taxa_resgate': 'https://pay.kiwify.com.br/2HipOfz'
            }
        }
        
        # Se tiver plano ativo, adicionar data de expiração
        if current_user.tem_plano_ativo and current_user.data_expiracao_plano:
            from datetime import datetime
            dias_restantes = (current_user.data_expiracao_plano - datetime.utcnow()).days
            status_data['dias_restantes_plano'] = dias_restantes
            status_data['data_expiracao'] = current_user.data_expiracao_plano.isoformat()
        
        logger.info(f"[FREEMIUM] Status retornado com sucesso para usuário {current_user.id}")
        return jsonify(status_data)
        
    except Exception as e:
        logger.error(f"[FREEMIUM] Erro ao buscar status para usuário {current_user.id}: {e}")
        logger.error(f"[FREEMIUM] Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Erro ao buscar status'
        }), 500




@api_freemium_bp.route('/verificar/<tipo>', methods=['GET'])
@login_required
def verificar_limite(tipo):
    """
    Verifica um tipo específico de limite
    Tipos: redacao, simulado, aula
    """
    try:
        # ⚠️ MODO CAMPANHA - Libera tudo automaticamente
        if not FREEMIUM_ATIVO:
            logger.info(f"[CAMPANHA] Freemium desabilitado - acesso liberado para {tipo}")
            return jsonify({
                'success': True,
                'pode_acessar': True,
                'mensagem': None,
                'restantes': 999,
                'tipo': tipo.lower(),
                'tem_plano_ativo': False,
                'mostrar_modal': False
            })
        
        # Código normal continua...
        logger.info(f"[FREEMIUM] Verificando limite '{tipo}' para usuário {current_user.id}")
        logger.info(f"[FREEMIUM] Plano ativo: {current_user.plano_ativo}, Tem plano: {current_user.tem_plano_ativo}")
        
        tipo = tipo.lower()
        
        if tipo == 'redacao':
            pode, mensagem = current_user.pode_fazer_redacao
            restantes = current_user.redacoes_gratuitas_restantes
            logger.info(f"[FREEMIUM] Redação - Pode: {pode}, Restantes: {restantes}")
        elif tipo == 'simulado':
            pode, mensagem = current_user.pode_fazer_simulado
            restantes = current_user.simulados_gratuitos_restantes
            logger.info(f"[FREEMIUM] Simulado - Pode: {pode}, Restantes: {restantes}")
        elif tipo == 'aula':
            pode, mensagem = current_user.pode_assistir_aula
            restantes = current_user.aulas_gratuitas_restantes
            logger.info(f"[FREEMIUM] Aula - Pode: {pode}, Restantes: {restantes}, Mensagem: {mensagem}")
        else:
            logger.warning(f"[FREEMIUM] Tipo inválido solicitado: {tipo}")
            return jsonify({
                'success': False,
                'error': 'Tipo inválido. Use: redacao, simulado ou aula'
            }), 400
        
        response_data = {
            'success': True,
            'pode_acessar': pode,
            'mensagem': mensagem,
            'restantes': restantes,
            'tipo': tipo,
            'tem_plano_ativo': current_user.tem_plano_ativo,
            'mostrar_modal': not pode and not current_user.tem_plano_ativo
        }
        
        logger.info(f"[FREEMIUM] Resposta para usuário {current_user.id}: {response_data}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"[FREEMIUM] Erro ao verificar limite '{tipo}' para usuário {current_user.id}: {e}")
        logger.error(f"[FREEMIUM] Traceback: {traceback.format_exc()}")
        
        # Retornar erro estruturado
        return jsonify({
            'success': False,
            'error': 'Erro ao verificar limite',
            'pode_acessar': False,
            'mostrar_modal': True,
            'tipo': tipo
        }), 500


@api_freemium_bp.route('/consumir/<tipo>', methods=['POST'])
@login_required
def consumir_recurso(tipo):
    """
    Consome um recurso gratuito (interno - apenas para tracking)
    """
    try:
        logger.info(f"[FREEMIUM] Tentando consumir '{tipo}' para usuário {current_user.id}")
        tipo = tipo.lower()
        
        if tipo == 'redacao':
            pode, msg = current_user.pode_fazer_redacao
            if pode:
                current_user.consumir_redacao_gratuita()
                logger.info(f"[FREEMIUM] Redação consumida. Restantes: {current_user.redacoes_gratuitas_restantes}")
                return jsonify({
                    'success': True,
                    'message': 'Redação consumida',
                    'restantes': current_user.redacoes_gratuitas_restantes
                })
        elif tipo == 'simulado':
            pode, msg = current_user.pode_fazer_simulado
            if pode:
                current_user.consumir_simulado_gratuito()
                logger.info(f"[FREEMIUM] Simulado consumido. Restantes: {current_user.simulados_gratuitos_restantes}")
                return jsonify({
                    'success': True,
                    'message': 'Simulado consumido',
                    'restantes': current_user.simulados_gratuitos_restantes
                })
        elif tipo == 'aula':
            pode, msg = current_user.pode_assistir_aula
            if pode:
                current_user.consumir_aula_gratuita()
                logger.info(f"[FREEMIUM] Aula consumida. Restantes: {current_user.aulas_gratuitas_restantes}")
                return jsonify({
                    'success': True,
                    'message': 'Aula consumida',
                    'restantes': current_user.aulas_gratuitas_restantes
                })
        
        logger.warning(f"[FREEMIUM] Não foi possível consumir '{tipo}' para usuário {current_user.id}")
        return jsonify({
            'success': False,
            'error': 'Não foi possível consumir recurso',
            'mostrar_modal': True
        }), 403
        
    except Exception as e:
        logger.error(f"[FREEMIUM] Erro ao consumir recurso '{tipo}': {e}")
        logger.error(f"[FREEMIUM] Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': 'Erro ao processar'
        }), 500

@api_freemium_bp.route('/widget-info', methods=['GET'])
@login_required
def widget_info():
    """
    Retorna informações resumidas para widgets/badges no frontend
    """
    try:
        logger.info(f"[FREEMIUM] Buscando widget info para usuário {current_user.id}")
        
        return jsonify({
            'success': True,
            'plano': current_user.plano_ativo,
            'tem_plano': current_user.tem_plano_ativo,
            'limites': {
                'redacoes': {
                    'usado': 3 - current_user.redacoes_gratuitas_restantes,
                    'total': 3,
                    'restantes': current_user.redacoes_gratuitas_restantes,
                    'percentual': (current_user.redacoes_gratuitas_restantes / 3) * 100
                },
                'simulados': {
                    'usado': 3 - current_user.simulados_gratuitos_restantes,
                    'total': 3,
                    'restantes': current_user.simulados_gratuitos_restantes,
                    'percentual': (current_user.simulados_gratuitos_restantes / 3) * 100
                },
                'aulas': {
                    'usado': 10 - current_user.aulas_gratuitas_restantes,
                    'total': 10,
                    'restantes': current_user.aulas_gratuitas_restantes,
                    'percentual': (current_user.aulas_gratuitas_restantes / 10) * 100
                }
            }
        })
    except Exception as e:
        logger.error(f"[FREEMIUM] Erro ao buscar widget info: {e}")
        logger.error(f"[FREEMIUM] Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_freemium_bp.route('/debug/<tipo>', methods=['GET'])
@login_required
def debug_limite(tipo):
    """
    Endpoint de debug para verificar status detalhado do usuário
    REMOVER EM PRODUÇÃO ou proteger com admin_required
    """
    try:
        tipo = tipo.lower()
        
        debug_info = {
            'user_id': current_user.id,
            'username': current_user.username,
            'plano_ativo': current_user.plano_ativo,
            'tem_plano_ativo': current_user.tem_plano_ativo,
            'data_expiracao_plano': str(current_user.data_expiracao_plano) if current_user.data_expiracao_plano else None,
            'redacoes_restantes': current_user.redacoes_gratuitas_restantes,
            'simulados_restantes': current_user.simulados_gratuitos_restantes,
            'aulas_restantes': current_user.aulas_gratuitas_restantes,
        }
        
        if tipo == 'aula':
            pode, msg = current_user.pode_assistir_aula
            debug_info['tipo'] = 'aula'
            debug_info['pode_acessar'] = pode
            debug_info['mensagem'] = msg
        elif tipo == 'simulado':
            pode, msg = current_user.pode_fazer_simulado
            debug_info['tipo'] = 'simulado'
            debug_info['pode_acessar'] = pode
            debug_info['mensagem'] = msg
        elif tipo == 'redacao':
            pode, msg = current_user.pode_fazer_redacao
            debug_info['tipo'] = 'redacao'
            debug_info['pode_acessar'] = pode
            debug_info['mensagem'] = msg
        
        return jsonify({
            'success': True,
            'debug': debug_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500
