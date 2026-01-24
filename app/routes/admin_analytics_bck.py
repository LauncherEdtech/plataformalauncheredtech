# app/routes/admin_analytics.py - VERSÃO COMPLETA COM ENGAJAMENTO
"""
Painel de Gestão Completo - Analytics e Métricas da Plataforma
VERSÃO 3.0 - Com Shop, Vendas e Análise de Engajamento (Quente/Morno/Frio)
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import func, and_, or_, case, distinct, desc
from datetime import datetime, timedelta
from app import db
from app.models.user import User
from app.models.simulado import Simulado, Questao
from app.models.estatisticas import TempoEstudo, ExercicioRealizado, XpGanho
from app.services.engajamento_service import EngajamentoService
import json
import logging

logger = logging.getLogger(__name__)

# Importar modelos do shop
try:
    from app.models.shop import Produto, Resgate
    SHOP_DISPONIVEL = True
except:
    SHOP_DISPONIVEL = False
    Produto = None
    Resgate = None

admin_analytics_bp = Blueprint('admin_analytics', __name__, url_prefix='/admin/analytics')

def admin_required(f):
    """Decorator para garantir que apenas admins acessem"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Acesso negado'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# ROTA PRINCIPAL - DASHBOARD
# ==========================================
@admin_analytics_bp.route('/')
@login_required
@admin_required
def index():
    """Página principal do painel de gestão"""
    return render_template('admin/analytics_dashboard.html')

# ==========================================
# MÉTRICAS GERAIS DA PLATAFORMA
# ==========================================
@admin_analytics_bp.route('/api/metricas-gerais')
@login_required
@admin_required
def metricas_gerais():
    """Retorna métricas gerais da plataforma"""
    
    # Total de usuários
    total_usuarios = User.query.count()
    
    # Usuários ativos (que fizeram algo nos últimos 7 dias)
    data_7_dias_atras = datetime.utcnow() - timedelta(days=7)
    usuarios_ativos = User.query.join(TempoEstudo).filter(
        TempoEstudo.data_inicio >= data_7_dias_atras
    ).distinct().count()
    
    # Novos usuários (últimos 30 dias)
    data_30_dias_atras = datetime.utcnow() - timedelta(days=30)
    novos_usuarios = User.query.filter(
        User.data_registro >= data_30_dias_atras
    ).count()
    
    # Total de simulados realizados
    simulados_concluidos = Simulado.query.filter(
        Simulado.status == 'Concluído'
    ).count()
    
    # Total de tempo de estudo (em horas)
    tempo_total = db.session.query(func.sum(TempoEstudo.minutos)).scalar() or 0
    tempo_total_horas = tempo_total / 60
    
    # Taxa de engajamento (usuários ativos / total)
    taxa_engajamento = (usuarios_ativos / total_usuarios * 100) if total_usuarios > 0 else 0
    
    # Média de XP por usuário
    xp_medio = db.session.query(func.avg(User.xp_total)).scalar() or 0
    
    # Total de exercícios realizados
    exercicios_realizados = ExercicioRealizado.query.count()
    
    return jsonify({
        'total_usuarios': total_usuarios,
        'usuarios_ativos': usuarios_ativos,
        'novos_usuarios': novos_usuarios,
        'simulados_concluidos': simulados_concluidos,
        'tempo_total_horas': round(tempo_total_horas, 2),
        'taxa_engajamento': round(taxa_engajamento, 2),
        'xp_medio': round(xp_medio, 2),
        'exercicios_realizados': exercicios_realizados
    })

# ==========================================
# ANÁLISE DE VENDAS E COMPRAS
# ==========================================
@admin_analytics_bp.route('/api/vendas')
@login_required
@admin_required
def analise_vendas():
    """Análise de vendas e novos usuários compradores"""
    
    # Usuários registrados nos últimos 7 dias
    data_7_dias = datetime.utcnow() - timedelta(days=7)
    novos_7d = User.query.filter(User.data_registro >= data_7_dias).count()
    
    # Usuários registrados nos últimos 30 dias
    data_30_dias = datetime.utcnow() - timedelta(days=30)
    novos_30d = User.query.filter(User.data_registro >= data_30_dias).count()
    
    # Usuários registrados hoje
    hoje = datetime.utcnow().date()
    novos_hoje = User.query.filter(
        func.date(User.data_registro) == hoje
    ).count()
    
    # Evolução de cadastros nos últimos 30 dias (dia a dia)
    evolucao_cadastros = db.session.query(
        func.date(User.data_registro).label('data'),
        func.count(User.id).label('cadastros')
    ).filter(
        User.data_registro >= data_30_dias
    ).group_by('data').order_by('data').all()
    
    # Taxa de crescimento (comparar últimos 7 dias com 7 dias anteriores)
    data_14_dias = datetime.utcnow() - timedelta(days=14)
    novos_7d_anteriores = User.query.filter(
        User.data_registro >= data_14_dias,
        User.data_registro < data_7_dias
    ).count()
    
    taxa_crescimento = 0
    if novos_7d_anteriores > 0:
        taxa_crescimento = ((novos_7d - novos_7d_anteriores) / novos_7d_anteriores * 100)
    
    return jsonify({
        'novos_usuarios_hoje': novos_hoje,
        'novos_usuarios_7d': novos_7d,
        'novos_usuarios_30d': novos_30d,
        'taxa_crescimento_7d': round(taxa_crescimento, 2),
        'evolucao_cadastros': {
            'datas': [str(item[0]) for item in evolucao_cadastros],
            'valores': [item[1] for item in evolucao_cadastros]
        }
    })

