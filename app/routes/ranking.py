# app/routes/ranking.py - VERSÃO FINAL CORRIGIDA
"""
Rotas do Sistema de Ranking
Versão 2.0 - Integração com XP e Estudos
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_login import login_required, current_user
from app.utils.ranking_utils import RankingUtils
from app import db
from app.models.user import User
from datetime import datetime
import traceback

ranking_bp = Blueprint('ranking', __name__, url_prefix='/ranking')

@ranking_bp.route('/')
@login_required
def index():
    """Redireciona para o ranking geral"""
    return redirect(url_for('ranking.ranking_geral'))

@ranking_bp.route('/geral')
@login_required
def ranking_geral():
    """Ranking geral por XP total"""
    try:
        # Buscar top 50
        top_users = RankingUtils.calcular_ranking_geral(limit=50)
        
        # Enriquecer dados
        ranking_data = []
        for idx, user_data in enumerate(top_users, 1):
            user = User.query.get(user_data.id)
            if user:
                # Calcular nível baseado no XP (se não existir campo nivel)
                nivel_calculado = _calcular_nivel(user_data.xp_total)
                
                ranking_data.append({
                    'posicao': idx,
                    'user': user,
                    'xp_total': user_data.xp_total,
                    'nivel': nivel_calculado,
                    'badge_info': _get_user_badge_by_nivel(nivel_calculado),
                    'is_current_user': user.id == current_user.id
                })
        
        # Buscar posição do usuário atual
        user_position = RankingUtils.get_posicao_usuario(current_user.id, tipo='geral')
        
        # Estatísticas gerais
        stats = RankingUtils.get_estatisticas_gerais()
        
        return render_template('ranking/ranking.html',
                             title='Ranking Geral',
                             tipo_ranking='geral',
                             ranking_data=ranking_data,
                             user_position=user_position,
                             stats=stats,
                             periodo='geral')
                             
    except Exception as e:
        print(f"Erro ao carregar ranking geral: {str(e)}")
        print(traceback.format_exc())
        return render_template('ranking/ranking.html',
                             title='Ranking Geral',
                             tipo_ranking='geral',
                             ranking_data=[],
                             error="Erro ao carregar ranking")

@ranking_bp.route('/mensal')
@login_required
def ranking_mensal():
    """Ranking do mês por XP ganho"""
    try:
        top_users = RankingUtils.calcular_ranking_mensal(limit=50)
        
        ranking_data = []
        for idx, user_data in enumerate(top_users, 1):
            user = User.query.get(user_data.id)
            if user:
                ranking_data.append({
                    'posicao': idx,
                    'user': user,
                    'xp_mes': user_data.xp_mes,
                    'badge_info': _get_xp_badge(user_data.xp_mes),
                    'is_current_user': user.id == current_user.id
                })
        
        user_position = RankingUtils.get_posicao_usuario(current_user.id, tipo='mensal')
        stats = RankingUtils.get_estatisticas_gerais()
        
        return render_template('ranking/ranking.html',
                             title='Ranking Mensal',
                             tipo_ranking='mensal',
                             ranking_data=ranking_data,
                             user_position=user_position,
                             stats=stats,
                             periodo='mensal')
                             
    except Exception as e:
        print(f"Erro ao carregar ranking mensal: {str(e)}")
        print(traceback.format_exc())
        return render_template('ranking/ranking.html',
                             title='Ranking Mensal',
                             tipo_ranking='mensal',
                             ranking_data=[],
                             error="Erro ao carregar ranking")

@ranking_bp.route('/tempo-estudo')
@login_required
def ranking_tempo():
    """Ranking por tempo de estudo no mês"""
    try:
        top_users = RankingUtils.calcular_ranking_tempo(limit=50)
        
        ranking_data = []
        for idx, user_data in enumerate(top_users, 1):
            user = User.query.get(user_data.id)
            if user:
                tempo_formatado = RankingUtils.formatar_tempo_estudo(user_data.tempo_total)
                badge_tempo = RankingUtils.get_badge_tempo_estudo(user_data.tempo_total)
                
                ranking_data.append({
                    'posicao': idx,
                    'user': user,
                    'tempo_total': user_data.tempo_total,
                    'tempo_formatado': tempo_formatado,
                    'badge_info': badge_tempo,
                    'is_current_user': user.id == current_user.id
                })
        
        user_position = RankingUtils.get_posicao_usuario(current_user.id, tipo='tempo_estudo')
        stats = RankingUtils.get_estatisticas_gerais()
        
        return render_template('ranking/ranking.html',
                             title='Ranking Tempo de Estudo',
                             tipo_ranking='tempo_estudo',
                             ranking_data=ranking_data,
                             user_position=user_position,
                             stats=stats,
                             periodo='tempo')
                             
    except Exception as e:
        print(f"Erro ao carregar ranking tempo: {str(e)}")
        print(traceback.format_exc())
        return render_template('ranking/ranking.html',
                             title='Ranking Tempo de Estudo',
                             tipo_ranking='tempo_estudo',
                             ranking_data=[],
                             error="Erro ao carregar ranking")

@ranking_bp.route('/simulados')
@login_required
def ranking_simulados():
    """Ranking por performance em simulados"""
    try:
        top_users = RankingUtils.calcular_ranking_simulados(limit=50)
        
        ranking_data = []
        for idx, user_data in enumerate(top_users, 1):
            user = User.query.get(user_data.id)
            if user:
                nota_badge = RankingUtils.get_badge_nota_tri(user_data.media_notas)
                
                ranking_data.append({
                    'posicao': idx,
                    'user': user,
                    'media_notas': round(user_data.media_notas, 1),
                    'total_simulados': user_data.total_simulados,
                    'badge_info': nota_badge,
                    'is_current_user': user.id == current_user.id
                })
        
        user_position = RankingUtils.get_posicao_usuario(current_user.id, tipo='simulados')
        stats = RankingUtils.get_estatisticas_gerais()
        
        return render_template('ranking/ranking.html',
                             title='Ranking Simulados',
                             tipo_ranking='simulados',
                             ranking_data=ranking_data,
                             user_position=user_position,
                             stats=stats,
                             periodo='simulados')
                             
    except Exception as e:
        print(f"Erro ao carregar ranking simulados: {str(e)}")
        print(traceback.format_exc())
        return render_template('ranking/ranking.html',
                             title='Ranking Simulados',
                             tipo_ranking='simulados',
                             ranking_data=[],
                             error="Erro ao carregar ranking")

# ==================== FUNÇÕES AUXILIARES ====================

def _calcular_nivel(xp_total):
    """
    Calcula o nível do usuário baseado no XP total
    Fórmula: Nível = XP / 1000 (arredondado para baixo) + 1
    """
    if xp_total <= 0:
        return 1
    
    # 1000 XP = Nível 2, 2000 XP = Nível 3, etc.
    nivel = (xp_total // 1000) + 1
    
    # Limitar nível máximo (opcional)
    return min(nivel, 100)

def _get_user_badge_by_nivel(nivel):
    """Retorna badge baseado no nível calculado"""
    if nivel >= 50:
        return {'classe': 'bg-danger', 'texto': 'Mestre', 'icone': 'trophy-fill'}
    elif nivel >= 30:
        return {'classe': 'bg-warning text-dark', 'texto': 'Expert', 'icone': 'star-fill'}
    elif nivel >= 15:
        return {'classe': 'bg-success', 'texto': 'Avançado', 'icone': 'arrow-up'}
    else:
        return {'classe': 'bg-primary', 'texto': 'Iniciante', 'icone': 'person'}

def _get_xp_badge(xp_mes):
    """Badge baseado no XP do mês"""
    if xp_mes >= 5000:
        return {'classe': 'bg-danger', 'texto': 'Em Chamas', 'icone': 'fire'}
    elif xp_mes >= 2500:
        return {'classe': 'bg-warning text-dark', 'texto': 'Dedicado', 'icone': 'lightning'}
    elif xp_mes >= 1000:
        return {'classe': 'bg-success', 'texto': 'Consistente', 'icone': 'star'}
    else:
        return {'classe': 'bg-primary', 'texto': 'Iniciando', 'icone': 'arrow-up'}
