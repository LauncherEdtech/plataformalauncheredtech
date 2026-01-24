# app/routes/perfil.py
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from sqlalchemy import func, desc

perfil_bp = Blueprint('perfil', __name__, url_prefix='/perfil')

@perfil_bp.route('/')
@login_required
def index():
    """Página principal do perfil do usuário"""
    try:
        # Dados básicos do perfil
        dados_perfil = obter_dados_perfil_completos(current_user.id)
        
        return render_template('perfil/index.html', **dados_perfil)
        
    except Exception as e:
        print(f"Erro ao carregar perfil: {e}")
        return render_template('perfil/index.html', **dados_perfil_padrao())

@perfil_bp.route('/api/dados')
@login_required
def api_dados():
    """API para obter dados do perfil em JSON"""
    try:
        dados = obter_dados_perfil_completos(current_user.id)
        return jsonify(dados)
    except Exception as e:
        print(f"Erro na API de dados do perfil: {e}")
        return jsonify(dados_perfil_padrao())

def obter_dados_perfil_completos(user_id):
    """Obtém todos os dados necessários para o perfil"""
    try:
        from app.models.user import User
        user = User.query.get(user_id)
        
        # Estatísticas básicas
        dados = {
            # Dados do usuário
            'user': user,
            
            # XP e Diamantes
            'xp_total': getattr(user, 'xp_total', 0) or 0,
            'diamantes': getattr(user, 'diamantes', 0) or 0,
            'total_moedas': getattr(user, 'total_moedas', 0) or 0,
            
            # Estudos
            'aulas_concluidas': obter_aulas_concluidas(user_id),
            'tempo_estudo_total': obter_tempo_estudo_total(user_id),
            'sequencia_dias': obter_sequencia_estudo(user_id),
            
            # Simulados
            'simulados_realizados': obter_simulados_realizados(user_id),
            'ultima_nota_simulado': obter_ultima_nota_simulado(user_id),
            
            # Shop
            'produtos_resgatados': obter_produtos_resgatados(user_id),
            
            # Ranking
            'posicao_ranking': obter_posicao_ranking(user_id),
            
            # Progresso por matéria
            'progresso_materias': obter_progresso_materias(user_id)
        }
        
        return dados
        
    except Exception as e:
        print(f"Erro ao obter dados do perfil: {e}")
        return dados_perfil_padrao()

def obter_aulas_concluidas(user_id):
    """Conta o número de aulas concluídas pelo usuário"""
    try:
        from app.models.estudo import ProgressoAula
        return ProgressoAula.query.filter_by(
            user_id=user_id, 
            concluida=True
        ).count()
    except:
        return 0

def obter_tempo_estudo_total(user_id):
    """Calcula o tempo total de estudo em formato legível"""
    try:
        from app.models.estudo import SessaoEstudo
        total_segundos = db.session.query(
            func.sum(SessaoEstudo.tempo_ativo)
        ).filter_by(user_id=user_id).scalar() or 0
        
        # Converter para horas
        horas = total_segundos // 3600
        if horas > 0:
            return f"{horas}h"
        else:
            minutos = total_segundos // 60
            return f"{minutos}min"
            
    except:
        return "0h"

def obter_sequencia_estudo(user_id):
    """Calcula a sequência atual de dias estudando"""
    try:
        from app.models.estudo import SessaoEstudo
        from datetime import datetime, timedelta
        
        hoje = datetime.now().date()
        sequencia = 0
        data_verificacao = hoje
        
        # Verificar até 365 dias atrás
        while sequencia < 365:
            sessoes_do_dia = SessaoEstudo.query.filter(
                SessaoEstudo.user_id == user_id,
                func.date(SessaoEstudo.inicio) == data_verificacao,
                SessaoEstudo.tempo_ativo >= 300  # Mínimo 5 minutos
            ).first()
            
            if sessoes_do_dia:
                sequencia += 1
                data_verificacao -= timedelta(days=1)
            else:
                break
                
        return sequencia
        
    except:
        return 0

def obter_simulados_realizados(user_id):
    """Conta o número de simulados realizados"""
    try:
        from app.models.simulado import Simulado
        return Simulado.query.filter_by(
            user_id=user_id, 
            status='Concluído'
        ).count()
    except:
        return 0

def obter_ultima_nota_simulado(user_id):
    """Obtém a última nota de simulado"""
    try:
        from app.models.simulado import Simulado
        ultimo = Simulado.query.filter_by(
            user_id=user_id, 
            status='Concluído'
        ).order_by(desc(Simulado.data_realizado)).first()
        
        if ultimo and ultimo.nota_tri:
            return f"{ultimo.nota_tri:.0f}"
        return "N/A"
    except:
        return "N/A"

def obter_produtos_resgatados(user_id):
    """Obtém a lista de produtos resgatados pelo usuário"""
    try:
        from app.models.shop import Resgate, Produto
        resgates = db.session.query(Resgate, Produto).join(
            Produto, Resgate.produto_id == Produto.id
        ).filter(
            Resgate.user_id == user_id,
            Resgate.status == 'concluido'
        ).order_by(desc(Resgate.data_resgate)).limit(5).all()
        
        produtos = []
        for resgate, produto in resgates:
            produtos.append({
                'nome': produto.nome,
                'preco': produto.preco_xp,
                'data_resgate': resgate.data_resgate
            })
            
        return produtos
        
    except:
        return []

def obter_posicao_ranking(user_id):
    """Calcula a posição do usuário no ranking de XP"""
    try:
        from app.models.user import User
        user = User.query.get(user_id)
        user_xp = getattr(user, 'xp_total', 0) or 0
        
        # Contar quantos usuários têm mais XP
        posicao = db.session.query(User).filter(
            User.xp_total > user_xp,
            User.xp_total.isnot(None)
        ).count() + 1
        
        return posicao
        
    except:
        return "N/A"

def obter_progresso_materias(user_id):
    """Obtém o progresso por matéria"""
    try:
        from app.models.estudo import Materia, Modulo, Aula, ProgressoAula
        
        materias = Materia.query.filter_by(ativa=True).all()
        progresso = []
        
        for materia in materias:
            # Total de aulas na matéria
            total_aulas = db.session.query(Aula).join(Modulo).filter(
                Modulo.materia_id == materia.id,
                Aula.ativa == True
            ).count()
            
            # Aulas concluídas pelo usuário
            aulas_concluidas = db.session.query(ProgressoAula).join(Aula).join(Modulo).filter(
                Modulo.materia_id == materia.id,
                ProgressoAula.user_id == user_id,
                ProgressoAula.concluida == True
            ).count()
            
            # Calcular percentual
            percentual = (aulas_concluidas / total_aulas * 100) if total_aulas > 0 else 0
            
            progresso.append({
                'nome': materia.nome,
                'percentual': int(percentual),
                'aulas_concluidas': aulas_concluidas,
                'total_aulas': total_aulas
            })
            
        return progresso
        
    except:
        return []

def dados_perfil_padrao():
    """Dados padrão em caso de erro"""
    return {
        'user': current_user,
        'xp_total': 0,
        'diamantes': 0,
        'total_moedas': 0,
        'aulas_concluidas': 0,
        'tempo_estudo_total': '0h',
        'sequencia_dias': 0,
        'simulados_realizados': 0,
        'ultima_nota_simulado': 'N/A',
        'produtos_resgatados': [],
        'posicao_ranking': 'N/A',
        'progresso_materias': []
    }
