# app/services/onboarding_service.py
"""
Serviço de Onboarding - Gerencia o tour guiado para novos usuários
Sistema de modais overlay que guia o usuário pelas principais funcionalidades
"""

from datetime import datetime
from app import db
from sqlalchemy import and_
import logging

logger = logging.getLogger(__name__)

# ==================== CONFIGURAÇÃO DAS ETAPAS ====================
# ==================== BLOCO 1: ETAPAS_ONBOARDING (Substituir das linhas 15-65) ====================

ETAPAS_ONBOARDING = {
    1: {
        'nome': 'boas_vindas',
        'titulo': '🎉 Bem-vindo à Plataforma Launcher!',
        'descricao': 'Vamos fazer um tour rápido de 3 minutos para você conhecer as principais funcionalidades?',
        'rota_destino': None,
        'acao_necessaria': 'aceitar_tour',
        'recompensa': {'xp': 0, 'diamantes': 0}
    },
    2: {
        'nome': 'cronograma',
        'titulo': '📅 Organize seus Estudos',
        'descricao': 'Primeiro, vamos criar seu cronograma personalizado! Ele vai te ajudar a manter uma rotina de estudos consistente.',
        'rota_destino': '/cronograma/wizard',
        'elemento_destaque': '.wizard-container',
        'acao_necessaria': 'criar_cronograma',
        'recompensa': {'xp': 20, 'diamantes': 10, 'badge': 'Planejador'}
    },
    3: {
        'nome': 'primeira_aula',
        'titulo': '🎓 Conheça o Sistema de Aulas',
        'descricao': 'Agora vamos conhecer como funcionam as aulas! Assista 2 minutos de uma aula para ganhar suas primeiras moedas.',
        'rota_destino': '/estudo/aula/474',
        'elemento_destaque': 'video, iframe, .video-player',
        'acao_necessaria': 'assistir_aula',
        'recompensa': {'xp': 30, 'diamantes': 15, 'badge': 'Primeiro Passo'},
        'info_adicional': '💡 Você ganha moedas estudando! A cada 3 minutos = 2 XP + 1 Launcher Coin'
    },
    4: {
        'nome': 'explicacao_simulados',
        'titulo': '📝 Conheça os Simulados',
        'descricao': 'Agora vamos fazer um mini simulado! Em simulados, você pode responder questões enquanto estuda e aprende com explicações detalhadas.',
        'rota_destino': None,
        'acao_necessaria': 'entender_simulados',
        'recompensa': {'xp': 0, 'diamantes': 0},
        'info_adicional': '💡 Cada questão tem explicação completa para você entender seus erros e acertos!'
    },
    5: {
        'nome': 'simulado_diagnostico',
        'titulo': '📊 Avalie seu Nível Inicial',
        'descricao': 'Vamos fazer um diagnóstico rápido com 5 questões para avaliar seu nível atual. Não se preocupe, é só para te conhecer melhor!',
        'rota_destino': '/simulados/diagnostico-onboarding',
        'elemento_destaque': '.btn-primary',
        'acao_necessaria': 'concluir_diagnostico',
        'recompensa': {'xp': 50, 'diamantes': 25, 'badge': 'Avaliado'},
        'info_adicional': '💡 Simulados também rendem moedas baseadas na sua nota!'
    },
    6: {
        'nome': 'finalizacao',
        'titulo': '🎊 Parabéns! Tour Básico Completo!',
        'descricao': 'Você já conhece o essencial da plataforma! Quer fazer o tour completo e ganhar 100 Launcher Coins extras?',
        'rota_destino': None,
        'acao_necessaria': 'escolher_proximo_passo',
        'recompensa': {'xp': 0, 'diamantes': 0},
        'opcoes': [
            {'texto': '🚀 Pular Etapa', 'acao': 'finalizar_basico'},
            {'texto': '📚 Fazer Tour Completo (+100 Launcher Coins)', 'acao': 'continuar_tour_completo'},
            {'texto': '⏭️ Fazer Depois', 'acao': 'adiar_tour'}
        ]
    }
}


# ==================== BLOCO 2: ETAPAS_TOUR_COMPLETO (Substituir das linhas 70-115) ====================

