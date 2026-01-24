# app/routes/admin_analytics.py
"""
Painel de Métricas Administrativas - Versão Corrigida (V3.1)
Correção de atributos de data e otimização de consultas.
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import func, and_, or_, desc
from datetime import datetime, timedelta
from app import db
from app.models.user import User
from app.models.simulado import Simulado
from app.models.estatisticas import TempoEstudo, ExercicioRealizado

# Importação protegida para evitar erros se o modelo não existir
try:
    from app.models.redacao import Redacao
except ImportError:
    Redacao = None

admin_analytics_bp = Blueprint('admin_analytics', __name__, url_prefix='/admin/analytics')

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verifica se o usuário é admin. Nota: assumesse que 'is_admin' é um booleano no banco.
        if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
            return jsonify({"error": "Acesso restrito a administradores."}), 403
        return f(*args, **kwargs)
    return decorated_function

@admin_analytics_bp.route('/')
@login_required
@admin_required
def index():
    return render_template('admin/analytics_dashboard.html')

@admin_analytics_bp.route('/data')
@login_required
@admin_required
def get_metrics_data():
    try:
        # 1. Filtros
        periodo = request.args.get('periodo', '30')
        status = request.args.get('status', 'todos')
        user_id_filtro = request.args.get('user_id')
        
        try:
            dias = int(periodo)
        except ValueError:
            dias = 30
            
        data_limite = datetime.now() - timedelta(days=dias)
        
        # 2. Query de Usuários
        user_query = db.session.query(User)
        if status == 'premium':
            user_query = user_query.filter(User.is_premium == True)
        elif status == 'free':
            user_query = user_query.filter(User.is_premium == False)
            
        if user_id_filtro and user_id_filtro.strip():
            user_query = user_query.filter(User.id == int(user_id_filtro))
            
        target_users = user_query.all()
        target_user_ids = [u.id for u in target_users]

        if not target_user_ids:
            return jsonify({
                "summary": {k: 0 for k in ["total_usuarios_filtrados", "total_redacoes", "total_simulados", "total_questoes", "tempo_total_horas", "media_tempo_sessao_minutos"]},
                "detalhes_atividades": {},
                "usuarios": []
            })

        # 3. Métricas de Volume (Corrigido para 'data' em vez de 'data_criacao')
        # Redações
        total_redacoes = 0
        if Redacao:
            # Note: Usando 'data' conforme consta no seu SQL exportado
            total_redacoes = db.session.query(func.count(Redacao.id))\
                .filter(Redacao.user_id.in_(target_user_ids))\
                .filter(Redacao.data >= data_limite).scalar() or 0

        # Simulados
        total_simulados = db.session.query(func.count(Simulado.id))\
            .filter(Simulado.user_id.in_(target_user_ids))\
            .filter(Simulado.data_inicio >= data_limite).scalar() or 0

        # Questões
        total_questoes = db.session.query(func.count(ExercicioRealizado.id))\
            .filter(ExercicioRealizado.user_id.in_(target_user_ids))\
            .filter(ExercicioRealizado.data >= data_limite).scalar() or 0

        # 4. Métricas de Tempo
        tempo_stats = db.session.query(
            TempoEstudo.atividade,
            func.sum(TempoEstudo.duracao_segundos).label('total_segundos'),
            func.count(TempoEstudo.id).label('total_sessoes')
        ).filter(TempoEstudo.user_id.in_(target_user_ids))\
         .filter(TempoEstudo.data >= data_limite)\
         .group_by(TempoEstudo.atividade).all()

        tempo_por_atividade = {}
        tempo_total_geral = 0
        sessoes_totais = 0
        
        for item in tempo_stats:
            atividade = item.atividade or 'Geral'
            segundos = int(item.total_segundos or 0)
            sessoes = item.total_sessoes or 0
            
            tempo_por_atividade[atividade] = {
                "total_minutos": round(segundos / 60, 1),
                "media_sessao_minutos": round((segundos / sessoes) / 60, 1) if sessoes > 0 else 0
            }
            tempo_total_geral += segundos
            sessoes_totais += sessoes

        # 5. Formatação de Saída
        return jsonify({
            "summary": {
                "total_usuarios_filtrados": len(target_user_ids),
                "total_redacoes": total_redacoes,
                "total_simulados": total_simulados,
                "total_questoes": total_questoes,
                "tempo_total_horas": round(tempo_total_geral / 3600, 1),
                "media_tempo_sessao_minutos": round((tempo_total_geral / sessoes_totais) / 60, 1) if sessoes_totais > 0 else 0
            },
            "detalhes_atividades": tempo_por_atividade,
            "usuarios": [
                {
                    "id": u.id,
                    "nome": u.nome,
                    "email": u.email,
                    "status": "Premium" if u.is_premium else "Freemium",
                    "data_cadastro": u.data_criacao.strftime('%d/%m/%Y') if hasattr(u, 'data_criacao') and u.data_criacao else 'N/A'
                } for u in target_users[:20] # Limitado para evitar sobrecarga no JSON
            ]
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500
