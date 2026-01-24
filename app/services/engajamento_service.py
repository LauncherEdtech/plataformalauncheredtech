# app/services/engajamento_service.py
"""
Sistema de Análise de Engajamento de Usuários
Classifica usuários em: 🔥 Quente | 🟡 Morno | 🧊 Frio
"""

from datetime import datetime, timedelta
from sqlalchemy import func, distinct
from app import db
from app.models.user import User
from app.models.estatisticas import TempoEstudo, ExercicioRealizado, XpGanho
from app.models.simulado import Simulado
import logging

logger = logging.getLogger(__name__)


class EngajamentoService:
    """Serviço para análise de engajamento dos usuários"""
    
    # Pesos para cálculo do score
    PESO_FREQUENCIA = 0.40  # 40%
    PESO_TEMPO = 0.25       # 25%
    PESO_VARIEDADE = 0.20   # 20%
    PESO_PROGRESSAO = 0.15  # 15%
    
    # Thresholds de classificação
    SCORE_QUENTE = 60    # 60-100: Quente
    SCORE_MORNO = 30     # 30-59: Morno
    # 0-29: Frio
    
    @classmethod
    def calcular_score_engajamento(cls, user_id, dias_analise=7):
        """
        Calcula score de engajamento de 0-100 para um usuário
        
        Args:
            user_id: ID do usuário
            dias_analise: Janela de tempo para análise (padrão: 7 dias)
            
        Returns:
            dict com score e métricas detalhadas
        """
        try:
            data_inicio = datetime.utcnow() - timedelta(days=dias_analise)
            
            # 1. FREQUÊNCIA (40%) - Dias ativos
            score_frequencia = cls._calcular_score_frequencia(user_id, data_inicio, dias_analise)
            
            # 2. TEMPO DE ESTUDO (25%) - Horas estudadas
            score_tempo = cls._calcular_score_tempo(user_id, data_inicio)
            
            # 3. VARIEDADE (20%) - Tipos de atividades
            score_variedade = cls._calcular_score_variedade(user_id, data_inicio)
            
            # 4. PROGRESSÃO (15%) - XP ganho
            score_progressao = cls._calcular_score_progressao(user_id, data_inicio)
            
            # Score total ponderado
            score_total = (
                score_frequencia * cls.PESO_FREQUENCIA +
                score_tempo * cls.PESO_TEMPO +
                score_variedade * cls.PESO_VARIEDADE +
                score_progressao * cls.PESO_PROGRESSAO
            )
            
            # Classificação
            classificacao = cls._classificar_usuario(score_total)
            
            return {
                'score_total': round(score_total, 1),
                'classificacao': classificacao,
                'detalhes': {
                    'frequencia': round(score_frequencia, 1),
                    'tempo': round(score_tempo, 1),
                    'variedade': round(score_variedade, 1),
                    'progressao': round(score_progressao, 1)
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular score de engajamento para user {user_id}: {e}")
            return {
                'score_total': 0,
                'classificacao': 'frio',
                'detalhes': {
                    'frequencia': 0,
                    'tempo': 0,
                    'variedade': 0,
                    'progressao': 0
                }
            }
    
    @classmethod
    def _calcular_score_frequencia(cls, user_id, data_inicio, dias_analise):
        """Calcula score baseado em dias ativos e consistência"""
        try:
            # Contar dias únicos com atividade
            dias_ativos = db.session.query(
                func.count(distinct(func.date(TempoEstudo.data_inicio)))
            ).filter(
                TempoEstudo.user_id == user_id,
                TempoEstudo.data_inicio >= data_inicio,
                TempoEstudo.minutos >= 5  # Pelo menos 5 minutos para contar
            ).scalar() or 0
            
            # Calcular percentual de dias ativos
            percentual_dias = (dias_ativos / dias_analise) * 100
            
            # Calcular streak (sequência)
            streak = cls._calcular_streak_recente(user_id)
            bonus_streak = min(streak * 5, 20)  # Até 20 pontos de bônus
            
            score = min(percentual_dias + bonus_streak, 100)
            return score
            
        except Exception as e:
            logger.error(f"Erro ao calcular score de frequência: {e}")
            return 0
    
    @classmethod
    def _calcular_score_tempo(cls, user_id, data_inicio):
        """Calcula score baseado em tempo de estudo"""
        try:
            # Total de minutos estudados
            total_minutos = db.session.query(
                func.sum(TempoEstudo.minutos)
            ).filter(
                TempoEstudo.user_id == user_id,
                TempoEstudo.data_inicio >= data_inicio
            ).scalar() or 0
            
            horas = total_minutos / 60
            
            # Escala: 10+ horas = 100 pontos
            # 3-9 horas = 30-90 pontos
            # <3 horas = 0-30 pontos
            if horas >= 10:
                score = 100
            elif horas >= 3:
                score = 30 + ((horas - 3) / 7) * 70
            else:
                score = (horas / 3) * 30
            
            return min(score, 100)
            
        except Exception as e:
            logger.error(f"Erro ao calcular score de tempo: {e}")
            return 0
    
    @classmethod
    def _calcular_score_variedade(cls, user_id, data_inicio):
        """Calcula score baseado na variedade de atividades"""
        try:
            # Tipos diferentes de atividades
            atividades_unicas = db.session.query(
                func.count(distinct(TempoEstudo.atividade))
            ).filter(
                TempoEstudo.user_id == user_id,
                TempoEstudo.data_inicio >= data_inicio,
                TempoEstudo.atividade.isnot(None)
            ).scalar() or 0
            
            # Simulados realizados
            simulados = Simulado.query.filter(
                Simulado.user_id == user_id,
                Simulado.data_realizado >= data_inicio
            ).count()
            
            # Exercícios realizados
            exercicios = ExercicioRealizado.query.filter(
                ExercicioRealizado.user_id == user_id,
                ExercicioRealizado.data_realizado >= data_inicio
            ).count()
            
            # Pontuação por variedade
            score = 0
            score += min(atividades_unicas * 20, 40)  # Até 40 pontos
            score += min(simulados * 15, 30)           # Até 30 pontos
            score += min(exercicios * 0.5, 30)         # Até 30 pontos
            
            return min(score, 100)
            
        except Exception as e:
            logger.error(f"Erro ao calcular score de variedade: {e}")
            return 0
    
    @classmethod
    def _calcular_score_progressao(cls, user_id, data_inicio):
        """Calcula score baseado em XP ganho e progresso"""
        try:
            # XP ganho no período
            xp_periodo = db.session.query(
                func.sum(XpGanho.quantidade)
            ).filter(
                XpGanho.user_id == user_id,
                XpGanho.data >= data_inicio
            ).scalar() or 0
            
            # Escala: 500+ XP = 100 pontos
            # 100-499 XP = 20-90 pontos
            # <100 XP = 0-20 pontos
            if xp_periodo >= 500:
                score = 100
            elif xp_periodo >= 100:
                score = 20 + ((xp_periodo - 100) / 400) * 80
            else:
                score = (xp_periodo / 100) * 20
            
            return min(score, 100)
            
        except Exception as e:
            logger.error(f"Erro ao calcular score de progressão: {e}")
            return 0
    
    @classmethod
    def _calcular_streak_recente(cls, user_id):
        """Calcula sequência de dias consecutivos estudando"""
        try:
            hoje = datetime.utcnow().date()
            streak = 0
            data_verificacao = hoje
            
            for _ in range(30):  # Verificar até 30 dias
                tem_atividade = db.session.query(TempoEstudo).filter(
                    TempoEstudo.user_id == user_id,
                    func.date(TempoEstudo.data_inicio) == data_verificacao,
                    TempoEstudo.minutos >= 5
                ).first()
                
                if tem_atividade:
                    streak += 1
                    data_verificacao -= timedelta(days=1)
                else:
                    break
            
            return streak
            
        except Exception as e:
            logger.error(f"Erro ao calcular streak: {e}")
            return 0
    
    @classmethod
    def _classificar_usuario(cls, score):
        """Classifica usuário baseado no score"""
        if score >= cls.SCORE_QUENTE:
            return 'quente'
        elif score >= cls.SCORE_MORNO:
            return 'morno'
        else:
            return 'frio'
    
    @classmethod
    def obter_metricas_detalhadas(cls, user_id):
        """Obtém métricas detalhadas de engajamento para um usuário"""
        try:
            user = User.query.get(user_id)
            if not user:
                return None
            
            data_7d = datetime.utcnow() - timedelta(days=7)
            data_30d = datetime.utcnow() - timedelta(days=30)
            
            # Score e classificação
            engajamento = cls.calcular_score_engajamento(user_id, dias_analise=7)
            
            # Dias ativos
            dias_ativos_7d = db.session.query(
                func.count(distinct(func.date(TempoEstudo.data_inicio)))
            ).filter(
                TempoEstudo.user_id == user_id,
                TempoEstudo.data_inicio >= data_7d
            ).scalar() or 0
            
            # Tempo total
            tempo_7d = db.session.query(
                func.sum(TempoEstudo.minutos)
            ).filter(
                TempoEstudo.user_id == user_id,
                TempoEstudo.data_inicio >= data_7d
            ).scalar() or 0
            
            # Simulados
            simulados_7d = Simulado.query.filter(
                Simulado.user_id == user_id,
                Simulado.data_realizado >= data_7d
            ).count()
            
            # Última atividade
            ultima_atividade = db.session.query(
                func.max(TempoEstudo.data_inicio)
            ).filter(
                TempoEstudo.user_id == user_id
            ).scalar()
            
            dias_sem_atividade = 0
            if ultima_atividade:
                dias_sem_atividade = (datetime.utcnow() - ultima_atividade).days
            else:
                dias_sem_atividade = (datetime.utcnow() - user.data_registro).days
            
            # Streak
            streak = cls._calcular_streak_recente(user_id)
            
            return {
                'user_id': user_id,
                'username': user.username,
                'email': user.email,
                'telefone': user.telefone or "-",
                'score': engajamento['score_total'],
                'classificacao': engajamento['classificacao'],
                'detalhes_score': engajamento['detalhes'],
                'dias_ativos_7d': dias_ativos_7d,
                'tempo_estudo_7d': round(tempo_7d / 60, 1),  # em horas
                'simulados_7d': simulados_7d,
                'streak_dias': streak,
                'dias_sem_atividade': dias_sem_atividade,
                'ultima_atividade': ultima_atividade.strftime('%d/%m/%Y %H:%M') if ultima_atividade else 'Nunca',
                'risco_churn': cls._calcular_risco_churn(engajamento['classificacao'], dias_sem_atividade)
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter métricas detalhadas: {e}")
            return None
    
    @classmethod
    def _calcular_risco_churn(cls, classificacao, dias_sem_atividade):
        """Calcula risco de churn do usuário"""
        if dias_sem_atividade >= 15:
            return 'alto'
        elif dias_sem_atividade >= 7 or classificacao == 'frio':
            return 'medio'
        elif classificacao == 'morno':
            return 'baixo'
        else:
            return 'muito_baixo'
    
    @classmethod
    def obter_distribuicao_engajamento(cls):
        """Obtém distribuição de usuários por classificação"""
        try:
            todos_usuarios = User.query.all()
            
            distribuicao = {
                'quente': 0,
                'morno': 0,
                'frio': 0
            }
            
            usuarios_classificados = []
            
            for user in todos_usuarios:
                resultado = cls.calcular_score_engajamento(user.id)
                classificacao = resultado['classificacao']
                distribuicao[classificacao] += 1
                
                usuarios_classificados.append({
                    'user_id': user.id,
                    'username': user.username,
                    'score': resultado['score_total'],
                    'classificacao': classificacao
                })
            
            return {
                'distribuicao': distribuicao,
                'total_usuarios': len(todos_usuarios),
                'percentuais': {
                    'quente': round((distribuicao['quente'] / len(todos_usuarios) * 100), 1) if todos_usuarios else 0,
                    'morno': round((distribuicao['morno'] / len(todos_usuarios) * 100), 1) if todos_usuarios else 0,
                    'frio': round((distribuicao['frio'] / len(todos_usuarios) * 100), 1) if todos_usuarios else 0
                },
                'usuarios': usuarios_classificados
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter distribuição de engajamento: {e}")
            return {
                'distribuicao': {'quente': 0, 'morno': 0, 'frio': 0},
                'total_usuarios': 0,
                'percentuais': {'quente': 0, 'morno': 0, 'frio': 0},
                'usuarios': []
            }
    
    @classmethod
    def obter_alertas_engajamento(cls):
        """Identifica usuários que precisam de atenção/intervenção"""
        try:
            data_7d = datetime.utcnow() - timedelta(days=7)
            data_15d = datetime.utcnow() - timedelta(days=15)
            
            alertas = {
                'criticos': [],  # Sem atividade 15+ dias
                'atenção': [],   # Sem atividade 7-14 dias
                'reativados': [], # Voltaram após período inativo
                'super_engajados': []  # Score 90+
            }
            
            usuarios = User.query.all()
            
            for user in usuarios:
                metricas = cls.obter_metricas_detalhadas(user.id)
                if not metricas:
                    continue
                
                dias_sem = metricas['dias_sem_atividade']
                score = metricas['score']
                
                # Alertas críticos
                if dias_sem >= 15:
                    alertas['criticos'].append(metricas)
                
                # Alertas de atenção
                elif dias_sem >= 7:
                    alertas['atenção'].append(metricas)
                
                # Super engajados
                if score >= 90:
                    alertas['super_engajados'].append(metricas)
            
            return alertas
            
        except Exception as e:
            logger.error(f"Erro ao obter alertas: {e}")
            return {
                'criticos': [],
                'atenção': [],
                'reativados': [],
                'super_engajados': []
            }
