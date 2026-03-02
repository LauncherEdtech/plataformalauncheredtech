# app/routes/questoes.py
"""
Blueprint de Questões Individuais
Fluxo: Explorar → Selecionar Matéria/Tópico → Praticar
"""

from flask import (
    Blueprint, render_template, request, jsonify,
    session, redirect, url_for, current_app
)
from flask_login import login_required, current_user
import uuid
import json
from app.services.questoes_service import (
    listar_provas,
    listar_todas_materias_topicos,
    listar_topicos_por_materia,
    buscar_questoes,
    buscar_questao_por_id,
    registrar_resposta,
    calcular_desempenho_usuario,
    sugerir_proximas_questoes
)

questoes_bp = Blueprint('questoes', __name__, url_prefix='/questoes')

# ─────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────

def _get_provas_selecionadas():
    """Lê provas da sessão ou query string."""
    provas = request.args.getlist('provas')
    if not provas:
        provas = session.get('provas_selecionadas', [])
    return provas or []


# ─────────────────────────────────────────────────
#  ROTAS PRINCIPAIS
# ─────────────────────────────────────────────────

@questoes_bp.route('/')
@login_required
def index():
    """
    Tela de entrada: escolher vestibulares e explorar matérias.
    Layout Netflix com linhas por matéria.
    """
    try:
        provas = _get_provas_selecionadas()
        todas_provas = listar_provas()
        catalogo = listar_todas_materias_topicos(provas if provas else None)

        # Desempenho do usuário para personalização
        desempenho = calcular_desempenho_usuario(current_user.id)

        return render_template(
            'questoes/index.html',
            todas_provas=todas_provas,
            provas_selecionadas=provas,
            catalogo=catalogo,
            desempenho=desempenho
        )
    except Exception as e:
        current_app.logger.error(f"Erro em questoes.index: {e}", exc_info=True)
        return render_template('questoes/index.html',
                               todas_provas=[], provas_selecionadas=[],
                               catalogo={}, desempenho={})


@questoes_bp.route('/explorar')
@login_required
def explorar():
    """
    API endpoint para atualizar catálogo ao mudar filtro de provas.
    Retorna JSON com estrutura de matérias/tópicos.
    """
    provas = request.args.getlist('provas')
    if provas:
        session['provas_selecionadas'] = provas

    try:
        catalogo = listar_todas_materias_topicos(provas if provas else None)
        return jsonify({'success': True, 'catalogo': catalogo})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@questoes_bp.route('/subtemas')
@login_required
def subtemas():
    """
    Retorna subtópicos de uma matéria/tópico para o modal.
    """
    materia = request.args.get('materia')
    topico = request.args.get('topico')
    provas = request.args.getlist('provas')

    if not materia or not topico:
        return jsonify({'success': False, 'error': 'Parâmetros inválidos'}), 400

    try:
        topicos_dados = listar_topicos_por_materia(materia, provas if provas else None)
        topico_info = next((t for t in topicos_dados if t['topico'] == topico), None)
        return jsonify({'success': True, 'subtopicos': topico_info['subtopicos'] if topico_info else []})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@questoes_bp.route('/praticar')
@login_required
def praticar():
    """
    Tela de prática de questões.
    Carrega sessão de questões baseada nos filtros.
    """
    materia = request.args.get('materia', '')
    topico = request.args.get('topico', '')
    subtopico = request.args.get('subtopico', '')
    provas = request.args.getlist('provas')
    quantidade = request.args.get('quantidade', 20, type=int)

    if not materia:
        return redirect(url_for('questoes.index'))

    # Criar sessão de prática
    sessao_id = str(uuid.uuid4())[:8]

    # Pré-carregar questões
    try:
        questoes = buscar_questoes(
            materia=materia or None,
            topico=topico or None,
            subtopico=subtopico or None,
            provas=provas if provas else None,
            quantidade=min(quantidade, 50)
        )
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar questões: {e}")
        questoes = []

    if not questoes:
        return redirect(url_for('questoes.index'))

    # Serializar IDs para uso no front (evita nova query)
    ids_questoes = [q['id'] for q in questoes]

    return render_template(
        'questoes/praticar.html',
        materia=materia,
        topico=topico,
        subtopico=subtopico,
        provas=provas,
        sessao_id=sessao_id,
        total_questoes=len(questoes),
        ids_questoes_json=json.dumps(ids_questoes),
        primeira_questao=questoes[0] if questoes else None,
        questoes=questoes  # todas para o JS
    )