ETAPAS_TOUR_COMPLETO = {
    7: {
        'nome': 'helpzone',
        'titulo': '💬 HelpZone - Rede Social de Estudos',
        'descricao': 'Compartilhe sua rotina e tire dúvidas com outros estudantes! Faça seu primeiro post.',
        'rota_destino': '/helpzone',
        'elemento_destaque': '.criar-post-btn',
        'acao_necessaria': 'criar_post',
        'recompensa': {'xp': 25, 'diamantes': 12}
    },
    8: {
        'nome': 'redacao',
        'titulo': '✍️ Redações com IA',
        'descricao': 'Nossa IA corrige sua redação seguindo os critérios do ENEM! Envie uma redação agora para ganhar sua recompensa, ou pule para continuar.',
        'rota_destino': '/redacao',
        'elemento_destaque': '.btn-nova-redacao',
        'acao_necessaria': 'enviar_redacao',
        'recompensa': {'xp': 20, 'diamantes': 10},
        'info_adicional': '💡 A IA avalia nas 5 competências do ENEM e dá feedback detalhado!'
    },
    9: {
        'nome': 'shop',
        'titulo': '🛍️ Shop - Troque suas Moedas!',
        'descricao': 'Você ganhou moedas estudando! Agora vamos desbloquear seu primeiro desconto especial.',
        'rota_destino': '/shop/yampi',
        'elemento_destaque': '.produto-card:first',
        'acao_necessaria': 'desbloquear_produto',
        'recompensa': {'xp': 20, 'diamantes': 0},
        'info_adicional': '💡 Clique em "Desbloquear Agora" no produto especial para resgatar seu desconto!'
    },
    10: {
        'nome': 'metricas',
        'titulo': '📈 Acompanhe seu Progresso',
        'descricao': 'Visualize suas estatísticas, rankings e evolução nos estudos!',
        'rota_destino': '/progresso',
        'elemento_destaque': '.stats-card',
        'acao_necessaria': 'visualizar_metricas',
        'recompensa': {'xp': 0, 'diamantes': 0}
    },
    11: {
        'nome': 'tour_completo_finalizado',
        'titulo': '🏆 Tour Completo Finalizado!',
        'descricao': 'Parabéns! Você conhece todas as funcionalidades da plataforma!',
        'rota_destino': None,
        'acao_necessaria': 'finalizar_tour_completo',
        'recompensa': {'xp': 100, 'diamantes': 50, 'badge': 'Explorador Completo'}
    }
}


class OnboardingProgresso(db.Model):
    """
    Rastreia o progresso do onboarding de cada usuário
    """
    __tablename__ = 'onboarding_progresso'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    
    # Controle de etapas
    etapa_atual = db.Column(db.Integer, default=1)  # Etapa em que o usuário está
    etapas_concluidas = db.Column(db.JSON, default=list)  # Lista de nomes das etapas concluídas
    
    # Flags de controle
    onboarding_iniciado = db.Column(db.Boolean, default=False)
    onboarding_basico_completo = db.Column(db.Boolean, default=False)
    tour_completo_ativo = db.Column(db.Boolean, default=False)
    tour_completo_finalizado = db.Column(db.Boolean, default=False)
    
    # Controle de ações específicas (para não dar recompensa duplicada)
    cronograma_criado = db.Column(db.Boolean, default=False)
    primeira_aula_assistida = db.Column(db.Boolean, default=False)
    diagnostico_concluido = db.Column(db.Boolean, default=False)
    primeiro_post_criado = db.Column(db.Boolean, default=False)
    
    # Timestamps
    data_inicio = db.Column(db.DateTime, default=datetime.utcnow)
    data_conclusao_basico = db.Column(db.DateTime)
    data_conclusao_completo = db.Column(db.DateTime)
    adiado_ate = db.Column(db.DateTime, nullable=True)
    # Recompensas já dadas (para evitar duplicação)
    recompensas_dadas = db.Column(db.JSON, default=list)
    
    # Relacionamento
    user = db.relationship('User', backref=db.backref('onboarding', uselist=False))
    
    def __repr__(self):
        return f'<OnboardingProgresso User {self.user_id} - Etapa {self.etapa_atual}>'


# ==================== FUNÇÕES DO SERVIÇO ====================

