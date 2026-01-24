# app/routes/ranking.py - VERSÃO CORRIGIDA COMPLETA
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models.user import User
from app.models.estatisticas import XpGanho, TempoEstudo
from app.models.simulado import Simulado
from app.models.redacao import Redacao
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func, desc, text

ranking_bp = Blueprint('ranking', __name__, url_prefix='/ranking')

def formatar_tempo(minutos):
    """Formata minutos em string legível."""
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

def calcular_posicao_usuario_segura(user_id, tipo='geral'):
    """
    Versão segura para calcular posição do usuário.
    Evita problemas com subqueries complexas.
    """
    try:
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
            inicio_mes = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # XP do usuário no mês
            xp_usuario_mes = db.session.query(func.coalesce(func.sum(XpGanho.quantidade), 0)).filter(
                XpGanho.user_id == user_id,
                XpGanho.data >= inicio_mes
            ).scalar()
            
            if xp_usuario_mes == 0:
                return None
            
            # Buscar todos os XPs mensais e comparar em Python
            todos_xps = db.session.query(
                XpGanho.user_id,
                func.sum(XpGanho.quantidade).label('total_xp')
            ).filter(
                XpGanho.data >= inicio_mes
            ).group_by(XpGanho.user_id).all()
            
            melhores = sum(1 for xp_row in todos_xps if xp_row.total_xp > xp_usuario_mes)
            return melhores + 1
        
        elif tipo == 'tempo_estudo':
            inicio_mes = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Tempo do usuário no mês
            tempo_usuario = db.session.query(func.coalesce(func.sum(TempoEstudo.minutos), 0)).filter(
                TempoEstudo.user_id == user_id,
                TempoEstudo.data_inicio >= inicio_mes
            ).scalar()
            
            if tempo_usuario == 0:
                return None
            
            # Buscar todos os tempos mensais
            todos_tempos = db.session.query(
                TempoEstudo.user_id,
                func.sum(TempoEstudo.minutos).label('total_tempo')
            ).filter(
                TempoEstudo.data_inicio >= inicio_mes
            ).group_by(TempoEstudo.user_id).all()
            
            melhores = sum(1 for tempo_row in todos_tempos if tempo_row.total_tempo > tempo_usuario)
            return melhores + 1
        
        elif tipo == 'simulados':
            inicio_mes = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Média do usuário
            media_usuario = db.session.query(func.avg(Simulado.nota_tri)).filter(
                Simulado.user_id == user_id,
                Simulado.status == 'Concluído',
                Simulado.data_realizado >= inicio_mes,
                Simulado.nota_tri.isnot(None)
            ).scalar()
            
            if not media_usuario:
                return None
            
            # Buscar todas as médias
            todas_medias = db.session.query(
                Simulado.user_id,
                func.avg(Simulado.nota_tri).label('media_notas')
            ).filter(
                Simulado.status == 'Concluído',
                Simulado.data_realizado >= inicio_mes,
                Simulado.nota_tri.isnot(None)
            ).group_by(Simulado.user_id).having(
                func.count(Simulado.id) >= 1
            ).all()
            
            melhores = sum(1 for media_row in todas_medias if media_row.media_notas > media_usuario)
            return melhores + 1
        
        return None
        
    except Exception as e:
        print(f"Erro ao calcular posição para {tipo}: {e}")
        return None

@ranking_bp.route('/')
@login_required
def index():
    """Ranking geral por XP total."""
    
    try:
        # Ranking geral (top 50)
        ranking_geral = db.session.query(
            User.id,
            User.nome_completo,
            User.username,
            User.xp_total
        ).filter(
            User.is_active == True,
            User.xp_total > 0
        ).order_by(desc(User.xp_total)).limit(50).all()
        
        # Posição do usuário atual
        posicao_usuario = calcular_posicao_usuario_segura(current_user.id, 'geral')
        
        # Estatísticas gerais
        total_usuarios = User.query.filter_by(is_active=True).count()* 100
        media_xp = db.session.query(func.avg(User.xp_total)).filter(
            User.is_active == True,
            User.xp_total > 0
        ).scalar() or 0
        
        return render_template('ranking/index.html',
                              ranking_geral=ranking_geral,
                              posicao_usuario=posicao_usuario,
                              total_usuarios=total_usuarios,
                              media_xp=round(media_xp),
                              usuario_atual=current_user)
                              
    except Exception as e:
        print(f"Erro no ranking geral: {e}")
        return render_template('ranking/index.html',
                              ranking_geral=[],
                              posicao_usuario=None,
                              total_usuarios=0,
                              media_xp=0,
                              usuario_atual=current_user)