# ==========================================
# ANÁLISE DE SHOP
# ==========================================
@admin_analytics_bp.route('/api/shop')
@login_required
@admin_required
def analise_shop():
    """Análise completa do Shop"""
    
    if not SHOP_DISPONIVEL or not Resgate:
        return jsonify({
            'erro': 'Shop não disponível',
            'shop_disponivel': False
        })
    
    # Total de resgates
    total_resgates = Resgate.query.count()
    
    # Resgates pendentes
    resgates_pendentes = Resgate.query.filter_by(status='Pendente').count()
    
    # Resgates enviados
    resgates_enviados = Resgate.query.filter_by(status='Enviado').count()
    
    # Resgates entregues
    resgates_entregues = Resgate.query.filter_by(status='Entregue').count()
    
    # Resgates nos últimos 7 dias
    data_7_dias = datetime.utcnow() - timedelta(days=7)
    resgates_7d = Resgate.query.filter(
        Resgate.data_resgate >= data_7_dias
    ).count()
    
    # Resgates nos últimos 30 dias
    data_30_dias = datetime.utcnow() - timedelta(days=30)
    resgates_30d = Resgate.query.filter(
        Resgate.data_resgate >= data_30_dias
    ).count()
    
    # Produtos mais resgatados (Top 10)
    produtos_populares = db.session.query(
        Produto.id,
        Produto.nome,
        Produto.imagem,
        Produto.preco_diamantes,
        func.count(Resgate.id).label('total_resgates')
    ).join(Resgate).group_by(
        Produto.id, Produto.nome, Produto.imagem, Produto.preco_diamantes
    ).order_by(desc('total_resgates')).limit(10).all()
    
    # Total de diamantes gastos
    total_diamantes = db.session.query(
        func.sum(Resgate.diamantes_gastos)
    ).scalar() or 0
    
    # Usuários únicos que já resgataram
    usuarios_compradores = db.session.query(
        func.count(distinct(Resgate.user_id))
    ).scalar() or 0
    
    # Taxa de conversão (usuários que resgataram / total de usuários)
    total_usuarios = User.query.count()
    taxa_conversao = (usuarios_compradores / total_usuarios * 100) if total_usuarios > 0 else 0
    
    # Evolução de resgates nos últimos 30 dias
    evolucao_resgates = db.session.query(
        func.date(Resgate.data_resgate).label('data'),
        func.count(Resgate.id).label('resgates')
    ).filter(
        Resgate.data_resgate >= data_30_dias
    ).group_by('data').order_by('data').all()
    
    # Produtos com estoque baixo (menos de 10 unidades)
    produtos_estoque_baixo = Produto.query.filter(
        Produto.estoque < 10,
        Produto.disponivel == True
    ).count()
    
    # Ticket médio (diamantes gastos por resgate)
    ticket_medio = db.session.query(
        func.avg(Resgate.diamantes_gastos)
    ).scalar() or 0
    
    # Distribuição por status
    distribuicao_status = db.session.query(
        Resgate.status,
        func.count(Resgate.id).label('total')
    ).group_by(Resgate.status).all()
    
    return jsonify({
        'shop_disponivel': True,
        'total_resgates': total_resgates,
        'resgates_pendentes': resgates_pendentes,
        'resgates_enviados': resgates_enviados,
        'resgates_entregues': resgates_entregues,
        'resgates_7d': resgates_7d,
        'resgates_30d': resgates_30d,
        'produtos_populares': [{
            'id': p[0],
            'nome': p[1],
            'imagem': p[2],
            'preco': p[3],
            'total_resgates': p[4]
        } for p in produtos_populares],
        'total_diamantes_gastos': int(total_diamantes),
        'usuarios_compradores': usuarios_compradores,
        'taxa_conversao': round(taxa_conversao, 2),
        'evolucao_resgates': {
            'datas': [str(item[0]) for item in evolucao_resgates],
            'valores': [item[1] for item in evolucao_resgates]
        },
        'produtos_estoque_baixo': produtos_estoque_baixo,
        'ticket_medio': round(ticket_medio, 2),
        'distribuicao_status': [{
            'status': item[0],
            'total': item[1]
        } for item in distribuicao_status]
    })

# ==========================================
# ANÁLISE DE USUÁRIOS
# ==========================================
@admin_analytics_bp.route('/api/analise-usuarios')
@login_required
@admin_required
def analise_usuarios():
    """Análise detalhada do perfil dos usuários"""
    
    # Distribuição por XP
    distribuicao_xp = db.session.query(
        case(
            (User.xp_total < 500, '0-500'),
            (User.xp_total < 1000, '500-1000'),
            (User.xp_total < 2000, '1000-2000'),
            (User.xp_total < 5000, '2000-5000'),
            else_='5000+'
        ).label('faixa'),
        func.count(User.id).label('count')
    ).group_by('faixa').all()
    
    # Usuários com mais XP (Top 10)
    top_usuarios_xp = db.session.query(
        User.id,
        User.username,
        User.nome_completo,
        User.xp_total,
        User.diamantes
    ).order_by(desc(User.xp_total)).limit(10).all()
    
    # Distribuição de tempo de estudo
    usuarios_tempo = db.session.query(
        User.id,
        User.username,
        func.sum(TempoEstudo.minutos).label('tempo_total')
    ).join(TempoEstudo).group_by(User.id, User.username).order_by(
        desc('tempo_total')
    ).limit(10).all()
    
    # Taxa de retenção (usuários que voltaram após registro)
    total_usuarios = User.query.count()
    usuarios_retornaram = User.query.join(TempoEstudo).filter(
        TempoEstudo.data_inicio > User.data_registro + timedelta(days=1)
    ).distinct().count()
    
    taxa_retencao = (usuarios_retornaram / total_usuarios * 100) if total_usuarios > 0 else 0
    
    # Usuários inativos (sem atividade há mais de 30 dias)
    data_30_dias = datetime.utcnow() - timedelta(days=30)
    usuarios_inativos = User.query.filter(
        ~User.id.in_(
            db.session.query(TempoEstudo.user_id).filter(
                TempoEstudo.data_inicio >= data_30_dias
            )
        )
    ).count()
    
    return jsonify({
        'distribuicao_xp': {
            'labels': [item[0] for item in distribuicao_xp],
            'values': [item[1] for item in distribuicao_xp]
        },
        'top_usuarios_xp': [{
            'id': u[0],
            'username': u[1],
            'nome': u[2],
            'xp': u[3],
            'diamantes': u[4]
        } for u in top_usuarios_xp],
        'top_usuarios_tempo': [{
            'id': u[0],
            'username': u[1],
            'tempo_minutos': u[2]
        } for u in usuarios_tempo],
        'taxa_retencao': round(taxa_retencao, 2),
        'usuarios_inativos': usuarios_inativos
    })


