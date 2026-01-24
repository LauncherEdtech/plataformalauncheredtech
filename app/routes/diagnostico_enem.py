from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import current_user
from functools import wraps
from datetime import datetime
from app import db
from sqlalchemy import text
import json
import random
import re

diagnostico_bp = Blueprint('diagnostico', __name__, url_prefix='/diagnostico-enem')

# ============================================
# DECORATOR PARA ROTAS ADMIN
# ============================================

def admin_required(f):
    """
    Decorator para proteger rotas que exigem permissão de admin
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar se usuário está autenticado
        if not current_user.is_authenticated:
            flash('Você precisa fazer login para acessar esta página.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Verificar se usuário é admin
        if not getattr(current_user, 'is_admin', False):
            flash('Acesso negado. Você não tem permissão de administrador.', 'danger')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function

# ============================================
# FUNÇÕES AUXILIARES
# ============================================

def get_questoes_aleatorias():
    """
    Seleciona 10 questões aleatórias seguindo a distribuição:
    - 3 questões fáceis (de 6 disponíveis)
    - 2 questões médias (de 4 disponíveis)
    - 5 questões difíceis (de 10 disponíveis)
    """
    # Buscar questões por dificuldade
    faceis = db.session.execute(text("""
        SELECT * FROM questoes_diagnostico 
        WHERE dificuldade = 'facil' AND ativa = TRUE
        ORDER BY RANDOM() LIMIT 3
    """)).mappings().all()
    
    medias = db.session.execute(text("""
        SELECT * FROM questoes_diagnostico 
        WHERE dificuldade = 'media' AND ativa = TRUE
        ORDER BY RANDOM() LIMIT 2
    """)).mappings().all()
    
    dificeis = db.session.execute(text("""
        SELECT * FROM questoes_diagnostico 
        WHERE dificuldade = 'dificil' AND ativa = TRUE
        ORDER BY RANDOM() LIMIT 5
    """)).mappings().all()
    
    # Combinar e embaralhar todas as questões
    questoes = list(faceis) + list(medias) + list(dificeis)
    random.shuffle(questoes)
    
    return questoes

# ============================================
# ROTAS PÚBLICAS
# ============================================

@diagnostico_bp.route('/')
def index():
    """Tela 1: Formulário inicial com nome, curso e telefone"""
    return render_template('diagnostico/inicio.html')

@diagnostico_bp.route('/questoes', methods=['POST'])
def questoes():
    """Tela 2: Página com as 10 questões e cronômetro de 20 minutos"""
    # Pegar dados do formulário
    nome = request.form.get('nome', '').strip()
    curso = request.form.get('curso', '').strip()
    telefone = request.form.get('telefone', '').strip()
    
    # Validação básica
    if not nome or not curso or not telefone:
        return render_template('diagnostico/inicio.html', 
                             erro="Por favor, preencha todos os campos")
    
    # ✅ Validar se curso tem números
    if re.search(r'\d', curso):
        return render_template('diagnostico/inicio.html', 
                             erro="O campo 'Qual curso quer fazer?' não pode conter números")
    
    # Armazenar na sessão
    session['diagnostico_nome'] = nome
    session['diagnostico_curso'] = curso
    session['diagnostico_telefone'] = telefone
    session['diagnostico_inicio'] = datetime.now().isoformat()
    
    # Buscar questões aleatórias
    questoes = get_questoes_aleatorias()
    
    # Guardar IDs das questões na sessão
    session['diagnostico_questoes_ids'] = [q['id'] for q in questoes]
    
    return render_template('diagnostico/questoes.html', 
                         questoes=questoes,
                         nome=nome,
                         curso=curso)

@diagnostico_bp.route('/finalizar', methods=['POST'])
def finalizar():
    """Processa as respostas e salva no banco de dados"""
    try:
        # Pegar dados da sessão
        nome = session.get('diagnostico_nome')
        curso = session.get('diagnostico_curso')
        telefone = session.get('diagnostico_telefone')
        inicio = session.get('diagnostico_inicio')
        questoes_ids = session.get('diagnostico_questoes_ids', [])
        
        if not nome or not curso or not telefone:
            return jsonify({'erro': 'Sessão expirada'}), 400
        
        # Validar respostas
        respostas = {}
        for questao_id in questoes_ids:
            resposta = request.form.get(f'questao_{questao_id}')
            if resposta:
                respostas[str(questao_id)] = resposta
        
        total_questoes = len(questoes_ids)
        total_respondidas = len(respostas)
        
        # Calcular tempo realizado
        tempo_realizado = 0
        tempo_limite_excedido = False
        
        if inicio:
            inicio_dt = datetime.fromisoformat(inicio)
            tempo_realizado = int((datetime.now() - inicio_dt).total_seconds())
            
            # ✅ Verificar se excedeu 25 minutos (20 + 5 de emergência)
            if tempo_realizado > (25 * 60):
                tempo_limite_excedido = True
        
        # ✅ Validação: Exigir todas as respostas, EXCETO se tempo esgotou
        if not tempo_limite_excedido and total_respondidas < total_questoes:
            return jsonify({
                'erro': f'Você precisa responder todas as {total_questoes} questões. '
                       f'Faltam {total_questoes - total_respondidas} questão(ões).'
            }), 400
        
        # Pegar IP e User Agent
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        
        # Salvar no banco
        result = db.session.execute(text("""
            INSERT INTO diagnostico_enem 
            (nome, curso_desejado, telefone, tempo_realizado, respostas, 
             questoes_utilizadas, ip_address, user_agent)
            VALUES (:nome, :curso, :telefone, :tempo, :respostas, 
                    :questoes, :ip, :user_agent)
            RETURNING id
        """), {
            'nome': nome,
            'curso': curso,
            'telefone': telefone,
            'tempo': tempo_realizado,
            'respostas': json.dumps(respostas),
            'questoes': json.dumps(questoes_ids),
            'ip': ip_address,
            'user_agent': user_agent
        })
        
        diagnostico_id = result.scalar()
        db.session.commit()
        
        # Limpar sessão
        session.pop('diagnostico_nome', None)
        session.pop('diagnostico_curso', None)
        session.pop('diagnostico_telefone', None)
        session.pop('diagnostico_inicio', None)
        session.pop('diagnostico_questoes_ids', None)
        
        return jsonify({
            'sucesso': True,
            'redirect': f'/diagnostico-enem/resultado/{diagnostico_id}'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao finalizar diagnóstico: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'erro': 'Erro ao processar respostas'}), 500
@diagnostico_bp.route('/resultado/<int:diagnostico_id>')
def resultado(diagnostico_id):
    """Tela 3: Página de resultado genérico com nome e curso"""
    try:
        resultado = db.session.execute(text("""
            SELECT nome, curso_desejado, data_realizacao
            FROM diagnostico_enem
            WHERE id = :id
        """), {'id': diagnostico_id}).mappings().first()
        
        if not resultado:
            return "Diagnóstico não encontrado", 404
        
        return render_template('diagnostico/resultado.html',
                             diagnostico_id=diagnostico_id,
                             nome=resultado['nome'],
                             curso=resultado['curso_desejado'],
                             data_realizacao=resultado['data_realizacao'])
        
    except Exception as e:
        print(f"Erro ao buscar resultado: {e}")
        import traceback
        traceback.print_exc()
        return "Erro ao carregar resultado", 500

@diagnostico_bp.route('/registrar-clique/<int:diagnostico_id>', methods=['POST'])
def registrar_clique(diagnostico_id):
    """Registra quando o usuário clica no botão CTA"""
    try:
        # Verificar se já existe
        resultado = db.session.execute(text("""
            SELECT clicou_cta, total_cliques 
            FROM diagnostico_enem 
            WHERE id = :id
        """), {'id': diagnostico_id}).mappings().first()
        
        if not resultado:
            return jsonify({'erro': 'Diagnóstico não encontrado'}), 404
        
        # Atualizar cliques
        if resultado['clicou_cta']:
            # Já clicou antes, apenas incrementa
            db.session.execute(text("""
                UPDATE diagnostico_enem 
                SET total_cliques = total_cliques + 1,
                    data_ultimo_clique = NOW()
                WHERE id = :id
            """), {'id': diagnostico_id})
        else:
            # Primeiro clique
            db.session.execute(text("""
                UPDATE diagnostico_enem 
                SET clicou_cta = TRUE,
                    total_cliques = 1,
                    data_primeiro_clique = NOW(),
                    data_ultimo_clique = NOW()
                WHERE id = :id
            """), {'id': diagnostico_id})
        
        db.session.commit()
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Clique registrado!'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao registrar clique: {e}")
        return jsonify({'erro': 'Erro ao registrar clique'}), 500

# ============================================
# ROTAS ADMINISTRATIVAS (Protegidas)
# ============================================

@diagnostico_bp.route('/admin/estatisticas')
@admin_required
def admin_estatisticas():
    """Dashboard com estatísticas dos diagnósticos realizados"""
    try:
        # Total de diagnósticos
        total_leads = db.session.execute(
            text("SELECT COUNT(*) FROM diagnostico_enem")
        ).scalar()
        
        # Leads que clicaram no CTA
        leads_clicaram = db.session.execute(
            text("SELECT COUNT(*) FROM diagnostico_enem WHERE clicou_cta = TRUE")
        ).scalar()
        
        # Taxa de clique
        taxa_clique = round((leads_clicaram / total_leads * 100), 1) if total_leads > 0 else 0
        
        # Diagnósticos por dia (últimos 7 dias)
        por_dia = db.session.execute(text("""
            SELECT
                DATE(data_realizacao AT TIME ZONE 'America/Sao_Paulo') AS data,
                COUNT(*) AS total
            FROM diagnostico_enem
            WHERE data_realizacao >= (NOW() AT TIME ZONE 'America/Sao_Paulo') - INTERVAL '7 days'
            GROUP BY DATE(data_realizacao AT TIME ZONE 'America/Sao_Paulo')
            ORDER BY data ASC
        """)).mappings().all()        
        labels_dias = [str(d['data']) for d in por_dia]
        valores_dias = [d['total'] for d in por_dia]
        
        # Cursos mais desejados com taxa de clique
        cursos_populares = db.session.execute(text("""
            SELECT 
                curso_desejado,
                COUNT(*) as total,
                SUM(CASE WHEN clicou_cta THEN 1 ELSE 0 END) as clicaram
            FROM diagnostico_enem
            GROUP BY curso_desejado
            ORDER BY total DESC
            LIMIT 10
        """)).mappings().all()
        
        # Tempo médio de realização
        tempo_medio = db.session.execute(text("""
            SELECT AVG(tempo_realizado) as tempo_medio
            FROM diagnostico_enem
            WHERE tempo_realizado IS NOT NULL
        """)).scalar()
        
        if tempo_medio:
            tempo_medio = int(tempo_medio / 60)
        
        return render_template('diagnostico/admin_estatisticas.html',
                             total_leads=total_leads,
                             leads_clicaram=leads_clicaram,
                             taxa_clique=taxa_clique,
                             labels_dias=labels_dias,
                             valores_dias=valores_dias,
                             cursos_populares=cursos_populares,
                             tempo_medio=tempo_medio)
        
    except Exception as e:
        print(f"Erro ao buscar estatísticas: {e}")
        import traceback
        traceback.print_exc()
        return "Erro ao carregar estatísticas", 500



@diagnostico_bp.route('/admin/leads')
@admin_required
def admin_leads():
    """Lista todos os leads capturados"""
    try:
        leads = db.session.execute(
            text("""
                SELECT 
                    id,
                    nome,
                    curso_desejado,
                    telefone,
                    tempo_realizado,
                    clicou_cta,
                    total_cliques,

                    to_char(
                        (data_realizacao AT TIME ZONE 'UTC') AT TIME ZONE 'America/Sao_Paulo',
                        'DD/MM/YYYY HH24:MI'
                    ) AS data_realizacao_br,

                    to_char(
                        (data_ultimo_clique AT TIME ZONE 'UTC') AT TIME ZONE 'America/Sao_Paulo',
                        'DD/MM/YYYY HH24:MI'
                    ) AS data_ultimo_clique_br,

                    -- versões ISO para ordenação correta no front
                    to_char(
                        (data_realizacao AT TIME ZONE 'UTC') AT TIME ZONE 'America/Sao_Paulo',
                        'YYYY-MM-DD HH24:MI:SS'
                    ) AS data_realizacao_br_sort,

                    to_char(
                        (data_ultimo_clique AT TIME ZONE 'UTC') AT TIME ZONE 'America/Sao_Paulo',
                        'YYYY-MM-DD HH24:MI:SS'
                    ) AS data_ultimo_clique_br_sort

                FROM diagnostico_enem
                ORDER BY data_realizacao DESC NULLS LAST
                LIMIT 100
            """)
        ).mappings().all()

        return render_template('diagnostico/admin_leads.html', leads=leads)

    except Exception as e:
        print(f"Erro ao buscar leads: {e}")
        import traceback
        traceback.print_exc()
        return "Erro ao carregar leads", 500






        
        return render_template('diagnostico/admin_leads.html', leads=leads)
        
    except Exception as e:
        print(f"Erro ao buscar leads: {e}")
        import traceback
        traceback.print_exc()
        return "Erro ao carregar leads", 500