def iniciar_onboarding(user_id):
    """
    Inicia o onboarding para um novo usuário
    Retorna: dict com status e dados da primeira etapa
    """
    try:
        # Verificar se já existe progresso
        progresso = OnboardingProgresso.query.filter_by(user_id=user_id).first()
        
        if progresso:
            # Se já iniciou, retorna etapa atual
            # Se já completou básico e ainda não ativou o tour completo
            # ✅ CORRIGIDO: ainda precisa mostrar a etapa 5 (finalizacao) para o usuário escolher
            if progresso.onboarding_basico_completo and not progresso.tour_completo_ativo:
                # Garante que a tela de decisão apareça
                return {
                    'status': 'ativo',  # importante: o frontend espera renderizar a etapa
                    'etapa': 6,
                    'dados_etapa': ETAPAS_ONBOARDING[6],
                    'etapas_concluidas': progresso.etapas_concluidas,
                    'tour_completo_ativo': False,
                    'pode_fazer_tour_completo': True
                }
            
            return obter_etapa_atual(user_id)
        
        # Criar novo progresso
        progresso = OnboardingProgresso(
            user_id=user_id,
            etapa_atual=1,
            etapas_concluidas=[],
            onboarding_iniciado=True
        )
        
        db.session.add(progresso)
        db.session.commit()
        
        logger.info(f"Onboarding iniciado para user_id={user_id}")
        
        # Retornar dados da primeira etapa
        return {
            'status': 'iniciado',
            'etapa': 1,
            'dados_etapa': ETAPAS_ONBOARDING[1]
        }
        
    except Exception as e:
        logger.error(f"Erro ao iniciar onboarding: {e}")
        db.session.rollback()
        return {
            'status': 'erro',
            'mensagem': str(e)
        }