# ==========================================
# ANÁLISE DE ENGAJAMENTO (ABA ANTIGA)
# ==========================================
@admin_analytics_bp.route('/api/engajamento')
@login_required
@admin_required
def analise_engajamento():
    """Métricas de engajamento dos usuários"""
    
    # Atividade nos últimos 30 dias (dia a dia)
    data_30_dias = datetime.utcnow() - timedelta(days=30)
    atividade_diaria = db.session.query(
        func.date(TempoEstudo.data_inicio).label('data'),
        func.count(distinct(TempoEstudo.user_id)).label('usuarios_ativos'),
        func.sum(TempoEstudo.minutos).label('tempo_total')
    ).filter(
        TempoEstudo.data_inicio >= data_30_dias
    ).group_by('data').order_by('data').all()
    
    # Atividades mais populares
    atividades_populares = db.session.query(
        TempoEstudo.atividade,
        func.count(TempoEstudo.id).label('total_sessoes'),
        func.sum(TempoEstudo.minutos).label('tempo_total'),
        func.count(distinct(TempoEstudo.user_id)).label('usuarios_unicos')
    ).group_by(TempoEstudo.atividade).order_by(desc('total_sessoes')).all()
    
    # Horários de pico (por hora do dia)
    horarios_pico = db.session.query(
        func.extract('hour', TempoEstudo.data_inicio).label('hora'),
        func.count(TempoEstudo.id).label('sessoes')
    ).group_by('hora').order_by('hora').all()
    
    # Dias da semana mais ativos
    dias_semana = db.session.query(
        func.extract('dow', TempoEstudo.data_inicio).label('dia'),
        func.count(distinct(TempoEstudo.user_id)).label('usuarios'),
        func.sum(TempoEstudo.minutos).label('tempo')
    ).group_by('dia').order_by('dia').all()
    
    dias_nomes = ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado']
    
    # Sequências de estudo (streak)
    usuarios_com_streak = User.query.all()
    sequencias = [u.calcular_sequencia_estudo() for u in usuarios_com_streak]
    media_sequencia = sum(sequencias) / len(sequencias) if sequencias else 0
    maior_sequencia = max(sequencias) if sequencias else 0
    
    return jsonify({
        'atividade_diaria': {
            'datas': [str(item[0]) for item in atividade_diaria],
            'usuarios': [item[1] for item in atividade_diaria],
            'tempo_minutos': [item[2] or 0 for item in atividade_diaria]
        },
        'atividades_populares': [{
            'atividade': item[0] or 'Desconhecido',
            'sessoes': item[1],
            'tempo_total': item[2] or 0,
            'usuarios': item[3]
        } for item in atividades_populares],
        'horarios_pico': {
            'horas': [int(item[0]) for item in horarios_pico],
            'sessoes': [item[1] for item in horarios_pico]
        },
        'dias_semana': {
            'dias': [dias_nomes[int(item[0])] for item in dias_semana],
            'usuarios': [item[1] for item in dias_semana],
            'tempo': [item[2] or 0 for item in dias_semana]
        },
        'sequencias': {
            'media': round(media_sequencia, 2),
            'maior': maior_sequencia
        }
    })



# ==========================================
# ANÁLISE DE DESEMPENHO
# ==========================================
@admin_analytics_bp.route('/api/desempenho')
@login_required
@admin_required
def analise_desempenho():
    """Análise de desempenho e resultados dos usuários"""
    
    try:
        # Total de simulados concluídos
        total_simulados = Simulado.query.filter_by(status='Concluído').count()
        
        # Média geral TRI
        media_geral = db.session.query(func.avg(Simulado.nota_tri)).filter(
            Simulado.nota_tri.isnot(None),
            Simulado.status == 'Concluído'
        ).scalar() or 0
        
        # Taxa de conclusão
        total_iniciados = Simulado.query.count()
        taxa_conclusao = (total_simulados / total_iniciados * 100) if total_iniciados > 0 else 0
        
        # Distribuição de notas dos simulados
        distribuicao_notas = db.session.query(
            case(
                (Simulado.nota_tri < 500, '0-500'),
                (Simulado.nota_tri < 600, '500-600'),
                (Simulado.nota_tri < 700, '600-700'),
                (Simulado.nota_tri < 800, '700-800'),
                else_='800+'
            ).label('faixa'),
            func.count(Simulado.id).label('count')
        ).filter(
            Simulado.nota_tri.isnot(None),
            Simulado.status == 'Concluído'
        ).group_by('faixa').all()
        
        # Média de notas por área
        medias_por_area = db.session.query(
            Simulado.areas,
            func.avg(Simulado.nota_tri).label('media'),
            func.count(Simulado.id).label('total')
        ).filter(
            Simulado.nota_tri.isnot(None),
            Simulado.status == 'Concluído',
            Simulado.areas.isnot(None)
        ).group_by(Simulado.areas).all()
        
        # Taxa de acertos em exercícios
        taxa_acertos = db.session.query(
            func.sum(case((ExercicioRealizado.acertou == True, 1), else_=0)).label('acertos'),
            func.count(ExercicioRealizado.id).label('total')
        ).first()
        
        percentual_acertos = (taxa_acertos[0] / taxa_acertos[1] * 100) if (taxa_acertos and taxa_acertos[1] > 0) else 0
        
        # Evolução de desempenho (últimos 60 dias)
        data_60_dias = datetime.utcnow() - timedelta(days=60)
        evolucao = db.session.query(
            func.date(Simulado.data_realizado).label('data'),
            func.avg(Simulado.nota_tri).label('media_nota'),
            func.count(Simulado.id).label('simulados')
        ).filter(
            Simulado.data_realizado >= data_60_dias,
            Simulado.nota_tri.isnot(None),
            Simulado.status == 'Concluído'
        ).group_by('data').order_by('data').all()
        
        # Top 10 usuários com melhores notas
        top_notas = db.session.query(
            User.id,
            User.username,
            User.nome_completo,
            func.avg(Simulado.nota_tri).label('media_notas'),
            func.count(Simulado.id).label('total_simulados')
        ).join(Simulado).filter(
            Simulado.nota_tri.isnot(None),
            Simulado.status == 'Concluído'
        ).group_by(User.id, User.username, User.nome_completo).order_by(
            desc('media_notas')
        ).limit(10).all()
        
        # Áreas com baixo desempenho (média < 600)
        areas_baixo = db.session.query(
            Simulado.areas,
            func.avg(Simulado.nota_tri).label('media'),
            func.count(Simulado.id).label('total')
        ).filter(
            Simulado.nota_tri.isnot(None),
            Simulado.status == 'Concluído',
            Simulado.areas.isnot(None)
        ).group_by(Simulado.areas).having(
            func.avg(Simulado.nota_tri) < 600
        ).all()
        
        return jsonify({
            'total_simulados': total_simulados,
            'media_geral_tri': round(media_geral, 2),
            'taxa_conclusao': round(taxa_conclusao, 2),
            'taxa_acertos_geral': round(percentual_acertos, 2),
            'distribuicao_notas': [{
                'faixa': item[0],
                'quantidade': item[1]
            } for item in distribuicao_notas],
            'desempenho_areas': [{
                'area': item[0],
                'media': round(item[1], 2),
                'total': item[2]
            } for item in medias_por_area],
            'evolucao_desempenho': {
                'datas': [str(item[0]) for item in evolucao],
                'medias': [round(item[1], 2) if item[1] else 0 for item in evolucao],
                'simulados': [item[2] for item in evolucao]
            },
            'top_alunos': [{
                'id': item[0],
                'username': item[1],
                'nome': item[2],
                'media': round(item[3], 2),
                'simulados': item[4]
            } for item in top_notas],
            'areas_baixo_desempenho': [{
                'area': item[0],
                'media': round(item[1], 2),
                'total': item[2]
            } for item in areas_baixo]
        })
        
    except Exception as e:
        logger.error(f"Erro na análise de desempenho: {e}")
        return jsonify({
            'error': str(e),
            'total_simulados': 0,
            'media_geral_tri': 0,
            'taxa_conclusao': 0,
            'taxa_acertos_geral': 0,
            'distribuicao_notas': [],
            'desempenho_areas': [],
            'evolucao_desempenho': {'datas': [], 'medias': [], 'simulados': []},
            'top_alunos': [],
            'areas_baixo_desempenho': []
        })