@ranking_bp.route('/mensal')
@login_required
def mensal():
    """Ranking mensal por XP ganho no mês."""
    
    try:
        # Data do início do mês
        inicio_mes = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Ranking mensal - XP ganho no mês atual
        ranking_mensal = db.session.query(
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
        ).order_by(desc('xp_mes')).limit(50).all()
        
        # XP do usuário atual no mês
        xp_usuario_mes = db.session.query(func.coalesce(func.sum(XpGanho.quantidade), 0)).filter(
            XpGanho.user_id == current_user.id,
            XpGanho.data >= inicio_mes
        ).scalar()
        
        # Posição do usuário atual
        posicao_usuario = calcular_posicao_usuario_segura(current_user.id, 'mensal')
        
        return render_template('ranking/mensal.html',
                              ranking_mensal=ranking_mensal,
                              posicao_usuario=posicao_usuario,
                              xp_usuario_mes=xp_usuario_mes,
                              mes_atual=datetime.utcnow().strftime('%B %Y'),
                              usuario_atual=current_user)
                              
    except Exception as e:
        print(f"Erro no ranking mensal: {e}")
        return render_template('ranking/mensal.html',
                              ranking_mensal=[],
                              posicao_usuario=None,
                              xp_usuario_mes=0,
                              mes_atual=datetime.utcnow().strftime('%B %Y'),
                              usuario_atual=current_user)

@ranking_bp.route('/tempo-estudo')
@login_required 
def tempo_estudo():
    """Ranking por tempo de estudo no mês."""
    
    try:
        # Data do início do mês
        inicio_mes = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Ranking por tempo de estudo no mês
        ranking_tempo = db.session.query(
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
        ).order_by(desc('tempo_total')).limit(50).all()
        
        # Tempo do usuário atual no mês
        tempo_usuario_mes = db.session.query(func.coalesce(func.sum(TempoEstudo.minutos), 0)).filter(
            TempoEstudo.user_id == current_user.id,
            TempoEstudo.data_inicio >= inicio_mes
        ).scalar()
        
        # Posição do usuário atual
        posicao_usuario = calcular_posicao_usuario_segura(current_user.id, 'tempo_estudo')
        
        return render_template('ranking/tempo_estudo.html',
                              ranking_tempo=ranking_tempo,
                              posicao_usuario=posicao_usuario,
                              tempo_usuario_mes=tempo_usuario_mes,
                              tempo_usuario_formatado=formatar_tempo(tempo_usuario_mes),
                              mes_atual=datetime.utcnow().strftime('%B %Y'),
                              usuario_atual=current_user,
                              formatar_tempo=formatar_tempo)
                              
    except Exception as e:
        print(f"Erro no ranking de tempo: {e}")
        return render_template('ranking/tempo_estudo.html',
                              ranking_tempo=[],
                              posicao_usuario=None,
                              tempo_usuario_mes=0,
                              tempo_usuario_formatado="0h",
                              mes_atual=datetime.utcnow().strftime('%B %Y'),
                              usuario_atual=current_user,
                              formatar_tempo=formatar_tempo)

@ranking_bp.route('/simulados')
@login_required
def simulados():
    """Ranking por performance em simulados - VERSÃO CORRIGIDA."""
    
    try:
        # Data do início do mês
        inicio_mes = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Ranking por melhor média de notas TRI no mês - SIMPLIFICADO
        ranking_simulados = db.session.query(
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
        ).order_by(desc('media_notas')).limit(50).all()
        
        # Performance do usuário atual - SIMPLIFICADO
        stats_usuario = db.session.query(
            func.avg(Simulado.nota_tri).label('media_notas'),
            func.count(Simulado.id).label('total_simulados'),
            func.max(Simulado.nota_tri).label('melhor_nota')
        ).filter(
            Simulado.user_id == current_user.id,
            Simulado.status == 'Concluído',
            Simulado.data_realizado >= inicio_mes,
            Simulado.nota_tri.isnot(None)
        ).first()
        
        # Calcular posição do usuário de forma mais simples e segura
        posicao_usuario = calcular_posicao_usuario_segura(current_user.id, 'simulados')
        
        return render_template('ranking/simulados.html',
                              ranking_simulados=ranking_simulados,
                              posicao_usuario=posicao_usuario,
                              stats_usuario=stats_usuario,
                              mes_atual=datetime.utcnow().strftime('%B %Y'),
                              usuario_atual=current_user)
                              
    except Exception as e:
        print(f"Erro no ranking de simulados: {e}")
        # Criar stats_usuario vazio em caso de erro
        from collections import namedtuple
        StatsUsuario = namedtuple('StatsUsuario', ['media_notas', 'total_simulados', 'melhor_nota'])
        stats_usuario = StatsUsuario(None, 0, None)
        
        return render_template('ranking/simulados.html',
                              ranking_simulados=[],
                              posicao_usuario=None,
                              stats_usuario=stats_usuario,
                              mes_atual=datetime.utcnow().strftime('%B %Y'),
                              usuario_atual=current_user)

@ranking_bp.route('/api/posicao')
@login_required
def api_posicao():
    """API para obter posição atual do usuário em tempo real."""
    try:
        tipo = request.args.get('tipo', 'geral')
        
        posicao = calcular_posicao_usuario_segura(current_user.id, tipo)
        
        return jsonify({
            'sucesso': True,
            'posicao': posicao,
            'xp_total': current_user.xp_total
        })
        
    except Exception as e:
        print(f"Erro na API de posição: {e}")
        return jsonify({
            'sucesso': False,
            'erro': 'Erro interno',
            'posicao': None,
            'xp_total': current_user.xp_total
        })
