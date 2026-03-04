# app/routes/dashboard_analytics.py
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.simulado import Simulado
from app.models.redacao import Redacao
from app.models.estatisticas import TempoEstudo
from datetime import datetime, timedelta, date, time
from sqlalchemy import func, cast, Date, extract, case, and_, or_, text, distinct
from collections import defaultdict
import json
import pytz
from sqlalchemy import distinct




# ============================================================
# TIMEZONE DE BRASÍLIA
# ============================================================
BRASILIA_TZ = pytz.timezone('America/Sao_Paulo')


def now_brasilia():
    """Retorna datetime atual com timezone de Brasília"""
    return datetime.now(BRASILIA_TZ)


def to_brasilia(dt):
    """
    Converte datetime UTC para timezone de Brasília
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Se não tem timezone, assume UTC e converte para Brasília
        utc_tz = pytz.UTC
        dt = utc_tz.localize(dt)
    return dt.astimezone(BRASILIA_TZ)


def tornar_aware(dt):
    """
    Converte datetime/date do banco para timezone-aware
    
    CORRIGIDO: Agora detecta corretamente date vs datetime
    """
    if dt is None:
        return None
    
    # ✅ CORRIGIDO: Verificar se tem atributo 'hour' (datetime tem, date não tem)
    if hasattr(dt, 'hour'):
        # É datetime
        if dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
            # Já tem timezone, converter para Brasília
            return dt.astimezone(BRASILIA_TZ)
        else:
            # Não tem timezone, adicionar timezone de Brasília
            return BRASILIA_TZ.localize(dt)
    else:
        # É date (não tem 'hour')
        # Converter para datetime às 00:00:00 e adicionar timezone
        dt_as_datetime = datetime.combine(dt, time.min)
        return BRASILIA_TZ.localize(dt_as_datetime)


dashboard_analytics_bp = Blueprint('dashboard_analytics', __name__, url_prefix='/dashboard-analytics')


def safe_date(obj):
    """Converte datetime ou date para date de forma segura"""
    if obj is None:
        return None
    # Se já é date puro (não datetime), retorna direto
    if type(obj) == date:
        return obj
    # Se é datetime, extrai o date
    if isinstance(obj, datetime):
        return obj.date()
    return obj


def verificar_admin():
    """Verifica se o usuário atual é admin"""
    return current_user.is_authenticated and current_user.is_admin


def parse_date_filter(request):
    """
    Extrai filtros de data da requisição
    Retorna (data_inicio, data_fim) como datetime aware
    """
    periodo = request.args.get('periodo', '30')
    data_inicio_str = request.args.get('data_inicio')
    data_fim_str = request.args.get('data_fim')
    
    hoje = now_brasilia()
    
    if data_inicio_str and data_fim_str:
        # Usar datas customizadas
        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d')
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d')
            
            # Adicionar timezone
            data_inicio = BRASILIA_TZ.localize(data_inicio.replace(hour=0, minute=0, second=0))
            data_fim = BRASILIA_TZ.localize(data_fim.replace(hour=23, minute=59, second=59))
        except:
            # Se falhar, usar período padrão
            dias = int(periodo)
            data_inicio = hoje - timedelta(days=dias)
            data_fim = hoje
    else:
        # Usar período
        dias = int(periodo)
        data_inicio = hoje - timedelta(days=dias)
        data_fim = hoje
    
    return data_inicio, data_fim


def verificar_usuario_ativado(user_id, data_inicio=None, data_fim=None):
    """
    Verifica se usuário está ativado (fez simulado, redação OU assistiu aula)
    COM correção de timezone
    """
    try:
        # Verificar simulados
        simulados = Simulado.query.filter_by(user_id=user_id).all()
        if simulados:
            if data_inicio and data_fim:
                # Filtrar por data com conversão
                simulados_periodo = [
                    s for s in simulados
                    if s.data_realizado and 
                    data_inicio <= tornar_aware(s.data_realizado) <= data_fim
                ]
                if simulados_periodo:
                    return True
            else:
                return True
        
        # Verificar redações
        redacoes = Redacao.query.filter_by(user_id=user_id).all()
        if redacoes:
            if data_inicio and data_fim:
                # Filtrar por data com conversão
                redacoes_periodo = [
                    r for r in redacoes
                    if r.data_envio and 
                    data_inicio <= tornar_aware(r.data_envio) <= data_fim
                ]
                if redacoes_periodo:
                    return True
            else:
                return True
        
        # Verificar aulas assistidas (TempoEstudo já está importado no topo)
        tempo_estudo = TempoEstudo.query.filter(
            TempoEstudo.user_id == user_id,
            TempoEstudo.atividade.in_(['aula', 'video', 'aula_assistida'])
        ).all()
        
        if tempo_estudo:
            if data_inicio and data_fim:
                # Filtrar por data com conversão
                aulas_periodo = [
                    t for t in tempo_estudo
                    if t.data_inicio and 
                    data_inicio <= tornar_aware(t.data_inicio) <= data_fim
                ]
                if aulas_periodo:
                    return True
            else:
                return True
        
        return False
        
    except Exception as e:
        print(f"Erro em verificar_usuario_ativado: {e}")
        import traceback
        traceback.print_exc()
        return False


@dashboard_analytics_bp.route('/')
@login_required
def index():
    """Página principal do dashboard"""
    if not verificar_admin():
        return "Acesso negado", 403
    return render_template('dashboard_analytics.html')

# ============================================================
# APIs de KPIs (corrigidas com timezone)
# ============================================================

@dashboard_analytics_bp.route('/api/kpis-negocio')
@login_required
def kpis_negocio():
    """Retorna KPIs de negócio"""
    if not verificar_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    try:
        data_inicio, data_fim = parse_date_filter(request)
        
        # Total de usuários
        total_usuarios = User.query.count()
        
        # Novos usuários no período
        novos_usuarios = User.query.filter(
            User.data_registro.between(data_inicio, data_fim)
        ).count()
        
        # Usuários premium ativos
        usuarios_premium = User.query.filter(
            User.plano_ativo.in_(['mensal', 'anual']),
            User.data_expiracao_plano > now_brasilia()
        ).count()
        
        # Taxa de conversão
        usuarios_free = total_usuarios - usuarios_premium
        taxa_conversao = (usuarios_premium / total_usuarios * 100) if total_usuarios > 0 else 0
        
        # Receita (MRR e ARR)
        usuarios_mensais = User.query.filter(
            User.plano_ativo == 'mensal',
            User.data_expiracao_plano > now_brasilia()
        ).count()
        
        usuarios_anuais = User.query.filter(
            User.plano_ativo == 'anual',
            User.data_expiracao_plano > now_brasilia()
        ).count()
        
        mrr = usuarios_mensais * 49.90
        arr = usuarios_anuais * 399.90
        receita_mensal = mrr + (arr / 12)
        
        # Churn rate
        usuarios_expirados = User.query.filter(
            User.data_expiracao_plano.between(data_inicio, data_fim),
            User.plano_ativo == 'free'
        ).count()
        
        churn_rate = (usuarios_expirados / usuarios_premium * 100) if usuarios_premium > 0 else 0
        
        # LTV e CAC
        ltv = receita_mensal / usuarios_premium if usuarios_premium > 0 else 0
        cac_estimado = 50.00
        
        return jsonify({
            'total_usuarios': total_usuarios,
            'novos_usuarios': novos_usuarios,
            'usuarios_premium': usuarios_premium,
            'usuarios_free': usuarios_free,
            'taxa_conversao': round(taxa_conversao, 2),
            'mrr': round(mrr, 2),
            'arr': round(arr, 2),
            'receita_mensal': round(receita_mensal, 2),
            'churn_rate': round(churn_rate, 2),
            'ltv': round(ltv, 2),
            'cac': round(cac_estimado, 2),
            'ltv_cac_ratio': round(ltv / cac_estimado, 2) if cac_estimado > 0 else 0,
            'periodo': {
                'inicio': data_inicio.strftime('%Y-%m-%d'),
                'fim': data_fim.strftime('%Y-%m-%d')
            }
        })
    
    except Exception as e:
        print(f"Erro ao calcular KPIs de negócio: {e}")
        return jsonify({'erro': str(e)}), 500

@dashboard_analytics_bp.route('/api/kpis-produto')
@login_required
def kpis_produto():
    """Retorna KPIs de produto - CORRIGIDO COM AULAS"""
    if not verificar_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    try:
        data_inicio, data_fim = parse_date_filter(request)
        
        # Novos usuários no período
        novos_usuarios = User.query.filter(
            User.data_registro.between(data_inicio, data_fim)
        ).all()
        
        total_novos = len(novos_usuarios)
        
        # ✅ CORRIGIDO: Usuários ativados incluindo aulas
        usuarios_ativados = sum(1 for user in novos_usuarios if verificar_usuario_ativado(user.id))
        
        taxa_ativacao = (usuarios_ativados / total_novos * 100) if total_novos > 0 else 0
        
        # Retorno D1 e D7
        retorno_d1 = 0
        retorno_d7 = 0
        
        for user in novos_usuarios:
            if not user.ultimo_acesso or not user.data_registro:
                continue
                
            data_registro = safe_date(user.data_registro)
            ultimo_acesso_date = safe_date(user.ultimo_acesso)
            
            if not data_registro or not ultimo_acesso_date:
                continue
            
            # D1
            if ultimo_acesso_date >= data_registro + timedelta(days=1):
                retorno_d1 += 1
            
            # D7
            if data_registro + timedelta(days=1) <= ultimo_acesso_date <= data_registro + timedelta(days=7):
                retorno_d7 += 1
        
        taxa_retorno_d1 = (retorno_d1 / total_novos * 100) if total_novos > 0 else 0
        taxa_retorno_d7 = (retorno_d7 / total_novos * 100) if total_novos > 0 else 0
        
        # Tempo médio de uso (APENAS TEMPO_ESTUDO)
        #from app.models.estatisticas import TempoEstudo
        
        ids_ativados = [user.id for user in novos_usuarios if verificar_usuario_ativado(user.id)]
        
        tempo_ativados = db.session.query(
            func.sum(TempoEstudo.minutos)
        ).filter(
            TempoEstudo.user_id.in_(ids_ativados),
            TempoEstudo.data_inicio.between(data_inicio, data_fim)
        ).scalar() or 0
        
        tempo_medio_ativados = (tempo_ativados / usuarios_ativados) if usuarios_ativados > 0 else 0
        
        # DAU e MAU - CORRIGIDO
        hoje_brasilia = now_brasilia().date()
        
        # ✅ CORRIGIDO: MAU considera último acesso como DATE, não DATETIME
        dau = User.query.filter(
            cast(User.ultimo_acesso, Date) == hoje_brasilia
        ).count()
        
        inicio_mes = hoje_brasilia.replace(day=1)
        mau = User.query.filter(
            cast(User.ultimo_acesso, Date) >= inicio_mes
        ).count()
        
        stickiness = (dau / mau * 100) if mau > 0 else 0
        
        return jsonify({
            'total_novos_usuarios': total_novos,
            'usuarios_ativados': usuarios_ativados,
            'taxa_ativacao': round(taxa_ativacao, 2),
            'retorno_d1': retorno_d1,
            'taxa_retorno_d1': round(taxa_retorno_d1, 2),
            'retorno_d7': retorno_d7,
            'taxa_retorno_d7': round(taxa_retorno_d7, 2),
            'tempo_medio_uso_ativados': round(tempo_medio_ativados, 2),
            'dau': dau,
            'mau': mau,
            'stickiness': round(stickiness, 2),
            'periodo': {
                'inicio': data_inicio.strftime('%Y-%m-%d'),
                'fim': data_fim.strftime('%Y-%m-%d')
            }
        })
    
    except Exception as e:
        print(f"Erro ao calcular KPIs de produto: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

# ============================================================
# NOVA API: ENGAJAMENTO POR FUNCIONALIDADE (CORRIGIDA)
# ============================================================

@dashboard_analytics_bp.route('/api/engajamento-funcionalidades')
@login_required
def engajamento_funcionalidades():
    """Retorna métricas de engajamento por funcionalidade USANDO TEMPO_ESTUDO"""
    if not verificar_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    try:
        data_inicio, data_fim = parse_date_filter(request)
        #from app.models.estatisticas import TempoEstudo
        
        # Agregar por atividade
        resultados = db.session.query(
            TempoEstudo.atividade,
            func.sum(TempoEstudo.minutos).label('total_minutos'),
            func.count(distinct(TempoEstudo.user_id)).label('usuarios_unicos'),
            func.count(TempoEstudo.id).label('total_sessoes')
        ).filter(
            TempoEstudo.data_inicio.between(data_inicio, data_fim),
            TempoEstudo.minutos > 0
        ).group_by(
            TempoEstudo.atividade
        ).all()


        funcionalidades = []
        for resultado in resultados:
            atividade = resultado.atividade or 'Geral'
            total_min = int(resultado.total_minutos or 0)
            usuarios = int(resultado.usuarios_unicos or 0)
            sessoes = int(resultado.total_sessoes or 0)
            
            funcionalidades.append({
                'nome': atividade,
                'total_uso_minutos': total_min,
                'total_sessoes': sessoes,
                'usuarios_unicos': usuarios,
                'media_por_usuario': round(total_min / usuarios, 2) if usuarios > 0 else 0
            })
        
        # Ordenar por tempo total
        funcionalidades.sort(key=lambda x: x['total_uso_minutos'], reverse=True)
        
        return jsonify({
            'funcionalidades': funcionalidades,
            'periodo': {
                'inicio': data_inicio.strftime('%Y-%m-%d'),
                'fim': data_fim.strftime('%Y-%m-%d')
            }
        })
    
    except Exception as e:
        print(f"Erro ao calcular engajamento: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

# ============================================================
# NOVA API: LISTA DE USUÁRIOS ATIVADOS (VISÃO MICRO) - CORRIGIDA
# ============================================================

@dashboard_analytics_bp.route('/api/usuarios-ativados')
def lista_usuarios_ativados():
    """
    Lista de usuários ativados - com correção de timezone
    """
    try:
        data_inicio, data_fim = parse_date_filter(request)
        
        # Buscar usuários novos no período
        todos_usuarios = User.query.all()
        
        usuarios_novos = [
            u for u in todos_usuarios
            if u.data_registro and 
            data_inicio <= tornar_aware(u.data_registro) <= data_fim
        ]
        
        # Verificar quais estão ativados
        usuarios_ativados = []
        
        for user in usuarios_novos:
            if verificar_usuario_ativado(user.id, data_inicio, data_fim):
                # Calcular estatísticas
                simulados = Simulado.query.filter_by(user_id=user.id).count()
                redacoes = Redacao.query.filter_by(user_id=user.id).count()
                
                # Contar aulas
                aulas = TempoEstudo.query.filter(
                    TempoEstudo.user_id == user.id,
                    TempoEstudo.atividade.in_(['aula', 'video', 'aula_assistida'])
                ).count()
                
                # Tempo total
                tempo_total = db.session.query(
                    func.sum(TempoEstudo.minutos)
                ).filter(
                    TempoEstudo.user_id == user.id
                ).scalar() or 0
                
                ultimo_acesso = 'Nunca'
                if user.ultimo_acesso:
                    ultimo_acesso = tornar_aware(user.ultimo_acesso).strftime('%d/%m/%Y %H:%M')
                
                usuarios_ativados.append({
                    'id': user.id,
                    'nome_completo': user.nome_completo or user.username,
                    'telefone': user.telefone or 'Não informado',
                    'ultimo_acesso': ultimo_acesso,
                    'plano': user.plano_ativo or 'free',
                    'tempo_total_horas': round(tempo_total / 60, 1),
                    'total_simulados': simulados,
                    'total_redacoes': redacoes,
                    'total_aulas': aulas
                })
        
        return jsonify({
            'total': len(usuarios_ativados),
            'usuarios': usuarios_ativados,
            'periodo': {
                'inicio': data_inicio.strftime('%d/%m/%Y'),
                'fim': data_fim.strftime('%d/%m/%Y')
            }
        })
        
    except Exception as e:
        print(f"Erro em lista_usuarios_ativados: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

# ============================================================
# NOVA API: DETALHES DE UM USUÁRIO ESPECÍFICO
# ============================================================

@dashboard_analytics_bp.route('/api/usuario/<int:user_id>')
@login_required
def detalhes_usuario(user_id):
    """Retorna detalhes completos de um usuário específico"""
    if not verificar_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    try:
        #from app.models.estatisticas import TempoEstudo
        
        user = User.query.get_or_404(user_id)
        
        # Informações básicas
        dados_basicos = {
            'id': user.id,
            'nome_completo': user.nome_completo,
            'telefone': user.telefone,
            'email': user.email if hasattr(user, 'email') else (user.telefone or 'Não informado'),
            'data_registro': user.data_registro.strftime('%d/%m/%Y %H:%M'),
            'plano_ativo': user.plano_ativo,
            'is_admin': user.is_admin
        }

        # Último acesso
        if user.ultimo_acesso:
            if isinstance(user.ultimo_acesso, datetime):
                dados_basicos['ultimo_acesso'] = user.ultimo_acesso.strftime('%d/%m/%Y %H:%M')
            else:
                dados_basicos['ultimo_acesso'] = user.ultimo_acesso.strftime('%d/%m/%Y')
        else:
            dados_basicos['ultimo_acesso'] = 'Nunca'
        
        # Tempo de uso por funcionalidade
        tempo_por_funcionalidade = db.session.query(
            TempoEstudo.atividade,
            func.sum(TempoEstudo.minutos).label('total_minutos'),
            func.count(TempoEstudo.id).label('total_sessoes')
        ).filter(
            TempoEstudo.user_id == user_id
        ).group_by(
            TempoEstudo.atividade
        ).all()
        
        funcionalidades = []
        tempo_total = 0

        for item in tempo_por_funcionalidade:
            atividade = item.atividade or 'Geral'
            minutos = int(item.total_minutos or 0)
            sessoes = int(item.total_sessoes or 0)
            tempo_total += minutos
            
            funcionalidades.append({
                'atividade': atividade,
                'tempo_minutos': minutos,
                'tempo_horas': round(minutos / 60, 2),
                'sessoes': sessoes,
                'media_por_sessao': round(minutos / sessoes, 1) if sessoes > 0 else 0
            })
        
        # Ordenar por tempo
        funcionalidades.sort(key=lambda x: x['tempo_minutos'], reverse=True)
        
        # Simulados
        simulados = Simulado.query.filter_by(user_id=user_id).order_by(Simulado.data_realizado.desc()).limit(10).all()
        simulados_lista = []
        
        for sim in simulados:
            simulados_lista.append({
                'id': sim.id,
                'status': sim.status,
                'nota_tri': sim.nota_tri,
                'data': sim.data_realizado.strftime('%d/%m/%Y') if sim.data_realizado else 'N/A'
            })
        
        # Redações
        redacoes = Redacao.query.filter_by(user_id=user_id).order_by(Redacao.data_envio.desc()).limit(10).all()
        redacoes_lista = []
        
        for red in redacoes:
            redacoes_lista.append({
                'id': red.id,
                'tema': getattr(red, 'tema', 'Sem tema'),
                'data': red.data_envio.strftime('%d/%m/%Y') if red.data_envio else 'N/A'
            })
        
        # Atividade nos últimos 30 dias (gráfico)
        ultimos_30_dias = now_brasilia() - timedelta(days=30)
        
        atividade_diaria = db.session.query(
            cast(TempoEstudo.data_inicio, Date).label('data'),
            func.sum(TempoEstudo.minutos).label('minutos')
        ).filter(
            TempoEstudo.user_id == user_id,
            TempoEstudo.data_inicio >= ultimos_30_dias
        ).group_by(
            cast(TempoEstudo.data_inicio, Date)
        ).order_by('data').all()
        
        datas_grafico = []
        minutos_grafico = []
        
        for item in atividade_diaria:
            datas_grafico.append(item.data.strftime('%d/%m'))
            minutos_grafico.append(int(item.minutos))
        
        return jsonify({
            'dados_basicos': dados_basicos,
            'tempo_total_minutos': tempo_total,
            'tempo_total_horas': round(tempo_total / 60, 2),
            'tempo_por_funcionalidade': funcionalidades,
            'simulados': {
                'total': Simulado.query.filter_by(user_id=user_id).count(),
                'ultimos': simulados_lista
            },
            'redacoes': {
                'total': Redacao.query.filter_by(user_id=user_id).count(),
                'ultimas': redacoes_lista
            },
            'atividade_30_dias': {
                'datas': datas_grafico,
                'minutos': minutos_grafico
            }
        })
    
    except Exception as e:
        print(f"Erro ao buscar detalhes do usuário: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

# ============================================================
# NOVA API: ANÁLISE AVANÇADA - SEGMENTAÇÃO DE USUÁRIOS COM DRILL-DOWN
# ============================================================

@dashboard_analytics_bp.route('/api/analise-segmentacao')
@login_required
def analise_segmentacao():
    """Segmentação avançada de usuários por comportamento"""
    if not verificar_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    try:
        #from app.models.estatisticas import TempoEstudo
        
        # Segmentação por tempo de uso
        usuarios_com_tempo = db.session.query(
            TempoEstudo.user_id,
            func.sum(TempoEstudo.minutos).label('tempo_total')
        ).group_by(
            TempoEstudo.user_id
        ).subquery()
        
        segmentos = {
            'super_engajados': 0,  # >10h
            'engajados': 0,  # 5-10h
            'moderados': 0,  # 1-5h
            'baixo_engajamento': 0,  # <1h
            'inativos': 0  # 0h
        }
        
        total_usuarios = User.query.count()
        
        usuarios_query = db.session.query(
            User.id,
            func.coalesce(usuarios_com_tempo.c.tempo_total, 0).label('tempo')
        ).outerjoin(
            usuarios_com_tempo,
            User.id == usuarios_com_tempo.c.user_id
        ).all()
        
        for user in usuarios_query:
            tempo_horas = user.tempo / 60
            
            if tempo_horas == 0:
                segmentos['inativos'] += 1
            elif tempo_horas < 1:
                segmentos['baixo_engajamento'] += 1
            elif tempo_horas < 5:
                segmentos['moderados'] += 1
            elif tempo_horas < 10:
                segmentos['engajados'] += 1
            else:
                segmentos['super_engajados'] += 1
        
        # Conversão em percentuais
        segmentos_percentual = {
            k: round(v / total_usuarios * 100, 2) if total_usuarios > 0 else 0
            for k, v in segmentos.items()
        }
        
        return jsonify({
            'segmentos': segmentos,
            'segmentos_percentual': segmentos_percentual,
            'total_usuarios': total_usuarios
        })
    
    except Exception as e:
        print(f"Erro na análise de segmentação: {e}")
        return jsonify({'erro': str(e)}), 500

# ============================================================
# ✅ NOVO ENDPOINT: DRILL-DOWN DE SEGMENTAÇÃO
# ============================================================

@dashboard_analytics_bp.route('/api/analise-segmentacao/<string:segmento>')
@login_required
def drill_down_segmentacao(segmento):
    """Lista usuários de um segmento específico"""
    if not verificar_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    try:
        #from app.models.estatisticas import TempoEstudo
        
        # Definir range do segmento
        ranges = {
            'super_engajados': (600, None),  # >10h = >600min
            'engajados': (300, 600),  # 5-10h = 300-600min
            'moderados': (60, 300),  # 1-5h = 60-300min
            'baixo_engajamento': (1, 60),  # <1h = 1-60min
            'inativos': (0, 0)  # 0h
        }
        
        if segmento not in ranges:
            return jsonify({'erro': 'Segmento inválido'}), 400
        
        min_minutos, max_minutos = ranges[segmento]
        
        # Query de usuários com tempo
        usuarios_com_tempo = db.session.query(
            User.id,
            User.nome_completo,
            User.username,
            User.telefone,
            User.plano_ativo,
            User.ultimo_acesso,
            func.sum(TempoEstudo.minutos).label('tempo_total')
        ).outerjoin(
            TempoEstudo, User.id == TempoEstudo.user_id
        ).group_by(
            User.id, User.nome_completo,
            User.username, User.telefone, User.plano_ativo, User.ultimo_acesso
        ).all()
        
        # Filtrar por range
        usuarios_filtrados = []
        for u in usuarios_com_tempo:
            tempo = u.tempo_total or 0
            
            if max_minutos is None:  # super_engajados
                if tempo >= min_minutos:
                    usuarios_filtrados.append(u)
            elif segmento == 'inativos':
                if tempo == 0:
                    usuarios_filtrados.append(u)
            else:
                if min_minutos <= tempo < max_minutos:
                    usuarios_filtrados.append(u)
        
        # Formatar resposta
        resultado = []
        for u in usuarios_filtrados[:100]:  # Limitar a 100
            tempo_horas = (u.tempo_total or 0) / 60
            
            resultado.append({
                'id': u.id,
                'nome_completo': u.nome_completo,
                'telefone': u.telefone,
                'plano': u.plano_ativo,
                'tempo_total_horas': round(tempo_horas, 2),
                'tempo_total_minutos': int(u.tempo_total or 0),
                'ultimo_acesso': u.ultimo_acesso.strftime('%d/%m/%Y') if u.ultimo_acesso else 'Nunca'
            })
        
        # Ordenar por tempo
        resultado.sort(key=lambda x: x['tempo_total_minutos'], reverse=True)


        return jsonify({
            'segmento': segmento,
            'total': len(resultado),
            'usuarios': resultado
        })
        
    except Exception as e:
        print(f"Erro no drill-down de segmentação: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500

# ============================================================
# NOVA API: ANÁLISE AVANÇADA - PADRÕES DE USO
# ============================================================

@dashboard_analytics_bp.route('/api/analise-padroes-uso')
@login_required
def analise_padroes_uso():
    """Análise de padrões de uso por hora do dia e dia da semana"""
    if not verificar_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    try:
        #from app.models.estatisticas import TempoEstudo
        
        data_inicio, data_fim = parse_date_filter(request)
        
        # Uso por hora do dia
        uso_por_hora = db.session.query(
            extract('hour', TempoEstudo.data_inicio).label('hora'),
            func.count(TempoEstudo.id).label('total_sessoes'),
            func.sum(TempoEstudo.minutos).label('total_minutos')
        ).filter(
            TempoEstudo.data_inicio.between(data_inicio, data_fim)
        ).group_by(
            'hora'
        ).order_by('hora').all()
        
        horas = []
        sessoes_por_hora = []
        minutos_por_hora = []
        
        for i in range(24):
            horas.append(f"{i:02d}:00")
            sessoes_por_hora.append(0)
            minutos_por_hora.append(0)
        
        for item in uso_por_hora:
            hora_idx = int(item.hora)
            sessoes_por_hora[hora_idx] = int(item.total_sessoes)
            minutos_por_hora[hora_idx] = int(item.total_minutos or 0)
        
        # Uso por dia da semana
        uso_por_dia_semana = db.session.query(
            extract('dow', TempoEstudo.data_inicio).label('dia_semana'),
            func.count(TempoEstudo.id).label('total_sessoes'),
            func.sum(TempoEstudo.minutos).label('total_minutos')
        ).filter(
            TempoEstudo.data_inicio.between(data_inicio, data_fim)
        ).group_by(
            'dia_semana'
        ).order_by('dia_semana').all()
        
        dias_semana = ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado']
        sessoes_por_dia = [0] * 7
        minutos_por_dia = [0] * 7
        
        for item in uso_por_dia_semana:
            dia_idx = int(item.dia_semana)
            sessoes_por_dia[dia_idx] = int(item.total_sessoes)
            minutos_por_dia[dia_idx] = int(item.total_minutos or 0)
        
        return jsonify({
            'uso_por_hora': {
                'labels': horas,
                'sessoes': sessoes_por_hora,
                'minutos': minutos_por_hora
            },
            'uso_por_dia_semana': {
                'labels': dias_semana,
                'sessoes': sessoes_por_dia,
                'minutos': minutos_por_dia
            },
            'periodo': {
                'inicio': data_inicio.strftime('%Y-%m-%d'),
                'fim': data_fim.strftime('%Y-%m-%d')
            }
        })
    
    except Exception as e:
        print(f"Erro na análise de padrões: {e}")
        return jsonify({'erro': str(e)}), 500

# ============================================================
# APIs MANTIDAS (com suporte a filtro de data)
# ============================================================


@dashboard_analytics_bp.route('/api/crescimento-usuarios')
@login_required
def crescimento_usuarios():
    """Retorna dados de crescimento de usuários"""
    if not verificar_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    try:
        data_inicio, data_fim = parse_date_filter(request)
        dias = (data_fim.date() - data_inicio.date()).days
        
        registros_diarios = db.session.query(
            cast(User.data_registro, Date).label('data'),
            func.count(User.id).label('total')
        ).filter(
            User.data_registro.between(data_inicio, data_fim)
        ).group_by(
            cast(User.data_registro, Date)
        ).order_by('data').all()
        
        datas = []
        totais = []
        acumulado = User.query.filter(User.data_registro < data_inicio).count()
        acumulados = []
        
        registros_dict = {r.data: r.total for r in registros_diarios}
        
        for i in range(dias + 1):
            data_atual = (data_inicio.date() + timedelta(days=i))
            total_dia = registros_dict.get(data_atual, 0)
            acumulado += total_dia
            
            datas.append(data_atual.strftime('%d/%m'))
            totais.append(total_dia)
            acumulados.append(acumulado)
        
        return jsonify({
            'labels': datas,
            'novos': totais,
            'acumulado': acumulados
        })
    
    except Exception as e:
        print(f"Erro ao calcular crescimento: {e}")
        return jsonify({'erro': str(e)}), 500

@dashboard_analytics_bp.route('/api/funil-conversao')
@login_required
def funil_conversao():
    """Retorna dados do funil de conversão"""
    if not verificar_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    try:
        data_inicio, data_fim = parse_date_filter(request)
        
        total_registros = User.query.filter(
            User.data_registro.between(data_inicio, data_fim)
        ).count()
        
        usuarios_com_atividade = set()
        
        usuarios_simulados = db.session.query(Simulado.user_id).join(
            User, Simulado.user_id == User.id
        ).filter(
            User.data_registro.between(data_inicio, data_fim)
        ).distinct().all()
        usuarios_com_atividade.update([u[0] for u in usuarios_simulados])
        
        usuarios_redacoes = db.session.query(Redacao.user_id).join(
            User, Redacao.user_id == User.id
        ).filter(
            User.data_registro.between(data_inicio, data_fim)
        ).distinct().all()
        usuarios_com_atividade.update([u[0] for u in usuarios_redacoes])
        
        total_com_atividade = len(usuarios_com_atividade)
        
        usuarios_pagantes = User.query.filter(
            User.data_registro.between(data_inicio, data_fim),
            User.plano_ativo.in_(['mensal', 'anual']),
            User.data_expiracao_plano > now_brasilia()
        ).count()
        
        return jsonify({
            'funil': [
                {'etapa': 'Registro', 'total': total_registros, 'percentual': 100},
                {'etapa': 'Ativação', 'total': total_com_atividade, 'percentual': round(total_com_atividade/total_registros*100, 2) if total_registros > 0 else 0},
                {'etapa': 'Conversão (Pago)', 'total': usuarios_pagantes, 'percentual': round(usuarios_pagantes/total_registros*100, 2) if total_registros > 0 else 0}
            ]
        })
    
    except Exception as e:
        print(f"Erro ao calcular funil: {e}")
        return jsonify({'erro': str(e)}), 500

@dashboard_analytics_bp.route('/api/distribuicao-planos')
@login_required
def distribuicao_planos():
    """Retorna distribuição de usuários por plano"""
    if not verificar_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    try:
        distribuicao = db.session.query(
            User.plano_ativo,
            func.count(User.id)
        ).group_by(User.plano_ativo).all()
        
        planos = []
        totais = []
        
        for plano, total in distribuicao:
            nome_plano = {
                'free': 'Gratuito',
                'mensal': 'Mensal',
                'anual': 'Anual'
            }.get(plano, plano)
            
            planos.append(nome_plano)
            totais.append(total)
        
        return jsonify({
            'labels': planos,
            'values': totais
        })
    
    except Exception as e:
        print(f"Erro ao calcular distribuição: {e}")
        return jsonify({'erro': str(e)}), 500

@dashboard_analytics_bp.route('/api/performance-simulados')
@login_required
def performance_simulados():
    """Retorna métricas de performance em simulados"""
    if not verificar_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    try:
        data_inicio, data_fim = parse_date_filter(request)
        
        simulados = Simulado.query.filter(
            Simulado.data_realizado.between(data_inicio, data_fim),
            Simulado.status == 'Concluído'
        ).all()
        
        if not simulados:
            return jsonify({
                'total_simulados': 0,
                'nota_media': 0,
                'nota_minima': 0,
                'nota_maxima': 0,
                'evolucao_notas': []
            })
        
        notas = [s.nota_tri for s in simulados if s.nota_tri]
        
        return jsonify({
            'total_simulados': len(simulados),
            'nota_media': round(sum(notas) / len(notas), 2) if notas else 0,
            'nota_minima': min(notas) if notas else 0,
            'nota_maxima': max(notas) if notas else 0,
            'evolucao_notas': [round(n, 1) for n in notas[-10:]]
        })
    
    except Exception as e:
        print(f"Erro ao calcular performance: {e}")
        return jsonify({'erro': str(e)}), 500


@dashboard_analytics_bp.route('/api/retencao-coortes')
@login_required
def retencao_coortes():
    """Retorna análise de retenção por coortes"""
    if not verificar_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    try:
        semanas = []
        hoje = now_brasilia().date()
        
        for i in range(8):
            inicio_semana = hoje - timedelta(weeks=i+1)
            fim_semana = inicio_semana + timedelta(days=6)
            
            inicio_dt = BRASILIA_TZ.localize(datetime.combine(inicio_semana, datetime.min.time()))
            fim_dt = BRASILIA_TZ.localize(datetime.combine(fim_semana, datetime.max.time()))
            
            usuarios_coorte = User.query.filter(
                User.data_registro >= inicio_dt,
                User.data_registro <= fim_dt
            ).all()

            if not usuarios_coorte:
                continue
            
            total_coorte = len(usuarios_coorte)
            retencoes = []
            
            for semana_futura in range(1, min(i+1, 4)):
                data_check = fim_semana + timedelta(weeks=semana_futura)
                
                usuarios_retidos = sum(
                    1 for u in usuarios_coorte 
                    if u.ultimo_acesso and safe_date(u.ultimo_acesso) >= data_check
                )
                
                taxa_retencao = (usuarios_retidos / total_coorte * 100) if total_coorte > 0 else 0
                retencoes.append(round(taxa_retencao, 1))
            
            semanas.append({
                'inicio': inicio_semana.strftime('%d/%m'),
                'total': total_coorte,
                'retencoes': retencoes
            })
        
        return jsonify({
            'coortes': list(reversed(semanas))
        })
    
    except Exception as e:
        print(f"Erro ao calcular coortes: {e}")
        return jsonify({'erro': str(e)}), 500

@dashboard_analytics_bp.route('/api/metricas-ativacao-detalhadas')
@login_required
def metricas_ativacao_detalhadas():
    """Retorna métricas detalhadas de ativação - CORRIGIDO COM AULAS"""
    if not verificar_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    try:
        data_inicio, data_fim = parse_date_filter(request)
        #from app.models.estatisticas import TempoEstudo
        
        novos_usuarios = User.query.filter(
            User.data_registro.between(data_inicio, data_fim)
        ).all()
        
        total_novos = len(novos_usuarios)
        usuarios_ativados_ids = set()
        tempo_uso_ativados = {}
        
        # ✅ CORRIGIDO: Usar nova função que inclui aulas
        for user in novos_usuarios:
            if verificar_usuario_ativado(user.id):
                usuarios_ativados_ids.add(user.id)
        
        tempos_por_usuario = db.session.query(
            TempoEstudo.user_id,
            func.sum(TempoEstudo.minutos).label('total_minutos')
        ).filter(
            TempoEstudo.user_id.in_(usuarios_ativados_ids)
        ).group_by(TempoEstudo.user_id).all()
        
        tempo_uso_ativados = {user_id: total for user_id, total in tempos_por_usuario}
        
        tempo_total = sum(tempo_uso_ativados.values())
        tempo_medio = (tempo_total / len(usuarios_ativados_ids)) if usuarios_ativados_ids else 0
        
        taxa_ativacao = (len(usuarios_ativados_ids) / total_novos * 100) if total_novos > 0 else 0
        
        retorno_d1 = 0
        retorno_d7 = 0
        
        for user in novos_usuarios:
            if not user.ultimo_acesso or not user.data_registro:
                continue
                
            data_registro = safe_date(user.data_registro)
            ultimo_acesso_date = safe_date(user.ultimo_acesso)
            
            if not data_registro or not ultimo_acesso_date:
                continue
            
            diff = (ultimo_acesso_date - data_registro).days
            
            if diff >= 1:
                retorno_d1 += 1
            
            if 1 <= diff <= 7:
                retorno_d7 += 1
        
        taxa_retorno_d1 = (retorno_d1 / total_novos * 100) if total_novos > 0 else 0
        taxa_retorno_d7 = (retorno_d7 / total_novos * 100) if total_novos > 0 else 0
        
        distribuicao_tempo = {
            '0-30min': 0,
            '30-60min': 0,
            '1-2h': 0,
            '2-5h': 0,
            '5h+': 0
        }
        
        for tempo in tempo_uso_ativados.values():
            if tempo < 30:
                distribuicao_tempo['0-30min'] += 1
            elif tempo < 60:
                distribuicao_tempo['30-60min'] += 1
            elif tempo < 120:
                distribuicao_tempo['1-2h'] += 1
            elif tempo < 300:
                distribuicao_tempo['2-5h'] += 1
            else:
                distribuicao_tempo['5h+'] += 1
        
        dias = (data_fim.date() - data_inicio.date()).days


        return jsonify({
            'periodo_dias': dias,
            'total_novos_usuarios': total_novos,
            'usuarios_ativados': len(usuarios_ativados_ids),
            'taxa_ativacao': round(taxa_ativacao, 2),
            'retorno_d1': retorno_d1,
            'taxa_retorno_d1': round(taxa_retorno_d1, 2),
            'retorno_d7': retorno_d7,
            'taxa_retorno_d7': round(taxa_retorno_d7, 2),
            'tempo_medio_uso_ativados_minutos': round(tempo_medio, 2),
            'tempo_medio_uso_ativados_horas': round(tempo_medio / 60, 2),
            'distribuicao_tempo': distribuicao_tempo,
            'periodo': {
                'inicio': data_inicio.strftime('%Y-%m-%d'),
                'fim': data_fim.strftime('%Y-%m-%d')
            }
        })
    
    except Exception as e:
        print(f"Erro ao calcular métricas detalhadas: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500


# ============================================================
# APIs DE DETALHAMENTO (DRILL-DOWN) - CORRIGIDAS
# ============================================================
@dashboard_analytics_bp.route('/api/detalhes/total-usuarios')
def detalhes_total_usuarios():
    """
    ERRO ORIGINAL:
    "can't compare offset-naive and offset-aware datetimes"
    
    CAUSA:
    user.data_registro (naive) sendo comparado com data_inicio (aware)
    """
    try:
        data_inicio, data_fim = parse_date_filter(request)
        
        # ✅ SOLUÇÃO: Buscar todos e filtrar em Python
        todos_usuarios = User.query.order_by(User.data_registro.desc()).all()
        
        # Filtrar novos usuários do período (com conversão para aware)
        novos_usuarios = []
        for user in todos_usuarios:
            if user.data_registro:
                data_reg_aware = tornar_aware(user.data_registro)
                if data_inicio <= data_reg_aware <= data_fim:
                    novos_usuarios.append({
                        'id': user.id,
                        'nome_completo': user.nome_completo or user.username,
                        'telefone': user.telefone or 'Não informado',
                        'data_registro': data_reg_aware.strftime('%d/%m/%Y %H:%M'),
                        'is_novo': True
                    })
        
        # Preparar lista de todos os usuários
        todos_usuarios_data = []
        for user in todos_usuarios[:100]:  # Limitar a 100 para performance
            data_reg = tornar_aware(user.data_registro) if user.data_registro else None
            ultimo_acesso = tornar_aware(user.ultimo_acesso) if user.ultimo_acesso else None
            
            # Verificar se é novo
            is_novo = False
            if data_reg:
                is_novo = data_inicio <= data_reg <= data_fim
            
            todos_usuarios_data.append({
                'id': user.id,
                'nome_completo': user.nome_completo,
                'telefone': user.telefone,
                'data_registro': data_reg.strftime('%d/%m/%Y %H:%M') if data_reg else 'N/A',
                'ultimo_acesso': ultimo_acesso.strftime('%d/%m/%Y %H:%M') if ultimo_acesso else 'N/A',
                'plano': user.plano_ativo or 'free',
                'is_novo': is_novo
            })
        
        return jsonify({
            'total': len(todos_usuarios),
            'novos_periodo': len(novos_usuarios),
            'novos_usuarios': novos_usuarios,
            'todos_usuarios': todos_usuarios_data,
            'periodo': {
                'inicio': data_inicio.strftime('%d/%m/%Y'),
                'fim': data_fim.strftime('%d/%m/%Y')
            }
        })
        
    except Exception as e:
        print(f"Erro em detalhes_total_usuarios: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500


# ============================================================
# CORREÇÃO 2: /api/detalhes/usuarios-premium
# ============================================================

@dashboard_analytics_bp.route('/api/detalhes/usuarios-premium')
def detalhes_usuarios_premium():
    """
    ERRO ORIGINAL:
    "can't subtract offset-naive and offset-aware datetimes"
    
    CAUSA:
    user.data_expiracao_plano (naive) sendo subtraído de hoje (aware)
    """
    try:
        hoje = now_brasilia()
        
        # Buscar todos os usuários premium
        usuarios_query = User.query.filter(
            User.plano_ativo.in_(['mensal', 'anual'])
        ).all()
        
        # ✅ SOLUÇÃO: Filtrar e calcular em Python com tornar_aware()
        usuarios_premium = []
        mensais = 0
        anuais = 0
        
        for user in usuarios_query:
            # Converter data de expiração para aware
            if not user.data_expiracao_plano:
                continue
                
            expiracao_aware = tornar_aware(user.data_expiracao_plano)
            
            # Verificar se ainda está ativo
            if expiracao_aware <= hoje:
                continue
            
            # Calcular dias restantes
            dias_restantes = (expiracao_aware - hoje).days
            
            # Contar planos
            if user.plano_ativo == 'mensal':
                mensais += 1
            elif user.plano_ativo == 'anual':
                anuais += 1
            
            # Formatar último acesso
            ultimo_acesso = 'Nunca'
            if user.ultimo_acesso:
                ultimo_acesso_aware = tornar_aware(user.ultimo_acesso)
                ultimo_acesso = ultimo_acesso_aware.strftime('%d/%m/%Y %H:%M')
            
            usuarios_premium.append({
                'id': user.id,
                'nome_completo': user.nome_completo or user.username,
                'telefone': user.telefone or 'Não informado',
                'plano': user.plano_ativo,
                'expira_em': expiracao_aware.strftime('%d/%m/%Y'),
                'dias_restantes': dias_restantes,
                'ultimo_acesso': ultimo_acesso
            })
        
        return jsonify({
            'total': len(usuarios_premium),
            'mensais': mensais,
            'anuais': anuais,
            'usuarios': usuarios_premium
        })
        
    except Exception as e:
        print(f"Erro em detalhes_usuarios_premium: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500



# ============================================================
# ✅ API RETORNO D1 (CORRIGIDA COM DETALHAMENTO DE ATIVIDADES)
# ============================================================

@dashboard_analytics_bp.route('/api/detalhes/retorno-d1')
@login_required
def detalhes_retorno_d1():
    """Detalhes dos usuários que retornaram D1 - CORRIGIDO COM TEMPO POR ATIVIDADE"""
    if not verificar_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    try:
        data_inicio, data_fim = parse_date_filter(request)
        #from app.models.estatisticas import TempoEstudo
        
        # Usuários que se registraram no período
        novos_usuarios = db.session.query(
            User.id,
            User.nome_completo,
            User.username,
            User.telefone,
            User.data_registro,
            User.ultimo_acesso
        ).filter(
            User.data_registro.between(data_inicio, data_fim)
        ).all()
        
        # Verificar quem retornou D1
        usuarios_d1 = []
        for user in novos_usuarios:
            if user.ultimo_acesso and user.data_registro:
                try:
                    data_registro = safe_date(user.data_registro)
                    ultimo_acesso = safe_date(user.ultimo_acesso)
                    
                    if data_registro and ultimo_acesso:
                        diff = (ultimo_acesso - data_registro).days
                        retornou_d1 = diff >= 1
                        
                        # ✅ NOVO: Buscar tempo por atividade
                        tempo_atividades = db.session.query(
                            TempoEstudo.atividade,
                            func.sum(TempoEstudo.minutos).label('total_minutos')
                        ).filter(
                            TempoEstudo.user_id == user.id
                        ).group_by(TempoEstudo.atividade).all()
                        
                        detalhes_tempo = []
                        for ativ, minutos in tempo_atividades:
                            detalhes_tempo.append({
                                'atividade': ativ or 'Geral',
                                'tempo_minutos': int(minutos or 0),
                                'tempo_horas': round((minutos or 0) / 60, 2)
                            })
                        
                        usuarios_d1.append({
                            'id': user.id,
                            'nome_completo': user.nome_completo or user.username,
                            'telefone': user.telefone or 'Não informado',
                            'data_registro': user.data_registro.strftime('%d/%m/%Y %H:%M') if isinstance(user.data_registro, datetime) else str(user.data_registro),
                            'ultimo_acesso': user.ultimo_acesso.strftime('%d/%m/%Y %H:%M') if isinstance(user.ultimo_acesso, datetime) else str(user.ultimo_acesso),
                            'dias_ate_retorno': diff,
                            'retornou_d1': retornou_d1,
                            'tempo_por_atividade': detalhes_tempo  # ✅ NOVO
                        })
                except Exception as e:
                    print(f"Erro processando user {user.id}: {str(e)}")
                    continue
        
        retornaram = [u for u in usuarios_d1 if u['retornou_d1']]
        
        return jsonify({
            'usuarios': usuarios_d1,
            'total_novos': len(novos_usuarios),
            'total_retornaram_d1': len(retornaram),
            'taxa_retorno': round((len(retornaram) / len(novos_usuarios) * 100), 2) if len(novos_usuarios) > 0 else 0,
            'periodo': {
                'inicio': data_inicio.strftime('%d/%m/%Y'),
                'fim': data_fim.strftime('%d/%m/%Y')
            }
        })
    except Exception as e:
        print(f"Erro em detalhes_retorno_d1: {str(e)}")
        return jsonify({'erro': str(e)}), 500


# ============================================================
# ✅ API RETORNO D7 (CORRIGIDA COM DETALHAMENTO DE ATIVIDADES)
# ============================================================

@dashboard_analytics_bp.route('/api/detalhes/retorno-d7')
@login_required
def detalhes_retorno_d7():
    """Detalhes dos usuários que retornaram D7 - CORRIGIDO COM TEMPO POR ATIVIDADE"""
    if not verificar_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    try:
        data_inicio, data_fim = parse_date_filter(request)
        #from app.models.estatisticas import TempoEstudo
        
        # Usuários que se registraram no período
        novos_usuarios = db.session.query(
            User.id,
            User.nome_completo,
            User.nome_completo,
            User.username,
            User.telefone,
            User.telefone,
            User.data_registro,
            User.ultimo_acesso
        ).filter(
            User.data_registro.between(data_inicio, data_fim)
        ).all()
        
        # Verificar quem retornou D7
        usuarios_d7 = []
        for user in novos_usuarios:
            if user.ultimo_acesso and user.data_registro:
                try:
                    data_registro = safe_date(user.data_registro)
                    ultimo_acesso = safe_date(user.ultimo_acesso)
                    
                    if data_registro and ultimo_acesso:
                        diff = (ultimo_acesso - data_registro).days
                        retornou_d7 = diff >= 1 and diff <= 7
                        
                        # ✅ NOVO: Buscar tempo por atividade
                        tempo_atividades = db.session.query(
                            TempoEstudo.atividade,
                            func.sum(TempoEstudo.minutos).label('total_minutos')
                        ).filter(
                            TempoEstudo.user_id == user.id
                        ).group_by(TempoEstudo.atividade).all()
                        
                        detalhes_tempo = []
                        for ativ, minutos in tempo_atividades:
                            detalhes_tempo.append({
                                'atividade': ativ or 'Geral',
                                'tempo_minutos': int(minutos or 0),
                                'tempo_horas': round((minutos or 0) / 60, 2)
                            })
                        
                        usuarios_d7.append({
                            'id': user.id,
                            'nome_completo': user.nome_completo or user.username,
                            'telefone': user.telefone or 'Não informado',
                            'data_registro': user.data_registro.strftime('%d/%m/%Y %H:%M') if isinstance(user.data_registro, datetime) else str(user.data_registro),
                            'ultimo_acesso': user.ultimo_acesso.strftime('%d/%m/%Y %H:%M') if isinstance(user.ultimo_acesso, datetime) else str(user.ultimo_acesso),
                            'dias_ate_retorno': diff,
                            'retornou_d7': retornou_d7,
                            'tempo_por_atividade': detalhes_tempo  # ✅ NOVO
                        })
                except Exception as e:
                    print(f"Erro processando user {user.id}: {str(e)}")
                    continue
        
        retornaram = [u for u in usuarios_d7 if u['retornou_d7']]
        
        return jsonify({
            'usuarios': usuarios_d7,
            'total_novos': len(novos_usuarios),
            'total_retornaram_d7': len(retornaram),
            'taxa_retorno': round((len(retornaram) / len(novos_usuarios) * 100), 2) if len(novos_usuarios) > 0 else 0,
            'periodo': {
                'inicio': data_inicio.strftime('%d/%m/%Y'),
                'fim': data_fim.strftime('%d/%m/%Y')
            }
        })
    except Exception as e:
        print(f"Erro em detalhes_retorno_d7: {str(e)}")
        return jsonify({'erro': str(e)}), 500



# ============================================================
# API TEMPO MÉDIO (CORRIGIDA)
# ============================================================
@dashboard_analytics_bp.route('/api/detalhes/tempo-medio')
@login_required
def detalhes_tempo_medio():
    """Detalhes do tempo médio de uso por usuário"""
    if not verificar_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    try:
        data_inicio, data_fim = parse_date_filter(request)
        #from app.models.estatisticas import TempoEstudo

        usuarios_tempo = db.session.query(
            User.id,
            User.nome_completo,
            User.username,
            User.telefone,
            User.plano_ativo,
            func.sum(TempoEstudo.minutos).label('total_minutos'),
            func.count(TempoEstudo.id).label('total_sessoes')
        ).join(
            TempoEstudo, User.id == TempoEstudo.user_id
        ).filter(
            TempoEstudo.data_inicio.between(data_inicio, data_fim),
            TempoEstudo.minutos > 0
        ).group_by(
            User.id, User.nome_completo,
            User.username, User.telefone, User.plano_ativo
        ).order_by(
            func.sum(TempoEstudo.minutos).desc()
        ).all()
        
        # Formatar dados
        usuarios_formatados = []
        for u in usuarios_tempo:
            try:
                total_horas = float(u.total_minutos) / 60 if u.total_minutos else 0
                media_por_sessao = float(u.total_minutos) / u.total_sessoes if u.total_sessoes > 0 else 0
                
                usuarios_formatados.append({
                    'id': u.id,
                    'nome_completo': u.nome_completo,
                    'telefone': u.telefone,
                    'plano': u.plano_ativo,
                    'total_minutos': int(u.total_minutos) if u.total_minutos else 0,
                    'total_horas': round(total_horas, 2),
                    'total_sessoes': int(u.total_sessoes) if u.total_sessoes else 0,
                    'media_por_sessao': round(media_por_sessao, 1)
                })
            except Exception as e:
                print(f"Erro formatando user {u.id}: {str(e)}")
                continue
        
        # Buscar atividades por usuário
        atividades_por_usuario = {}
        for u in usuarios_tempo:
            try:
                atividades = db.session.query(
                    TempoEstudo.atividade,
                    func.sum(TempoEstudo.minutos).label('minutos')
                ).filter(
                    TempoEstudo.user_id == u.id,
                    TempoEstudo.data_inicio.between(data_inicio, data_fim),
                    TempoEstudo.minutos > 0
                ).group_by(TempoEstudo.atividade).all()
                
                atividades_por_usuario[u.id] = [{
                    'atividade': a.atividade or 'Geral',
                    'minutos': int(a.minutos) if a.minutos else 0
                } for a in atividades]
            except Exception as e:
                print(f"Erro buscando atividades user {u.id}: {str(e)}")
                atividades_por_usuario[u.id] = []
        
        # Adicionar atividades aos usuários
        for u in usuarios_formatados:
            u['atividades'] = atividades_por_usuario.get(u['id'], [])
        
        return jsonify({
            'usuarios': usuarios_formatados,
            'total_usuarios': len(usuarios_formatados),
            'periodo': {
                'inicio': data_inicio.strftime('%d/%m/%Y'),
                'fim': data_fim.strftime('%d/%m/%Y')
            }
        })
    except Exception as e:
        print(f"Erro em detalhes_tempo_medio: {str(e)}")
        return jsonify({'erro': str(e)}), 500


# ============================================================
# CORREÇÃO 3: /api/detalhes/dau
# ============================================================

@dashboard_analytics_bp.route('/api/detalhes/dau')
def detalhes_dau():
    """
    Daily Active Users - com correção de timezone
    """
    try:
        hoje = now_brasilia().date()
        
        # Buscar todos os usuários
        todos_usuarios = User.query.all()
        
        # ✅ SOLUÇÃO: Filtrar em Python com tornar_aware()
        usuarios_ativos = []
        
        for user in todos_usuarios:
            if not user.ultimo_acesso:
                continue
            
            # Converter para aware e extrair date
            ultimo_acesso_aware = tornar_aware(user.ultimo_acesso)
            ultimo_acesso_date = ultimo_acesso_aware.date()
            
            # Verificar se acessou hoje
            if ultimo_acesso_date == hoje:
                usuarios_ativos.append({
                    'id': user.id,
                    'nome_completo': user.nome_completo or user.username,
                    'telefone': user.telefone or 'Não informado',
                    'plano': user.plano_ativo or 'free',
                    'ultimo_acesso': ultimo_acesso_aware.strftime('%d/%m/%Y %H:%M')
                })
        
        return jsonify({
            'total': len(usuarios_ativos),
            'data': hoje.strftime('%d/%m/%Y'),
            'usuarios': usuarios_ativos
        })
        
    except Exception as e:
        print(f"Erro em detalhes_dau: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500


# ============================================================
# CORREÇÃO 4: /api/detalhes/mau
# ============================================================

@dashboard_analytics_bp.route('/api/detalhes/mau')
def detalhes_mau():
    """
    Monthly Active Users - com correção de timezone
    """
    try:
        hoje = now_brasilia().date()
        inicio_mes = hoje.replace(day=1)
        
        # Buscar todos os usuários
        todos_usuarios = User.query.all()
        
        # ✅ SOLUÇÃO: Filtrar em Python com tornar_aware()
        usuarios_ativos = []
        
        for user in todos_usuarios:
            if not user.ultimo_acesso:
                continue
            
            # Converter para aware e extrair date
            ultimo_acesso_aware = tornar_aware(user.ultimo_acesso)
            ultimo_acesso_date = ultimo_acesso_aware.date()
            
            # Verificar se acessou neste mês
            if ultimo_acesso_date >= inicio_mes:
                usuarios_ativos.append({
                    'id': user.id,
                    'nome_completo': user.nome_completo or user.username,
                    'telefone': user.telefone or 'Não informado',
                    'plano': user.plano_ativo or 'free',
                    'ultimo_acesso': ultimo_acesso_aware.strftime('%d/%m/%Y %H:%M')
                })
        
        return jsonify({
            'total': len(usuarios_ativos),
            'mes': hoje.strftime('%B %Y'),
            'periodo': {
                'inicio': inicio_mes.strftime('%d/%m/%Y'),
                'fim': hoje.strftime('%d/%m/%Y')
            },
            'usuarios': usuarios_ativos
        })
        
    except Exception as e:
        print(f"Erro em detalhes_mau: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'erro': str(e)}), 500




@dashboard_analytics_bp.route('/api/detalhes/churn')
@login_required
def detalhes_churn():
    """Detalhes dos usuários que cancelaram (churn)"""
    if not verificar_admin():
        return jsonify({'erro': 'Acesso negado'}), 403


    
    try:
        data_inicio, data_fim = parse_date_filter(request)
        
        # Usuários que expiraram no período
        usuarios = db.session.query(
            User.id,
            User.nome_completo,
            User.username,
            User.telefone,
            User.plano_ativo,
            User.data_expiracao_plano,
            User.data_registro
        ).filter(
            User.data_expiracao_plano.between(data_inicio, data_fim),
            User.plano_ativo == 'free'
        ).order_by(User.data_expiracao_plano.desc()).all()
        
        return jsonify({
            'total': len(usuarios),
            'periodo': {
                'inicio': data_inicio.strftime('%d/%m/%Y'),
                'fim': data_fim.strftime('%d/%m/%Y')
            },
            'usuarios': [{
                'id': u.id,
                'nome_completo': u.nome_completo,
                'telefone': u.telefone,
                'plano_atual': u.plano_ativo,
                'expirou_em': u.data_expiracao_plano.strftime('%d/%m/%Y') if u.data_expiracao_plano else 'N/A',
                'tempo_como_cliente': (u.data_expiracao_plano - u.data_registro).days if u.data_expiracao_plano and u.data_registro else 0
            } for u in usuarios]
        })
    except Exception as e:
        return jsonify({'erro': str(e)}), 500



@dashboard_analytics_bp.route('/api/detalhes/mrr')
@login_required
def detalhes_mrr():
    """Detalhes do MRR (Monthly Recurring Revenue)"""
    if not verificar_admin():
        return jsonify({'erro': 'Acesso negado'}), 403
    
    try:
        # Usuários com plano mensal ativo
        usuarios_mensais = db.session.query(
            User.id,
            User.nome_completo,
            User.username,
            User.telefone,
            User.data_registro,
            User.data_expiracao_plano
        ).filter(
            User.plano_ativo == 'mensal',
            User.data_expiracao_plano > now_brasilia()
        ).order_by(User.data_expiracao_plano.asc()).all()
        
        # Valor por usuário (configurável)
        valor_mensal = 49.90
        
        usuarios_formatados = [{
            'id': u.id,
            'nome_completo': u.nome_completo,
            'telefone': u.telefone,
            'valor': valor_mensal,
            'data_registro': u.data_registro.strftime('%d/%m/%Y') if u.data_registro else 'N/A',
            'proxima_cobranca': u.data_expiracao_plano.strftime('%d/%m/%Y') if u.data_expiracao_plano else 'N/A'
        } for u in usuarios_mensais]
        
        mrr_total = len(usuarios_mensais) * valor_mensal
        
        return jsonify({
            'total_assinantes': len(usuarios_mensais),
            'valor_por_assinante': valor_mensal,
            'mrr_total': mrr_total,
            'usuarios': usuarios_formatados
        })
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