# ==========================================
# ANÁLISE FINANCEIRA (XP e Diamantes)
# ==========================================
@admin_analytics_bp.route('/api/financeiro')
@login_required
@admin_required
def analise_financeiro():
    """Análise do sistema de XP e diamantes"""
    
    # Total de XP distribuído
    xp_total_distribuido = db.session.query(func.sum(User.xp_total)).scalar() or 0
    
    # Total de diamantes em circulação
    diamantes_circulacao = db.session.query(func.sum(User.diamantes)).scalar() or 0
    
    # Distribuição de XP por origem (últimos 30 dias)
    data_30_dias = datetime.utcnow() - timedelta(days=30)
    xp_por_origem = db.session.query(
        XpGanho.origem,
        func.sum(XpGanho.quantidade).label('total'),
        func.count(distinct(XpGanho.user_id)).label('usuarios')
    ).filter(
        XpGanho.data >= data_30_dias
    ).group_by(XpGanho.origem).all()
    
    # Evolução de XP distribuído (últimos 30 dias)
    evolucao_xp = db.session.query(
        func.date(XpGanho.data).label('data'),
        func.sum(XpGanho.quantidade).label('xp_dia')
    ).filter(
        XpGanho.data >= data_30_dias
    ).group_by('data').order_by('data').all()
    
    # Usuários com mais diamantes
    top_diamantes = db.session.query(
        User.id,
        User.username,
        User.diamantes,
        User.xp_total
    ).order_by(desc(User.diamantes)).limit(10).all()
    
    # Taxa de conversão XP -> Diamantes
    total_usuarios_com_xp = User.query.filter(User.xp_total > 0).count()
    total_usuarios_com_diamantes = User.query.filter(User.diamantes > 0).count()
    taxa_conversao = (total_usuarios_com_diamantes / total_usuarios_com_xp * 100) if total_usuarios_com_xp > 0 else 0
    
    return jsonify({
        'xp_total_distribuido': xp_total_distribuido,
        'diamantes_circulacao': diamantes_circulacao,
        'xp_por_origem': [{
            'origem': item[0] or 'Desconhecido',
            'total': item[1],
            'usuarios': item[2]
        } for item in xp_por_origem],
        'evolucao_xp': {
            'datas': [str(item[0]) for item in evolucao_xp],
            'valores': [item[1] for item in evolucao_xp]
        },
        'top_diamantes': [{
            'id': item[0],
            'username': item[1],
            'diamantes': item[2],
            'xp': item[3]
        } for item in top_diamantes],
        'taxa_conversao': round(taxa_conversao, 2)
    })

