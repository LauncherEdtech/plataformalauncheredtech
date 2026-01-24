# app/utils/ranking_utils.py
from datetime import datetime, timedelta
from sqlalchemy import func
from app import db
from app.models.user import User
from app.models.estatisticas import XpGanho, TempoEstudo
from app.models.simulado import Simulado

class RankingUtils:
    """
    Classe utilitária para cálculos e operações relacionadas ao ranking.
    Centraliza funções comuns para otimização e reutilização.
    """
    
    @staticmethod
    def get_periodo_mes_atual():
        """Retorna o início e fim do mês atual."""
        agora = datetime.utcnow()
        inicio_mes = agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return inicio_mes
    
    @staticmethod
    def formatar_tempo_estudo(minutos):
        """
        Formata minutos em string legível para exibição.
        
        Args:
            minutos (int): Tempo em minutos
            
        Returns:
            str: Tempo formatado (ex: "2h30" ou "45min")
        """
        if minutos == 0:
            return "0h"
        
        horas = minutos // 60
        min_restantes = minutos % 60
        
        if horas > 0:
            if min_restantes > 0:
                return f"{horas}h{min_restantes:02d}"
            else:
                return f"{horas}h"
        else:
            return f"{min_restantes}min"
    
    @staticmethod
    def get_badge_nota_tri(nota):
        """
        Retorna a classe CSS e texto do badge baseado na nota TRI.
        
        Args:
            nota (float): Nota TRI
            
        Returns:
            dict: Contém 'classe' e 'texto' para o badge
        """
        if nota >= 700:
            return {'classe': 'nota-excelente', 'texto': 'Excelente', 'icone': 'star-fill'}
        elif nota >= 600:
            return {'classe': 'nota-boa', 'texto': 'Boa', 'icone': 'trophy'}
        elif nota >= 500:
            return {'classe': 'nota-media', 'texto': 'Média', 'icone': 'arrow-up'}
        else:
            return {'classe': 'nota-baixa', 'texto': 'Melhorar', 'icone': 'arrow-up'}
    
    @staticmethod
    def get_badge_tempo_estudo(minutos):
        """
        Retorna badge baseado no tempo de estudo mensal.
        
        Args:
            minutos (int): Tempo total de estudo em minutos
            
        Returns:
            dict: Informações do badge ou None
        """
        if minutos >= 1200:  # 20+ horas
            return {'classe': 'bg-danger', 'texto': 'Maratonista', 'icone': 'fire'}
        elif minutos >= 600:  # 10+ horas
            return {'classe': 'bg-warning text-dark', 'texto': 'Dedicado', 'icone': 'lightning'}
        elif minutos >= 300:  # 5+ horas
            return {'classe': 'bg-success', 'texto': 'Consistente', 'icone': 'star'}
        else:
            return None
    
    @staticmethod
    def calcular_ranking_geral(limit=50):
        """
        Calcula o ranking geral por XP total.
        
        Args:
            limit (int): Número máximo de usuários a retornar
            
        Returns:
            list: Lista de usuários ordenados por XP
        """
        return db.session.query(
            User.id,
            User.nome_completo,
            User.username,
            User.xp_total
        ).filter(
            User.is_active == True,
            User.xp_total > 0
        ).order_by(User.xp_total.desc()).limit(limit).all()
    
    @staticmethod
    def calcular_ranking_mensal(limit=50):
        """
        Calcula o ranking mensal por XP ganho no mês.
        
        Args:
            limit (int): Número máximo de usuários a retornar
            
        Returns:
            list: Lista de usuários ordenados por XP do mês
        """
        inicio_mes = RankingUtils.get_periodo_mes_atual()
        
        return db.session.query(
            User.id,
            User.nome_completo,
            User.username,
            func.coalesce(func.sum(XpGanho.quantidade), 0).label('xp_mes')
        ).outerjoin(
            XpGanho,
            db.and_(User.id == XpGanho.user_id, XpGanho.data >= inicio_mes)
        ).filter(
            User.is_active == True
        ).group_by(
            User.id, User.nome_completo, User.username
        ).having(
            func.coalesce(func.sum(XpGanho.quantidade), 0) > 0
        ).order_by(func.sum(XpGanho.quantidade).desc()).limit(limit).all()
    
    @staticmethod
    def calcular_ranking_tempo(limit=50):
        """
        Calcula o ranking por tempo de estudo no mês.
        
        Args:
            limit (int): Número máximo de usuários a retornar
            
        Returns:
            list: Lista de usuários ordenados por tempo de estudo
        """
        inicio_mes = RankingUtils.get_periodo_mes_atual()
        
        return db.session.query(
            User.id,
            User.nome_completo,
            User.username,
            func.coalesce(func.sum(TempoEstudo.minutos), 0).label('tempo_total')
        ).outerjoin(
            TempoEstudo,
            db.and_(User.id == TempoEstudo.user_id, TempoEstudo.data_inicio >= inicio_mes)
        ).filter(
            User.is_active == True
        ).group_by(
            User.id, User.nome_completo, User.username
        ).having(
            func.coalesce(func.sum(TempoEstudo.minutos), 0) > 0
        ).order_by(func.sum(TempoEstudo.minutos).desc()).limit(limit).all()
    
    @staticmethod
    def calcular_ranking_simulados(limit=50):
        """
        Calcula o ranking por performance em simulados no mês.
        
        Args:
            limit (int): Número máximo de usuários a retornar
            
        Returns:
            list: Lista de usuários ordenados por média de notas TRI
        """
        inicio_mes = RankingUtils.get_periodo_mes_atual()
        
        return db.session.query(
            User.id,
            User.nome_completo,
            User.username,
            func.avg(Simulado.nota_tri).label('media_notas'),
            func.count(Simulado.id).label('total_simulados')
        ).join(
            Simulado,
            db.and_(
                User.id == Simulado.user_id,
                Simulado.status == 'Concluído',
                Simulado.data_realizado >= inicio_mes,
                Simulado.nota_tri.isnot(None)
            )
        ).filter(
            User.is_active == True
        ).group_by(
            User.id, User.nome_completo, User.username
        ).having(
            func.count(Simulado.id) >= 1  # Pelo menos 1 simulado
        ).order_by(func.avg(Simulado.nota_tri).desc()).limit(limit).all()
    
    @staticmethod
    def get_posicao_usuario(user_id, tipo='geral'):
        """
        Calcula a posição específica de um usuário no ranking.
        
        Args:
            user_id (int): ID do usuário
            tipo (str): Tipo de ranking ('geral', 'mensal', 'tempo_estudo', 'simulados')
            
        Returns:
            int: Posição do usuário (1-based)
        """
        if tipo == 'geral':
            user = User.query.get(user_id)
            if not user:
                return None
            
            posicao = db.session.query(func.count(User.id)).filter(
                User.xp_total > user.xp_total,
                User.is_active == True
            ).scalar()
            return posicao + 1
        
        elif tipo == 'mensal':
            inicio_mes = RankingUtils.get_periodo_mes_atual()
            
            xp_usuario_mes = db.session.query(func.coalesce(func.sum(XpGanho.quantidade), 0)).filter(
                XpGanho.user_id == user_id,
                XpGanho.data >= inicio_mes
            ).scalar()
            
            # Subquery para XP de outros usuários
            subquery = db.session.query(
                XpGanho.user_id,
                func.sum(XpGanho.quantidade).label('total_xp')
            ).filter(
                XpGanho.data >= inicio_mes
            ).group_by(XpGanho.user_id).subquery()
            
            posicao = db.session.query(func.count()).filter(
                subquery.c.total_xp > xp_usuario_mes
            ).scalar()
            
            return posicao + 1
        
        elif tipo == 'tempo_estudo':
            inicio_mes = RankingUtils.get_periodo_mes_atual()
            
            tempo_usuario = db.session.query(func.coalesce(func.sum(TempoEstudo.minutos), 0)).filter(
                TempoEstudo.user_id == user_id,
                TempoEstudo.data_inicio >= inicio_mes
            ).scalar()
            
            # Subquery para tempo de outros usuários
            subquery = db.session.query(
                TempoEstudo.user_id,
                func.sum(TempoEstudo.minutos).label('total_tempo')
            ).filter(
                TempoEstudo.data_inicio >= inicio_mes
            ).group_by(TempoEstudo.user_id).subquery()
            
            posicao = db.session.query(func.count()).filter(
                subquery.c.total_tempo > tempo_usuario
            ).scalar()
            
            return posicao + 1
        
        elif tipo == 'simulados':
            inicio_mes = RankingUtils.get_periodo_mes_atual()
            
            # Média do usuário atual
            media_usuario = db.session.query(func.avg(Simulado.nota_tri)).filter(
                Simulado.user_id == user_id,
                Simulado.status == 'Concluído',
                Simulado.data_realizado >= inicio_mes,
                Simulado.nota_tri.isnot(None)
            ).scalar()
            
            if not media_usuario:
                return None
            
            # Subquery para médias de outros usuários
            medias_usuarios = db.session.query(
                Simulado.user_id,
                func.avg(Simulado.nota_tri).label('media_usuario')
            ).filter(
                Simulado.status == 'Concluído',
                Simulado.data_realizado >= inicio_mes,
                Simulado.nota_tri.isnot(None)
            ).group_by(Simulado.user_id).having(
                func.count(Simulado.id) >= 1
            ).subquery()
            
            # Contar quantos usuários têm média melhor
            posicao = db.session.query(func.count()).filter(
                medias_usuarios.c.media_usuario > media_usuario
            ).scalar()
            
            return posicao + 1
        
        return None
    
    @staticmethod
    def get_estatisticas_gerais():
        """
        Retorna estatísticas gerais da plataforma para exibição.
        
        Returns:
            dict: Estatísticas gerais
        """
        total_usuarios = User.query.filter_by(is_active=True).count()
        
        media_xp = db.session.query(func.avg(User.xp_total)).filter(
            User.is_active == True,
            User.xp_total > 0
        ).scalar() or 0
        
        inicio_mes = RankingUtils.get_periodo_mes_atual()
        usuarios_ativos_mes = db.session.query(func.count(func.distinct(XpGanho.user_id))).filter(
            XpGanho.data >= inicio_mes
        ).scalar() or 0




        
        return {
            'total_usuarios': total_usuarios,
            'media_xp': round(media_xp),
            'usuarios_ativos_mes': usuarios_ativos_mes 
        }
