# app/services/xp_service.py - Serviço para gerenciar XP e Diamantes

from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from calendar import monthrange
import logging

logger = logging.getLogger(__name__)

# Blueprint para APIs de XP
xp_bp = Blueprint('xp_api', __name__, url_prefix='/api/xp')

class XpSession(db.Model):
    """Modelo para controlar sessões de XP com rigor"""
    __tablename__ = 'xp_session'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    atividade = db.Column(db.String(50), nullable=False)
    inicio = db.Column(db.DateTime, default=datetime.utcnow)
    ultima_atividade = db.Column(db.DateTime, default=datetime.utcnow)
    tempo_ativo = db.Column(db.Integer, default=0)  # Em segundos
    xp_ganho = db.Column(db.Integer, default=0)
    ativa = db.Column(db.Boolean, default=True)
    
    usuario = db.relationship('User', backref=db.backref('xp_sessions', lazy='dynamic'))

class XpService:
    """Serviço central para gerenciar XP e Diamantes"""
    
    @staticmethod
    def verificar_e_resetar_diamantes_mensais(user):
        """Verifica se é necessário resetar os diamantes do usuário (todo mês)"""
        agora = datetime.utcnow()
        ultimo_reset = user.ultimo_reset_diamantes or user.data_registro
        
        # Verificar se mudou o mês
        if ultimo_reset.month != agora.month or ultimo_reset.year != agora.year:
            logger.info(f"RESET MENSAL: Zerando diamantes do usuário {user.id} - novo mês")
            
            # ✅ CORREÇÃO: ZERAR diamantes completamente no reset mensal
            user.diamantes = 0  # Sempre zera, não importa o XP
            user.ultimo_reset_diamantes = agora
            
            db.session.commit()
            
            logger.info(f"Usuário {user.id}: Diamantes resetados para 0. XP continua: {user.xp_total}")
            
            return True, 0  # Sempre retorna 0 após reset
        
        # ✅ IMPORTANTE: Se não foi resetado, NÃO recalcular diamantes
        return False, user.diamantes

    @staticmethod
    def conceder_xp(user, quantidade, atividade, descricao=""):
        """Concede XP e atualiza diamantes automaticamente - VERSÃO CORRIGIDA"""
        try:
            # Atualizar XP (sempre acumulativo)
            user.xp_total = (user.xp_total or 0) + quantidade
            
            # Verificar reset mensal dos diamantes
            foi_resetado, diamantes_atuais = XpService.verificar_e_resetar_diamantes_mensais(user)
            
            # ✅ CORREÇÃO: APENAS adicionar diamantes se não foi resetado
            if not foi_resetado:
                # Adicionar diamantes proporcionalmente ao XP ganho (não recalcular total)
                diamantes_ganhos = quantidade // 2
                user.diamantes = (user.diamantes or 0) + diamantes_ganhos
            else:
                # Se foi resetado, começar do zero e adicionar os diamantes do XP atual
                diamantes_ganhos = quantidade // 2
                user.diamantes = diamantes_ganhos  # Começar do 0 após reset
            
            # Registrar no histórico
            from app.models.estatisticas import XpGanho
            xp_ganho = XpGanho(
                user_id=user.id,
                quantidade=quantidade,
                origem=f"{atividade}: {descricao}",
                data=datetime.utcnow()
            )
            db.session.add(xp_ganho)
            
            db.session.commit()
            
            logger.info(f"Usuário {user.id} ganhou {quantidade} XP e {diamantes_ganhos} diamantes. Total XP: {user.xp_total}, Total Diamantes: {user.diamantes}")
            
            return {
                'xp_ganho': quantidade,
                'xp_total': user.xp_total,
                'diamantes_ganhos': diamantes_ganhos,
                'diamantes_total': user.diamantes,
                'foi_resetado': foi_resetado
            }
            
        except Exception as e:
            logger.error(f"Erro ao conceder XP: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def gastar_diamantes(user, quantidade, motivo=""):
        """Gasta diamantes do usuário (usado no shop)"""
        try:
            # Verificar se tem diamantes suficientes
            if user.diamantes < quantidade:
                return False, "Diamantes insuficientes"
            
            # Gastar diamantes
            user.diamantes -= quantidade
            
            # Registrar gasto
            from app.models.estudo import Moeda
            moeda = Moeda(
                user_id=user.id,
                quantidade=-quantidade,
                tipo='shop',
                descricao=f"Shop: {motivo}"
            )
            db.session.add(moeda)
            db.session.commit()
            
            logger.info(f"Usuário {user.id} gastou {quantidade} diamantes. Saldo: {user.diamantes}")
            
            return True, user.diamantes
            
        except Exception as e:
            logger.error(f"Erro ao gastar diamantes: {e}")
            db.session.rollback()
            return False, str(e)

# ===============================
# ROTAS DA API
# ===============================

@xp_bp.route('/iniciar-sessao', methods=['POST'])
@login_required
def iniciar_sessao():
    """Inicia uma nova sessão de XP"""
    try:
        data = request.get_json()
        atividade = data.get('atividade', 'geral')
        
        # Finalizar qualquer sessão ativa anterior
        sessao_ativa = XpSession.query.filter_by(
            user_id=current_user.id,
            ativa=True
        ).first()
        
        if sessao_ativa:
            sessao_ativa.ativa = False
            db.session.commit()
        
        # Criar nova sessão
        nova_sessao = XpSession(
            user_id=current_user.id,
            atividade=atividade,
            inicio=datetime.utcnow(),
            ultima_atividade=datetime.utcnow()
        )
        
        db.session.add(nova_sessao)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'session_id': nova_sessao.id,
            'message': f'Sessão de {atividade} iniciada'
        })
        
    except Exception as e:
        logger.error(f"Erro ao iniciar sessão: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@xp_bp.route('/conceder-xp', methods=['POST'])
@login_required
def conceder_xp():
    """Concede XP durante uma sessão ativa"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        minutos_ativos = data.get('minutos_ativos', 3)
        
        # Verificar se a sessão existe e está ativa
        sessao = XpSession.query.filter_by(
            id=session_id,
            user_id=current_user.id,
            ativa=True
        ).first()
        
        if not sessao:
            return jsonify({'success': False, 'error': 'Sessão não encontrada'}), 400
        
        # Atualizar última atividade
        sessao.ultima_atividade = datetime.utcnow()
        sessao.tempo_ativo += minutos_ativos * 60  # Converter para segundos
        
        # Conceder 1 XP a cada 3 minutos
        xp_para_conceder = minutos_ativos // 3
        if xp_para_conceder > 0:
            resultado = XpService.conceder_xp(
                current_user, 
                xp_para_conceder, 
                sessao.atividade,
                f"Atividade comprovada ({minutos_ativos} min)"
            )
            
            if resultado:
                sessao.xp_ganho += xp_para_conceder
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'xp_ganho': resultado['xp_ganho'],
                    'xp_total': resultado['xp_total'],
                    'diamantes_ganhos': resultado['diamantes_ganhos'],
                    'diamantes_total': resultado['diamantes_total']
                })
        
        # Mesmo sem XP, confirmar atividade
        db.session.commit()
        return jsonify({
            'success': True,
            'xp_ganho': 0,
            'message': 'Atividade registrada'
        })
        
    except Exception as e:
        logger.error(f"Erro ao conceder XP: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@xp_bp.route('/pausar-sessao', methods=['POST'])
@login_required
def pausar_sessao():
    """Pausa uma sessão por inatividade"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        sessao = XpSession.query.filter_by(
            id=session_id,
            user_id=current_user.id
        ).first()
        
        if sessao and sessao.ativa:
            # Não finalizar, apenas marcar pausa
            sessao.ultima_atividade = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Sessão {session_id} pausada por inatividade")
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Erro ao pausar sessão: {e}")
        return jsonify({'success': False}), 500