# ==========================================
# ANÁLISE PREDITIVA
# ==========================================
@admin_analytics_bp.route('/api/previsoes')
@login_required
@admin_required
def analise_preditiva():
    """Análises preditivas e tendências com métricas avançadas"""
    
    try:
        # Datas de referência
        data_90_dias = datetime.utcnow() - timedelta(days=90)
        data_60_dias = datetime.utcnow() - timedelta(days=60)
        data_30_dias = datetime.utcnow() - timedelta(days=30)
        data_15_dias = datetime.utcnow() - timedelta(days=15)
        data_7_dias = datetime.utcnow() - timedelta(days=7)
        
        # ==========================================
        # 1. CRESCIMENTO DE USUÁRIOS
        # ==========================================
        crescimento = db.session.query(
            func.date(User.data_registro).label('data'),
            func.count(User.id).label('novos_usuarios')
        ).filter(
            User.data_registro >= data_90_dias
        ).group_by('data').order_by('data').all()
        
        # Tendência de crescimento (comparar últimos 7 vs 7 anteriores)
        if len(crescimento) >= 14:
            ultimos_7 = sum([item[1] for item in crescimento[-7:]])
            anteriores_7 = sum([item[1] for item in crescimento[-14:-7]])
            tendencia_crescimento = ((ultimos_7 - anteriores_7) / anteriores_7 * 100) if anteriores_7 > 0 else 0
        else:
            tendencia_crescimento = 0
        
        # Média de crescimento diário (últimos 30 dias)
        crescimento_30d = [item[1] for item in crescimento[-30:]] if len(crescimento) >= 30 else [item[1] for item in crescimento]
        media_diaria = sum(crescimento_30d) / len(crescimento_30d) if crescimento_30d else 0
        
        # Projeção de crescimento (próximos 30, 60 e 90 dias)
        projecao_30_dias = int(media_diaria * 30)
        projecao_60_dias = int(media_diaria * 60)
        projecao_90_dias = int(media_diaria * 90)
        
        # ==========================================
        # 2. ANÁLISE DE CHURN (RISCO DE ABANDONO)
        # ==========================================
        
        # Total de usuários
        total_usuarios = User.query.count()
        
        # Usuários em risco CRÍTICO (registrados há 30+ dias, sem atividade há 15+ dias)
        usuarios_risco_critico = User.query.filter(
            User.data_registro < data_30_dias,
            ~User.id.in_(
                db.session.query(TempoEstudo.user_id).filter(
                    TempoEstudo.data_inicio >= data_15_dias
                )
            )
        ).count()
        
        # Usuários em risco ALTO (registrados há 30+ dias, sem atividade há 7+ dias)
        usuarios_risco_alto = User.query.filter(
            User.data_registro < data_30_dias,
            ~User.id.in_(
                db.session.query(TempoEstudo.user_id).filter(
                    TempoEstudo.data_inicio >= data_7_dias
                )
            )
        ).count()
        
        # Usuários inativos totais (sem atividade há 30+ dias)
        usuarios_inativos_30d = User.query.filter(
            ~User.id.in_(
                db.session.query(TempoEstudo.user_id).filter(
                    TempoEstudo.data_inicio >= data_30_dias
                )
            )
        ).count()
        
        # Taxa de churn
        taxa_churn = (usuarios_inativos_30d / total_usuarios * 100) if total_usuarios > 0 else 0
        
        # ==========================================
        # 3. TAXA DE RETENÇÃO
        # ==========================================
        
        # Usuários que voltaram após 7 dias
        usuarios_elegivel_7d = User.query.filter(User.data_registro < data_7_dias).count()
        usuarios_retencao_7d = User.query.filter(
            User.data_registro < data_7_dias,
            User.id.in_(
                db.session.query(TempoEstudo.user_id).filter(
                    TempoEstudo.data_inicio >= data_7_dias
                )
            )
        ).count()
        
        taxa_retencao_7d = (usuarios_retencao_7d / usuarios_elegivel_7d * 100) if usuarios_elegivel_7d > 0 else 0
        
        # Usuários que voltaram após 30 dias
        usuarios_elegivel_30d = User.query.filter(User.data_registro < data_30_dias).count()
        usuarios_retencao_30d = User.query.filter(
            User.data_registro < data_30_dias,
            User.id.in_(
                db.session.query(TempoEstudo.user_id).filter(
                    TempoEstudo.data_inicio >= data_30_dias
                )
            )
        ).count()
        
        taxa_retencao_30d = (usuarios_retencao_30d / usuarios_elegivel_30d * 100) if usuarios_elegivel_30d > 0 else 0
        
        # ==========================================
        # 4. ENGAJAMENTO E PERFORMANCE
        # ==========================================
        
        # DAU (Daily Active Users) - média últimos 7 dias
        dau_7d = []
        for i in range(7):
            data = datetime.utcnow() - timedelta(days=i)
            data_inicio = data.replace(hour=0, minute=0, second=0)
            data_fim = data.replace(hour=23, minute=59, second=59)
            
            usuarios_dia = db.session.query(func.count(distinct(TempoEstudo.user_id))).filter(
                TempoEstudo.data_inicio >= data_inicio,
                TempoEstudo.data_inicio <= data_fim
            ).scalar() or 0
            dau_7d.append(usuarios_dia)
        
        dau_medio = sum(dau_7d) / len(dau_7d) if dau_7d else 0
        
        # MAU (Monthly Active Users)
        mau = db.session.query(func.count(distinct(TempoEstudo.user_id))).filter(
            TempoEstudo.data_inicio >= data_30_dias
        ).scalar() or 0
        
        # Razão DAU/MAU (stickiness) - métrica chave de engajamento
        stickiness = (dau_medio / mau * 100) if mau > 0 else 0
        
        # ==========================================
        # 5. USUÁRIOS COM ALTO POTENCIAL
        # ==========================================
        
        # Critérios: Boa média TRI + Engajamento alto nos últimos 30 dias
        usuarios_potencial = db.session.query(
            User.id,
            User.username,
            User.nome_completo,
            User.telefone,
            func.avg(Simulado.nota_tri).label('media'),
            func.count(Simulado.id).label('simulados'),
            User.xp_total,
            User.diamantes
        ).join(Simulado).filter(
            Simulado.data_realizado >= data_30_dias,
            Simulado.nota_tri.isnot(None),
            Simulado.status == 'Concluído'
        ).group_by(
            User.id, User.username, User.nome_completo, User.telefone, User.xp_total, User.diamantes
        ).having(
            (func.avg(Simulado.nota_tri) >= 700) &
            (func.count(Simulado.id) >= 3)
        ).order_by(desc('media')).limit(20).all()
        
        # ==========================================
        # 6. ÁREAS PROBLEMÁTICAS
        # ==========================================


        areas_baixo = db.session.query(
            Simulado.areas,
            func.avg(Simulado.nota_tri).label('media'),
            func.count(Simulado.id).label('total'),
            func.count(distinct(Simulado.user_id)).label('usuarios')
        ).filter(
            Simulado.nota_tri.isnot(None),
            Simulado.status == 'Concluído',
            Simulado.areas.isnot(None)
        ).group_by(Simulado.areas).having(
            func.avg(Simulado.nota_tri) < 600
        ).order_by('media').all()
        
        # ==========================================
        # 7. TENDÊNCIA DE DESEMPENHO
        # ==========================================
        
        # Média TRI por semana (últimas 12 semanas)
        tendencia_desempenho = []
        for i in range(12):
            inicio_semana = datetime.utcnow() - timedelta(weeks=i+1)
            fim_semana = datetime.utcnow() - timedelta(weeks=i)
            
            media_semana = db.session.query(func.avg(Simulado.nota_tri)).filter(
                Simulado.data_realizado >= inicio_semana,
                Simulado.data_realizado < fim_semana,
                Simulado.nota_tri.isnot(None),
                Simulado.status == 'Concluído'
            ).scalar() or 0
            
            tendencia_desempenho.append({
                'semana': f'Semana {12-i}',
                'media': round(media_semana, 2) if media_semana else 0
            })
        
        tendencia_desempenho.reverse()
        
        # ==========================================
        # 8. TAXA DE CONVERSÃO (FREEMIUM → PREMIUM)
        # ==========================================
        
        # Ajuste conforme seu sistema de pagamento
        usuarios_premium = User.query.filter(User.diamantes > 100).count()
        taxa_conversao_premium = (usuarios_premium / total_usuarios * 100) if total_usuarios > 0 else 0
        
        # ==========================================
        # 9. SAÚDE DA PLATAFORMA (SCORE GERAL)
        # ==========================================
        
        # Score de 0 a 100 baseado em múltiplos fatores
        score_crescimento = min(100, max(0, tendencia_crescimento * 2 if tendencia_crescimento > 0 else 50))
        score_retencao = taxa_retencao_30d
        score_engajamento = stickiness * 2  # Stickiness > 50% é excelente
        score_churn = max(0, 100 - taxa_churn * 3)
        
        saude_plataforma = (
            score_crescimento * 0.3 + 
            score_retencao * 0.3 + 
            score_engajamento * 0.2 + 
            score_churn * 0.2
        )
        
        # ==========================================
        # RETORNO FINAL
        # ==========================================
        
        return jsonify({
            # Crescimento
            'crescimento_usuarios': {
                'datas': [str(item[0]) for item in crescimento],
                'novos': [item[1] for item in crescimento]
            },
            'tendencia_crescimento': round(tendencia_crescimento, 2),
            'media_cadastros_diarios': round(media_diaria, 2),
            'projecao_30_dias': projecao_30_dias,
            'projecao_60_dias': projecao_60_dias,
            'projecao_90_dias': projecao_90_dias,
            
            # Churn e Retenção
            'usuarios_em_risco_critico': usuarios_risco_critico,
            'usuarios_em_risco_alto': usuarios_risco_alto,
            'usuarios_inativos_30d': usuarios_inativos_30d,
            'taxa_churn': round(taxa_churn, 2),
            'taxa_retencao_7d': round(taxa_retencao_7d, 2),
            'taxa_retencao_30d': round(taxa_retencao_30d, 2),
            
            # Engajamento
            'dau_medio': round(dau_medio, 2),
            'mau': mau,
            'stickiness': round(stickiness, 2),
            
            # Usuários de Alto Potencial
            'usuarios_alto_potencial': [{
                'id': item[0],
                'username': item[1],
                'nome': item[2],
                'telefone': item[3],
                'media_notas': round(item[4], 2),
                'simulados': item[5],
                'xp': item[6],
                'diamantes': item[7]
            } for item in usuarios_potencial],
            
            # Áreas Problemáticas
            'areas_baixo_desempenho': [{
                'area': item[0],
                'media': round(item[1], 2),
                'total_simulados': item[2],
                'usuarios_afetados': item[3]
            } for item in areas_baixo],
            
            # Tendência de Desempenho
            'tendencia_desempenho': tendencia_desempenho,
            
            # Conversão
            'taxa_conversao_premium': round(taxa_conversao_premium, 2),
            
            # Saúde da Plataforma
            'saude_plataforma': {
                'score_geral': round(saude_plataforma, 2),
                'score_crescimento': round(score_crescimento, 2),
                'score_retencao': round(score_retencao, 2),
                'score_engajamento': round(score_engajamento, 2),
                'score_churn': round(score_churn, 2),
                'status': 'excelente' if saude_plataforma >= 80 else 'bom' if saude_plataforma >= 60 else 'atenção' if saude_plataforma >= 40 else 'crítico'
            }
        })
        
    except Exception as e:
        logger.error(f"Erro na análise preditiva: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'crescimento_usuarios': {'datas': [], 'novos': []},
            'tendencia_crescimento': 0,
            'projecao_30_dias': 0,
            'usuarios_em_risco_critico': 0,
            'taxa_retencao_30d': 0,
            'dau_medio': 0,
            'mau': 0,
            'stickiness': 0,
            'usuarios_alto_potencial': [],
            'areas_baixo_desempenho': [],
            'tendencia_desempenho': [],
            'saude_plataforma': {'score_geral': 0, 'status': 'erro'}
        })