def obter_etapa_atual(user_id):
    """
    Retorna os dados da etapa atual do usuário
    """
    try:
        progresso = OnboardingProgresso.query.filter_by(user_id=user_id).first()
        
        if not progresso:
            return iniciar_onboarding(user_id)
        
        # ==================== SKIP INTELIGENTE ====================
        # Se está na etapa 2 (cronograma) mas já criou cronograma, avançar
        if progresso.etapa_atual == 2 and not progresso.cronograma_criado:
            # Verificar se usuário tem cronograma no banco
            from app.models.estudo import Cronograma
            tem_cronograma = Cronograma.query.filter_by(
                user_id=user_id, 
                ativo=True
            ).first() is not None
            
            if tem_cronograma:
                logger.info(f"✨ Skip inteligente: usuário {user_id} já tem cronograma, avançando automaticamente")
                # Avançar para próxima etapa sem dar recompensa duplicada
                progresso.cronograma_criado = True
                progresso.etapa_atual = 3
                if 'cronograma' not in progresso.etapas_concluidas:
                    progresso.etapas_concluidas.append('cronograma')
                db.session.commit()
        # =========================================================
        
        # Se já completou básico
        if progresso.onboarding_basico_completo and not progresso.tour_completo_ativo:
            return {
                'status': 'basico_completo',
                'mensagem': 'Onboarding básico concluído',
                'pode_fazer_tour_completo': True
            }
        
        # Se está no tour completo
        if progresso.tour_completo_ativo:
            etapa_info = ETAPAS_TOUR_COMPLETO.get(progresso.etapa_atual)
        else:
            etapa_info = ETAPAS_ONBOARDING.get(progresso.etapa_atual)
        
        if not etapa_info:
            return {
                'status': 'erro',
                'mensagem': 'Etapa não encontrada'
            }
        
        return {
            'status': 'ativo',
            'etapa': progresso.etapa_atual,
            'dados_etapa': etapa_info,
            'etapas_concluidas': progresso.etapas_concluidas,
            'tour_completo_ativo': progresso.tour_completo_ativo
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter etapa atual: {e}")
        return {
            'status': 'erro',
            'mensagem': str(e)
        }

def avancar_etapa(user_id, acao_concluida):
    """
    Avança para a próxima etapa após o usuário completar uma ação
    
    Args:
        user_id: ID do usuário
        acao_concluida: Nome da ação que foi concluída
    
    Returns:
        dict com status e dados da próxima etapa (ou finalização)
    """
    try:
        progresso = OnboardingProgresso.query.filter_by(user_id=user_id).first()
        
        if not progresso:
            return {
                'status': 'erro',
                'mensagem': 'Progresso não encontrado'
            }
        
        # Obter etapa atual
        if progresso.tour_completo_ativo:
            etapa_atual = ETAPAS_TOUR_COMPLETO.get(progresso.etapa_atual)
        else:
            etapa_atual = ETAPAS_ONBOARDING.get(progresso.etapa_atual)
        
        if not etapa_atual:
            return {
                'status': 'erro',
                'mensagem': 'Etapa atual não encontrada'
            }
        
        # Verificar se a ação concluída corresponde à etapa atual
        if etapa_atual['acao_necessaria'] != acao_concluida:
            logger.warning(f"Ação {acao_concluida} não corresponde à etapa {progresso.etapa_atual}")
            return {
                'status': 'erro',
                'mensagem': 'Ação não corresponde à etapa atual'
            }
        
        # Marcar etapa como concluída
        if etapa_atual['nome'] not in progresso.etapas_concluidas:
            progresso.etapas_concluidas.append(etapa_atual['nome'])
        
        # Marcar flags específicas de ações
        if acao_concluida == 'criar_cronograma':
            progresso.cronograma_criado = True
        elif acao_concluida == 'assistir_aula':
            progresso.primeira_aula_assistida = True
        elif acao_concluida == 'concluir_diagnostico':
            progresso.diagnostico_concluido = True
        elif acao_concluida == 'criar_post':
            progresso.primeiro_post_criado = True
        
        # Dar recompensa (se ainda não foi dada)
        recompensa_dada = None
        recompensa_nome = f"{etapa_atual['nome']}_etapa_{progresso.etapa_atual}"
        
        if recompensa_nome not in progresso.recompensas_dadas:
            recompensa_dada = dar_recompensa(user_id, etapa_atual['recompensa'])
            progresso.recompensas_dadas.append(recompensa_nome)
        
        # Avançar para próxima etapa
        progresso.etapa_atual += 1
        
        # Verificar se concluiu o básico
        if progresso.etapa_atual == 6 and not progresso.onboarding_basico_completo:
            progresso.onboarding_basico_completo = True
            progresso.data_conclusao_basico = datetime.utcnow()
            
            db.session.commit()
            
            return {
                'status': 'basico_finalizado',
                'recompensa': recompensa_dada,
                'dados_etapa': ETAPAS_ONBOARDING[6],  # Tela de finalização
                'xp_total_ganho': sum([e['recompensa'].get('xp', 0) for e in ETAPAS_ONBOARDING.values() if 'recompensa' in e]),
                'diamantes_total_ganho': sum([e['recompensa'].get('diamantes', 0) for e in ETAPAS_ONBOARDING.values() if 'recompensa' in e])
            }
        
        # Verificar se concluiu tour completo
        if progresso.tour_completo_ativo and progresso.etapa_atual > 11:
            progresso.tour_completo_finalizado = True
            progresso.data_conclusao_completo = datetime.utcnow()
            
            db.session.commit()
            
            return {
                'status': 'tour_completo_finalizado',
                'recompensa': recompensa_dada
            }
        db.session.commit()
        
        # Retornar próxima etapa
        return obter_etapa_atual(user_id)
        
    except Exception as e:
        logger.error(f"Erro ao avançar etapa: {e}")
        db.session.rollback()
        return {
            'status': 'erro',
            'mensagem': str(e)
        }



def ativar_tour_completo(user_id):
    """
    Ativa o tour completo após o usuário escolher fazer
    ✅ CORRIGIDO: Aceita usuário na etapa 5 mesmo sem flag basico_completo
    """
    try:
        progresso = OnboardingProgresso.query.filter_by(user_id=user_id).first()
        
        if not progresso:
            return {
                'status': 'erro',
                'mensagem': 'Progresso não encontrado'
            }
        
        # Etapa 5 = finalizacao, onde usuário escolhe próximo passo
        if progresso.etapa_atual != 6 and not progresso.onboarding_basico_completo:
            return {
                'status': 'erro',
                'mensagem': 'Onboarding básico precisa ser concluído primeiro'
            }
        
        # ✅ Marcar como completo se ainda não foi marcado
        if not progresso.onboarding_basico_completo:
            progresso.onboarding_basico_completo = True
            progresso.data_conclusao_basico = datetime.utcnow()
            logger.info(f"✅ Flag onboarding_basico_completo marcada para user_id={user_id}")
        
        # Ativar tour completo
        progresso.tour_completo_ativo = True
        progresso.etapa_atual = 7  # Primeira etapa do tour completo (HelpZone)
        
        db.session.commit()
        
        logger.info(f"✅ Tour completo ativado para user_id={user_id}, avançando para etapa 6")
        
        # Retornar dados da próxima etapa
        return obter_etapa_atual(user_id)
        
    except Exception as e:
        logger.error(f"❌ Erro ao ativar tour completo: {e}")
        db.session.rollback()
        return {
            'status': 'erro',
            'mensagem': str(e)
        }
def dar_recompensa(user_id, recompensa_config):
    """
    Concede recompensas (XP, diamantes, badges) ao usuário

    Args:
        user_id: ID do usuário
        recompensa_config: dict com 'xp', 'diamantes', 'badge'

    Returns:
        dict com recompensas concedidas
    """
    try:
        from app.models.user import User
        from app.services.xp_service import XpService

        user = User.query.get(user_id)
        if not user:
            return None

        recompensa_dada = {
            'xp': 0,
            'diamantes': 0,
            'badge': None
        }

        # XP e Diamantes
        xp = int(recompensa_config.get('xp', 0) or 0)
        diamantes = int(recompensa_config.get('diamantes', 0) or 0)

        # ✅ Conceder XP (se houver)
        if xp > 0:
            XpService.conceder_xp(
                user=user,
                quantidade=xp,
                atividade='onboarding',
                descricao='Recompensa de onboarding'
            )
            recompensa_dada['xp'] = xp

        # ✅ Somar diamantes manualmente (XpService não recebe diamantes)
        if diamantes > 0:
            user.diamantes = (user.diamantes or 0) + diamantes
            recompensa_dada['diamantes'] = diamantes

        # Badge (se houver sistema de badges implementado)
        badge = recompensa_config.get('badge')
        if badge:
            recompensa_dada['badge'] = badge

        # ✅ Persistir (importante, porque alteramos user.diamantes)
        db.session.commit()

        logger.info(f"✅ Recompensa dada ao user_id={user_id}: {recompensa_dada}")
        return recompensa_dada

    except Exception as e:
        logger.error(f"❌ Erro ao dar recompensa: {e}")
        db.session.rollback()
        return None


def verificar_onboarding_ativo(user_id):
    """
    Verifica se o onboarding deve aparecer
    ✅ Considera adiamento temporário
    """
    try:
        from datetime import datetime
        
        progresso = OnboardingProgresso.query.filter_by(user_id=user_id).first()
        if not progresso:
            return False

        # ✅ Se foi adiado e ainda não passou o prazo, não mostrar
        if progresso.adiado_ate and progresso.adiado_ate > datetime.utcnow():
            logger.info(f"⏰ Onboarding adiado até {progresso.adiado_ate} para user_id={user_id}")
            return False

        # ✅ Se passou o prazo, limpar o adiamento
        if progresso.adiado_ate and progresso.adiado_ate <= datetime.utcnow():
            progresso.adiado_ate = None
            db.session.commit()
            logger.info(f"✅ Adiamento expirado, onboarding ativo novamente para user_id={user_id}")

        etapa = int(progresso.etapa_atual or 0)

        # Etapa 5 deve continuar ativa até escolher
        if etapa == 6 and not progresso.tour_completo_ativo and not progresso.tour_completo_finalizado:
            return True

        # Se básico não foi completado, tem onboarding ativo
        if not progresso.onboarding_basico_completo:
            return True

        # Se tour completo está ativo e não finalizou
        if progresso.tour_completo_ativo and not progresso.tour_completo_finalizado:
            return True

        return False

    except Exception as e:
        logger.error(f"Erro ao verificar onboarding ativo: {e}")
        return False

def pular_onboarding(user_id, dias_adiar=7):
    """
    Adia o onboarding por X dias (padrão: 7)
    ✅ NUNCA marca como completo, apenas adia
    """
    try:
        from datetime import datetime, timedelta
        
        progresso = OnboardingProgresso.query.filter_by(user_id=user_id).first()
        
        if not progresso:
            return {
                'status': 'erro',
                'mensagem': 'Progresso não encontrado'
            }
        
        # ✅ NÃO marca como completo, apenas adia
        progresso.adiado_ate = datetime.utcnow() + timedelta(days=dias_adiar)
        
        db.session.commit()
        
        logger.info(f"⏭️ Onboarding adiado até {progresso.adiado_ate} para user_id={user_id}")
        
        return {
            'status': 'sucesso',
            'mensagem': f'Onboarding adiado por {dias_adiar} dias'
        }
        
    except Exception as e:
        logger.error(f"Erro ao pular onboarding: {e}")
        db.session.rollback()
        return {
            'status': 'erro',
            'mensagem': str(e)
        }


def finalizar_onboarding_permanente(user_id):
    """
    Finaliza o onboarding PERMANENTEMENTE
    Usado quando o usuário clica "Começar a Estudar" na etapa 5
    """
    try:
        progresso = OnboardingProgresso.query.filter_by(user_id=user_id).first()
        
        if not progresso:
            return {'status': 'erro', 'mensagem': 'Progresso não encontrado'}
        
        progresso.onboarding_basico_completo = True
        progresso.data_conclusao_basico = datetime.utcnow()
        progresso.adiado_ate = None  # Limpar qualquer adiamento
        
        db.session.commit()
        
        logger.info(f"✅ Onboarding finalizado PERMANENTEMENTE para user_id={user_id}")
        
        return {'status': 'sucesso', 'mensagem': 'Onboarding concluído'}
        
    except Exception as e:
        logger.error(f"Erro ao finalizar onboarding: {e}")
        db.session.rollback()
        return {'status': 'erro', 'mensagem': str(e)}