@xp_bp.route('/finalizar-sessao', methods=['POST'])
@login_required
def finalizar_sessao():
    """Finaliza uma sessão de XP"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        tempo_total = data.get('tempo_total', 0)
        
        sessao = XpSession.query.filter_by(
            id=session_id,
            user_id=current_user.id
        ).first()
        
        if sessao and sessao.ativa:
            sessao.ativa = False
            sessao.tempo_ativo = max(sessao.tempo_ativo, tempo_total)
            db.session.commit()
            
            logger.info(f"Sessão {session_id} finalizada. Tempo total: {tempo_total}s")
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Erro ao finalizar sessão: {e}")
        return jsonify({'success': False}), 500

@xp_bp.route('/status', methods=['GET'])
@login_required
def status_usuario():
    """Retorna status atual do usuário (XP, diamantes, etc)"""
    try:
        # Verificar reset mensal
        foi_resetado, diamantes = XpService.verificar_e_resetar_diamantes_mensais(current_user)
        
        return jsonify({
            'success': True,
            'xp_total': current_user.xp_total or 0,
            'diamantes': current_user.diamantes or 0,
            'foi_resetado': foi_resetado,
            'ultimo_reset': current_user.ultimo_reset_diamantes.isoformat() if current_user.ultimo_reset_diamantes else None
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