# ==========================================
# LISTA DE TODOS OS USUÁRIOS
# ==========================================
@admin_analytics_bp.route('/api/usuarios')
@login_required
@admin_required
def lista_usuarios():
    """Lista completa de usuários com filtros e paginação"""
    
    # Parâmetros de filtro
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    ordem = request.args.get('ordem', 'data_registro')
    direcao = request.args.get('direcao', 'desc')
    filtro_status = request.args.get('status', 'todos')  # todos, ativos, inativos
    
    # Query base
    query = User.query
    
    # Aplicar filtros
    if filtro_status == 'ativos':
        data_7_dias = datetime.utcnow() - timedelta(days=7)
        query = query.join(TempoEstudo).filter(
            TempoEstudo.data_inicio >= data_7_dias
        ).distinct()
    elif filtro_status == 'inativos':
        data_30_dias = datetime.utcnow() - timedelta(days=30)
        query = query.filter(
            ~User.id.in_(
                db.session.query(TempoEstudo.user_id).filter(
                    TempoEstudo.data_inicio >= data_30_dias
                )
            )
        )
    
    # Ordenação
    if ordem == 'xp_total':
        query = query.order_by(desc(User.xp_total) if direcao == 'desc' else User.xp_total)
    elif ordem == 'data_registro':
        query = query.order_by(desc(User.data_registro) if direcao == 'desc' else User.data_registro)
    elif ordem == 'diamantes':
        query = query.order_by(desc(User.diamantes) if direcao == 'desc' else User.diamantes)
    
    # Paginação
    paginacao = query.paginate(page=page, per_page=per_page, error_out=False)
    
    usuarios = []
    for u in paginacao.items:
        # Calcular métricas adicionais
        total_simulados = Simulado.query.filter_by(user_id=u.id, status='Concluído').count()
        media_notas = db.session.query(func.avg(Simulado.nota_tri)).filter(
            Simulado.user_id == u.id,
            Simulado.nota_tri.isnot(None)
        ).scalar() or 0
        
        tempo_total = db.session.query(func.sum(TempoEstudo.minutos)).filter(
            TempoEstudo.user_id == u.id
        ).scalar() or 0
        
        usuarios.append({
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'nome_completo': u.nome_completo,
            'telefone': u.telefone or '-',
            'xp_total': u.xp_total or 0,
            'diamantes': u.diamantes or 0,
            'data_registro': u.data_registro.strftime('%d/%m/%Y') if u.data_registro else '',
            'is_admin': u.is_admin,
            'is_active': u.is_active,
            'total_simulados': total_simulados,
            'media_notas': round(media_notas, 2),
            'tempo_estudo_horas': round(tempo_total / 60, 2)
        })
    
    return jsonify({
        'usuarios': usuarios,
        'total': paginacao.total,
        'paginas': paginacao.pages,
        'pagina_atual': page,
        'tem_proxima': paginacao.has_next,
        'tem_anterior': paginacao.has_prev
    })

# ==========================================
# DETALHES DE UM USUÁRIO ESPECÍFICO
# ==========================================
@admin_analytics_bp.route('/api/usuario/<int:user_id>')
@login_required
@admin_required
def detalhes_usuario(user_id):
    """Retorna dados completos de um usuário específico"""
    
    usuario = User.query.get_or_404(user_id)
    
    # Simulados do usuário
    simulados = Simulado.query.filter_by(user_id=user_id).order_by(
        desc(Simulado.data_realizado)
    ).limit(10).all()
    
    # Histórico de XP
    historico_xp = XpGanho.query.filter_by(user_id=user_id).order_by(
        desc(XpGanho.data)
    ).limit(20).all()
    
    # Tempo de estudo por atividade
    tempo_por_atividade = db.session.query(
        TempoEstudo.atividade,
        func.sum(TempoEstudo.minutos).label('total')
    ).filter(TempoEstudo.user_id == user_id).group_by(
        TempoEstudo.atividade
    ).all()
    
    # Desempenho por área
    desempenho = db.session.query(
        Simulado.areas,
        func.avg(Simulado.nota_tri).label('media'),
        func.count(Simulado.id).label('total')
    ).filter(
        Simulado.user_id == user_id,
        Simulado.nota_tri.isnot(None)
    ).group_by(Simulado.areas).all()
    
    return jsonify({
        'usuario': {
            'id': usuario.id,
            'username': usuario.username,
            'email': usuario.email,
            'nome_completo': usuario.nome_completo,
            'xp_total': usuario.xp_total or 0,
            'diamantes': usuario.diamantes or 0,
            'data_registro': usuario.data_registro.strftime('%d/%m/%Y %H:%M') if usuario.data_registro else '',
            'is_admin': usuario.is_admin,
            'sequencia_estudo': usuario.calcular_sequencia_estudo()
        },
        'simulados': [{
            'id': s.id,
            'titulo': s.titulo,
            'nota': s.nota_tri,
            'data': s.data_realizado.strftime('%d/%m/%Y') if s.data_realizado else ''
        } for s in simulados],
        'historico_xp': [{
            'quantidade': h.quantidade,
            'origem': h.origem,
            'data': h.data.strftime('%d/%m/%Y %H:%M')
        } for h in historico_xp],
        'tempo_por_atividade': [{
            'atividade': item[0] or 'Desconhecido',
            'minutos': item[1] or 0
        } for item in tempo_por_atividade],
        'desempenho_areas': [{
            'area': item[0],
            'media': round(item[1], 2),
            'total': item[2]
        } for item in desempenho]
    })