# ─────────────────────────────────────────────────
#  API ENDPOINTS (AJAX)
# ─────────────────────────────────────────────────

@questoes_bp.route('/api/questao/<int:questao_id>')
@login_required
def api_questao(questao_id):
    """Retorna dados de uma questão pelo ID (sem resposta correta)."""
    q = buscar_questao_por_id(questao_id)
    if not q:
        return jsonify({'success': False, 'error': 'Questão não encontrada'}), 404

    # Remover dados sensíveis antes de enviar ao cliente
    q_seguro = {k: v for k, v in q.items()
                if k not in ('resposta_correta', 'explicacao', 'explicacao_distratores', 'dica', 'pre_requisitos')}
    return jsonify({'success': True, 'questao': q_seguro})


@questoes_bp.route('/api/dica/<int:questao_id>')
@login_required
def api_dica(questao_id):
    """Retorna a dica de uma questão (chamada ao clicar no botão Dica)."""
    q = buscar_questao_por_id(questao_id)
    if not q:
        return jsonify({'success': False}), 404
    return jsonify({'success': True, 'dica': q.get('dica') or 'Dica não disponível para esta questão.'})


@questoes_bp.route('/api/pre-requisitos/<int:questao_id>')
@login_required
def api_pre_requisitos(questao_id):
    """Retorna pré-requisitos de uma questão."""
    q = buscar_questao_por_id(questao_id)
    if not q:
        return jsonify({'success': False}), 404
    return jsonify({
        'success': True,
        'pre_requisitos': q.get('pre_requisitos') or 'Nenhum pré-requisito específico.'
    })


@questoes_bp.route('/api/responder', methods=['POST'])
@login_required
def api_responder():
    """
    Registra resposta do usuário e retorna feedback completo.
    Dados: questao_id, resposta, tempo, sessao_id, usou_dica, usou_pre_requisitos
    """
    if not request.is_json:
        return jsonify({'success': False}), 400

    data = request.get_json()
    questao_id = data.get('questao_id')
    resposta = data.get('resposta', '').upper()
    tempo = data.get('tempo')  # segundos
    sessao_id = data.get('sessao_id')
    usou_dica = data.get('usou_dica', False)
    usou_pre_requisitos = data.get('usou_pre_requisitos', False)

    if not questao_id or resposta not in ['A', 'B', 'C', 'D', 'E']:
        return jsonify({'success': False, 'error': 'Dados inválidos'}), 400

    q = buscar_questao_por_id(questao_id)
    if not q:
        return jsonify({'success': False, 'error': 'Questão não encontrada'}), 404

    correta = (resposta == q['resposta_correta'])

    # Registrar desempenho
    registrar_resposta(
        user_id=current_user.id,
        questao_id=questao_id,
        resposta_usuario=resposta,
        correta=correta,
        tempo_resposta=tempo,
        materia=q.get('materia'),
        topico=q.get('topico'),
        subtopico=q.get('subtopico'),
        prova=q.get('prova') or 'ENEM',
        dificuldade=q.get('dificuldade'),
        usou_dica=usou_dica,
        usou_pre_requisitos=usou_pre_requisitos,
        sessao_id=sessao_id
    )

    return jsonify({
        'success': True,
        'correta': correta,
        'resposta_correta': q['resposta_correta'],
        'explicacao': q.get('explicacao') or '',
        'explicacao_distratores': q.get('explicacao_distratores') or '',
        'materia': q.get('materia'),
        'topico': q.get('topico'),
        'subtopico': q.get('subtopico'),
        'fonte': q.get('fonte') or '',
        'ano': q.get('ano') or '',
        'prova': q.get('prova') or 'ENEM',
    })


@questoes_bp.route('/api/desempenho')
@login_required
def api_desempenho():
    """Retorna análise de desempenho do usuário atual."""
    desempenho = calcular_desempenho_usuario(current_user.id)
    return jsonify({'success': True, 'desempenho': desempenho})


@questoes_bp.route('/api/sugestoes')
@login_required
def api_sugestoes():
    """Retorna questões sugeridas baseadas no desempenho."""
    sugestoes = sugerir_proximas_questoes(current_user.id)
    return jsonify({'success': True, 'sugestoes': sugestoes})