# ==========================================
# ANÁLISE DE ENGAJAMENTO - QUENTE/MORNO/FRIO
# ==========================================
@admin_analytics_bp.route('/api/engajamento/distribuicao')
@login_required
@admin_required
def distribuicao_engajamento():
    """Retorna distribuição de usuários por nível de engajamento"""
    try:
        resultado = EngajamentoService.obter_distribuicao_engajamento()
        return jsonify(resultado)
    except Exception as e:
        logger.error(f"Erro na distribuição de engajamento: {e}")
        return jsonify({'error': str(e)}), 500

@admin_analytics_bp.route('/api/engajamento/usuarios')
@login_required
@admin_required
def lista_usuarios_engajamento():
    """Lista usuários com seus scores de engajamento"""
    try:
        # Parâmetros
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        filtro = request.args.get('filtro', 'todos')  # todos, quente, morno, frio
        ordem = request.args.get('ordem', 'score')     # score, username, dias_ativos
        
        # Obter todos os usuários
        usuarios = User.query.all()
        
        # Calcular engajamento para cada um
        usuarios_engajamento = []
        for user in usuarios:
            metricas = EngajamentoService.obter_metricas_detalhadas(user.id)
            if metricas:
                usuarios_engajamento.append(metricas)
        
        # Filtrar por classificação
        if filtro != 'todos':
            usuarios_engajamento = [u for u in usuarios_engajamento if u['classificacao'] == filtro]
        
        # Ordenar
        if ordem == 'score':
            usuarios_engajamento.sort(key=lambda x: x['score'], reverse=True)
        elif ordem == 'username':
            usuarios_engajamento.sort(key=lambda x: x['username'])
        elif ordem == 'dias_ativos':
            usuarios_engajamento.sort(key=lambda x: x['dias_ativos_7d'], reverse=True)
        
        # Paginar
        total = len(usuarios_engajamento)
        inicio = (page - 1) * per_page
        fim = inicio + per_page
        usuarios_pagina = usuarios_engajamento[inicio:fim]
        
        return jsonify({
            'usuarios': usuarios_pagina,
            'total': total,
            'paginas': (total + per_page - 1) // per_page,
            'pagina_atual': page,
            'tem_proxima': fim < total,
            'tem_anterior': page > 1
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar usuários por engajamento: {e}")
        return jsonify({'error': str(e)}), 500

@admin_analytics_bp.route('/api/engajamento/alertas')
@login_required
@admin_required
def alertas_engajamento():
    """Retorna alertas de usuários que precisam atenção"""
    try:
        alertas = EngajamentoService.obter_alertas_engajamento()
        return jsonify(alertas)
    except Exception as e:
        logger.error(f"Erro ao obter alertas: {e}")
        return jsonify({'error': str(e)}), 500

@admin_analytics_bp.route('/api/engajamento/usuario/<int:user_id>')
@login_required
@admin_required
def detalhes_engajamento_usuario(user_id):
    """Retorna análise detalhada de engajamento de um usuário específico"""
    try:
        metricas = EngajamentoService.obter_metricas_detalhadas(user_id)
        if not metricas:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        return jsonify(metricas)
    except Exception as e:
        logger.error(f"Erro ao obter detalhes de engajamento: {e}")
        return jsonify({'error': str(e)}), 500

@admin_analytics_bp.route('/api/engajamento/evolucao')
@login_required
@admin_required
def evolucao_engajamento():
    """Evolução do engajamento ao longo do tempo"""
    try:
        data_30_dias = datetime.utcnow() - timedelta(days=30)
        
        # Engajamento por dia (últimos 30 dias)
        evolucao = []
        for i in range(30, -1, -1):
            data = datetime.utcnow() - timedelta(days=i)
            data_inicio = data.replace(hour=0, minute=0, second=0)
            data_fim = data.replace(hour=23, minute=59, second=59)
            
            # Usuários ativos nesse dia
            usuarios_ativos = db.session.query(
                func.count(distinct(TempoEstudo.user_id))
            ).filter(
                TempoEstudo.data_inicio >= data_inicio,
                TempoEstudo.data_inicio <= data_fim
            ).scalar() or 0
            
            evolucao.append({
                'data': data.strftime('%Y-%m-%d'),
                'usuarios_ativos': usuarios_ativos
            })
        
        return jsonify({
            'evolucao': evolucao
        })
        
    except Exception as e:
        logger.error(f"Erro na evolução de engajamento: {e}")
        return jsonify({'error': str(e)}), 500

# ==========================================
# EXPORTAR DADOS
# ==========================================
@admin_analytics_bp.route('/api/exportar/<tipo>')
@login_required
@admin_required
def exportar_dados(tipo):
    """Exporta dados em formato JSON para download"""
    
    if tipo == 'usuarios':
        usuarios = User.query.all()
        dados = [{
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'xp_total': u.xp_total,
            'diamantes': u.diamantes,
            'data_registro': u.data_registro.isoformat() if u.data_registro else None
        } for u in usuarios]
    
    elif tipo == 'simulados':
        simulados = Simulado.query.filter_by(status='Concluído').all()
        dados = [{
            'id': s.id,
            'user_id': s.user_id,
            'titulo': s.titulo,
            'nota_tri': s.nota_tri,
            'data_realizado': s.data_realizado.isoformat() if s.data_realizado else None
        } for s in simulados]
    
    elif tipo == 'resgates' and SHOP_DISPONIVEL:
        resgates = Resgate.query.all()
        dados = [{
            'id': r.id,
            'user_id': r.user_id,
            'produto_id': r.produto_id,
            'status': r.status,
            'diamantes_gastos': r.diamantes_gastos,
            'data_resgate': r.data_resgate.isoformat() if r.data_resgate else None
        } for r in resgates]
    
    else:
        return jsonify({'error': 'Tipo inválido'}), 400
    
    return jsonify({
        'tipo': tipo,
        'total_registros': len(dados),
        'data_exportacao': datetime.utcnow().isoformat(),
        'dados': dados
    })



# ==========================================
# ANÁLISE DE NAVEGAÇÃO E PÁGINAS
# ==========================================

@admin_analytics_bp.route('/api/analise-paginas')
@login_required
@admin_required
def analise_paginas():
    """Análise detalhada de uso de páginas/módulos da plataforma"""
    try:
        data_30_dias = datetime.utcnow() - timedelta(days=30)
        data_7_dias = datetime.utcnow() - timedelta(days=7)
        
        # 1. PÁGINAS MAIS UTILIZADAS (últimos 30 dias)
        paginas_populares = db.session.query(
            TempoEstudo.atividade,
            func.count(TempoEstudo.id).label('total_sessoes'),
            func.sum(TempoEstudo.minutos).label('tempo_total'),
            func.count(distinct(TempoEstudo.user_id)).label('usuarios_unicos'),
            func.avg(TempoEstudo.minutos).label('tempo_medio_sessao')
        ).filter(
            TempoEstudo.data_inicio >= data_30_dias,
            TempoEstudo.atividade.isnot(None)
        ).group_by(TempoEstudo.atividade).order_by(desc('total_sessoes')).all()
        
        # 2. PÁGINAS SUBUTILIZADAS (menos de 10 sessões nos últimos 30 dias)
        paginas_subutilizadas = db.session.query(
            TempoEstudo.atividade,
            func.count(TempoEstudo.id).label('total_sessoes'),
            func.count(distinct(TempoEstudo.user_id)).label('usuarios_unicos')
        ).filter(
            TempoEstudo.data_inicio >= data_30_dias,
            TempoEstudo.atividade.isnot(None)
        ).group_by(TempoEstudo.atividade).having(
            func.count(TempoEstudo.id) < 10
        ).order_by('total_sessoes').all()
        
        # 3. CRESCIMENTO DE USO POR PÁGINA (últimos 7 dias vs 7 anteriores)
        crescimento_paginas = []
        for atividade_row in paginas_populares:
            atividade = atividade_row[0]
            
            # Últimos 7 dias
            uso_7d = db.session.query(func.count(TempoEstudo.id)).filter(
                TempoEstudo.atividade == atividade,
                TempoEstudo.data_inicio >= data_7_dias
            ).scalar() or 0
            
            # 7 dias anteriores
            data_14_dias = datetime.utcnow() - timedelta(days=14)
            uso_7d_anterior = db.session.query(func.count(TempoEstudo.id)).filter(
                TempoEstudo.atividade == atividade,
                TempoEstudo.data_inicio >= data_14_dias,
                TempoEstudo.data_inicio < data_7_dias
            ).scalar() or 0
            
            variacao = 0
            if uso_7d_anterior > 0:
                variacao = ((uso_7d - uso_7d_anterior) / uso_7d_anterior) * 100
            
            crescimento_paginas.append({
                'atividade': atividade,
                'uso_atual': uso_7d,
                'uso_anterior': uso_7d_anterior,
                'variacao': round(variacao, 1)
            })
        
        # 4. JORNADA DO USUÁRIO - Páginas mais visitadas em sequência
        jornada_usuario = db.session.query(
            TempoEstudo.user_id,
            TempoEstudo.atividade,
            TempoEstudo.data_inicio
        ).filter(
            TempoEstudo.data_inicio >= data_30_dias,
            TempoEstudo.atividade.isnot(None)
        ).order_by(TempoEstudo.user_id, TempoEstudo.data_inicio).limit(1000).all()
        
        # Calcular transições mais comuns
        transicoes = {}
        usuario_atual = None
        atividade_anterior = None
        
        for user_id, atividade, data in jornada_usuario:
            if user_id == usuario_atual and atividade_anterior:
                chave = f"{atividade_anterior} → {atividade}"
                transicoes[chave] = transicoes.get(chave, 0) + 1
            usuario_atual = user_id
            atividade_anterior = atividade
        
        transicoes_ordenadas = sorted(transicoes.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # 5. TAXA DE ENGAJAMENTO POR PÁGINA (% de usuários que retornam)
        taxa_retorno_paginas = []
        total_usuarios = User.query.count()
        
        for atividade_row in paginas_populares:
            atividade = atividade_row[0]
            
            # Usuários que usaram a página
            usuarios_usaram = db.session.query(distinct(TempoEstudo.user_id)).filter(
                TempoEstudo.atividade == atividade,
                TempoEstudo.data_inicio >= data_30_dias
            ).count()
            
            # Desses, quantos voltaram mais de uma vez?
            usuarios_retornaram = db.session.query(TempoEstudo.user_id).filter(
                TempoEstudo.atividade == atividade,
                TempoEstudo.data_inicio >= data_30_dias
            ).group_by(TempoEstudo.user_id).having(
                func.count(TempoEstudo.id) > 1
            ).count()
            
            taxa_retorno = (usuarios_retornaram / usuarios_usaram * 100) if usuarios_usaram > 0 else 0
            penetracao = (usuarios_usaram / total_usuarios * 100) if total_usuarios > 0 else 0
            
            taxa_retorno_paginas.append({
                'atividade': atividade,
                'usuarios_usaram': usuarios_usaram,
                'usuarios_retornaram': usuarios_retornaram,
                'taxa_retorno': round(taxa_retorno, 1),
                'penetracao': round(penetracao, 1)
            })
        
        # 6. TEMPO MÉDIO POR PÁGINA
        tempo_medio_paginas = [{
            'atividade': item[0],
            'tempo_medio_minutos': round(item[4], 1) if item[4] else 0
        } for item in paginas_populares]
        
        return jsonify({
            'paginas_populares': [{
                'atividade': item[0],
                'total_sessoes': item[1],
                'tempo_total_minutos': item[2] or 0,
                'usuarios_unicos': item[3],
                'tempo_medio_sessao': round(item[4], 1) if item[4] else 0
            } for item in paginas_populares],
            'paginas_subutilizadas': [{
                'atividade': item[0],
                'total_sessoes': item[1],
                'usuarios_unicos': item[2]
            } for item in paginas_subutilizadas],
            'crescimento_paginas': crescimento_paginas,
            'transicoes_comuns': [{
                'transicao': t[0],
                'quantidade': t[1]
            } for t in transicoes_ordenadas],
            'taxa_retorno_paginas': sorted(taxa_retorno_paginas, key=lambda x: x['taxa_retorno'], reverse=True),
            'tempo_medio_paginas': sorted(tempo_medio_paginas, key=lambda x: x['tempo_medio_minutos'], reverse=True)
        })
        
    except Exception as e:
        logger.error(f"Erro na análise de páginas: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'paginas_populares': [],
            'paginas_subutilizadas': [],
            'crescimento_paginas': [],
            'transicoes_comuns': [],
            'taxa_retorno_paginas': [],
            'tempo_medio_paginas': []
        })
