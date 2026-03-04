# =============================================================================
# VOCACIONAL.PY v2 — Blueprint Flask do Teste Vocacional
# Novidades: carreiras_favoritas, descrições nas carreiras salvas, bloco situacional
# =============================================================================

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from flask_login import login_required, current_user
from datetime import datetime
from app import db
import json
import logging

logger = logging.getLogger(__name__)

from app.models.vocacional_data import (
    QUESTOES_RIASEC,
    QUESTOES_SITUACIONAIS,       # NOVO v2
    QUESTOES_PERSONALIDADE,
    QUESTOES_VALORES,
    QUESTOES_HABILIDADES,
    QUESTOES_CONTEXTO,
    PERFIS_RIASEC,
    gerar_resultado_completo,
    CARREIRAS
)

vocacional_bp = Blueprint('vocacional', __name__, url_prefix='/vocacional')


# ─────────────────────────────────────────────────────────────────────────────
# MODELO DE BANCO DE DADOS
# ─────────────────────────────────────────────────────────────────────────────

class VocacionalResultado(db.Model):
    """Armazena resultados do teste vocacional por usuário"""
    __tablename__ = 'vocacional_resultado'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)

    perfil_primario = db.Column(db.String(2), nullable=False)
    perfil_secundario = db.Column(db.String(2), nullable=False)
    combo_label = db.Column(db.String(80))                      # Ex: "O Analista de Sistemas"

    scores_riasec = db.Column(db.JSON, nullable=False)
    top_carreiras = db.Column(db.JSON, nullable=False)

    # NOVO v2: as 3 carreiras que o usuário escolheu como favoritas, em ordem
    # Formato: [{"posicao": 1, "id": "medicina", "nome": "Medicina", "emoji": "🩺"},
    #           {"posicao": 2, ...}, {"posicao": 3, ...}]
    carreiras_favoritas = db.Column(db.JSON, nullable=True)

    valores_usuario = db.Column(db.JSON)
    personalidade = db.Column(db.JSON)
    contexto = db.Column(db.JSON)
    radar_data = db.Column(db.JSON)
    respostas_brutas = db.Column(db.JSON)

    versao_teste = db.Column(db.String(10), default="2.0")      # Atualizado para v2
    data_realizado = db.Column(db.DateTime, default=datetime.utcnow)
    tempo_segundos = db.Column(db.Integer, nullable=True)

    # Quando o usuário salvou as favoritas (pode ser depois do teste)
    data_favoritas = db.Column(db.DateTime, nullable=True)

    usuario = db.relationship('User', backref=db.backref('vocacional_resultados', lazy='dynamic'))

    def __repr__(self):
        return f'<VocacionalResultado user={self.user_id} perfil={self.perfil_primario}{self.perfil_secundario}>'


# ─────────────────────────────────────────────────────────────────────────────
# ROTAS
# ─────────────────────────────────────────────────────────────────────────────

@vocacional_bp.route('/')
@login_required
def index():
    """Página inicial do teste vocacional"""
    ultimo_resultado = VocacionalResultado.query.filter_by(
        user_id=current_user.id
    ).order_by(VocacionalResultado.data_realizado.desc()).first()

    questoes_blocos = {
        "riasec":       QUESTOES_RIASEC,
        "situacional":  QUESTOES_SITUACIONAIS,   # NOVO v2
        "habilidades":  QUESTOES_HABILIDADES,
        "personalidade": QUESTOES_PERSONALIDADE,
        "valores":      QUESTOES_VALORES,
        "contexto":     QUESTOES_CONTEXTO,
    }

    total_questoes = sum(len(v) for v in questoes_blocos.values())

    return render_template(
        'vocacional/vocacional_teste.html',
        questoes_blocos=questoes_blocos,
        total_questoes=total_questoes,
        ultimo_resultado=ultimo_resultado,
        perfis_riasec=PERFIS_RIASEC,
    )


@vocacional_bp.route('/processar', methods=['POST'])
@login_required
def processar():
    """Processa as respostas e salva o resultado"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"sucesso": False, "erro": "Nenhum dado recebido"}), 400

        respostas = dados.get("respostas", {})
        tempo_segundos = dados.get("tempo_segundos", 0)

        total_questoes = (
            len(QUESTOES_RIASEC) + len(QUESTOES_SITUACIONAIS) +
            len(QUESTOES_PERSONALIDADE) + len(QUESTOES_VALORES) +
            len(QUESTOES_HABILIDADES) + len(QUESTOES_CONTEXTO)
        )

        if len(respostas) < (total_questoes * 0.45):
            return jsonify({
                "sucesso": False,
                "erro": f"Responda pelo menos {int(total_questoes * 0.45)} questões para obter um resultado confiável."
            }), 400

        resultado = gerar_resultado_completo(respostas)

        # Salva campos completos das carreiras (incluindo descricao para o resultado)
        top_carreiras_salvar = []
        for item in resultado["top_carreiras"]:
            c = item["carreira"]
            top_carreiras_salvar.append({
                "id": c["id"],
                "nome": c["nome"],
                "area": c["area"],
                "emoji": c["emoji"],
                "descricao": c.get("descricao", ""),           # NOVO v2
                "descricao_dia_a_dia": c.get("descricao_dia_a_dia", ""),  # NOVO v2
                "compatibilidade": item["compatibilidade"],
                "compatibilidade_label": item["compatibilidade_label"],
                "salario_min": c["salario_min"],
                "salario_max": c["salario_max"],
                "duracao_label": c["duracao_label"],
                "duracao_anos": c.get("duracao_anos", 4),
                "perspectiva_mercado": c["perspectiva_mercado"],
                "dificuldade_enem": c.get("dificuldade_enem", ""),
                "concurso_opcao": c.get("concurso_opcao", False),
                "remoto_opcao": c.get("remoto_opcao", False),
                "tags": c.get("tags", []),
            })

        novo_resultado = VocacionalResultado(
            user_id=current_user.id,
            perfil_primario=resultado["perfil_primario"],
            perfil_secundario=resultado["perfil_secundario"],
            combo_label=resultado.get("combo_label", ""),
            scores_riasec=resultado["scores_riasec"],
            top_carreiras=top_carreiras_salvar,
            valores_usuario=resultado["valores"],
            personalidade=resultado["personalidade"],
            contexto=respostas,
            radar_data=resultado["radar_data"],
            respostas_brutas=respostas,
            tempo_segundos=tempo_segundos,
        )

        db.session.add(novo_resultado)
        db.session.commit()

        logger.info(
            f"Teste vocacional v2: user={current_user.id} "
            f"perfil={resultado['perfil_primario']}{resultado['perfil_secundario']} "
            f"combo='{resultado.get('combo_label','')}'")

        return jsonify({
            "sucesso": True,
            "resultado_id": novo_resultado.id,
            "redirect": url_for('vocacional.resultado', resultado_id=novo_resultado.id)
        })

    except Exception as e:
        logger.error(f"Erro ao processar teste vocacional: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({"sucesso": False, "erro": "Erro interno. Tente novamente."}), 500


@vocacional_bp.route('/resultado/<int:resultado_id>')
@login_required
def resultado(resultado_id):
    """Exibe o resultado completo do teste"""
    resultado_db = VocacionalResultado.query.get_or_404(resultado_id)

    if resultado_db.user_id != current_user.id and not current_user.is_admin:
        return redirect(url_for('vocacional.index'))

    # Carreiras completas enriquecidas com dados do vocacional_data
    carreiras_map = {c["id"]: c for c in CARREIRAS}
    top_carreiras_completas = []
    for item in resultado_db.top_carreiras:
        carreira_id = item.get("id")
        dados_completos = carreiras_map.get(carreira_id, {})
        top_carreiras_completas.append({
            **item,
            "detalhes": dados_completos  # dados_completos pode ser {} se carreira foi removida
        })

    perfil_primario_dados = PERFIS_RIASEC.get(resultado_db.perfil_primario, {})
    perfil_secundario_dados = PERFIS_RIASEC.get(resultado_db.perfil_secundario, {})
    scores = resultado_db.scores_riasec or {}
    ranking_riasec = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    return render_template(
        'vocacional/vocacional_resultado.html',
        resultado=resultado_db,
        top_carreiras=top_carreiras_completas,
        perfil_primario_dados=perfil_primario_dados,
        perfil_secundario_dados=perfil_secundario_dados,
        ranking_riasec=ranking_riasec,
        perfis_riasec=PERFIS_RIASEC,
        radar_data=resultado_db.radar_data or {},
        carreiras_favoritas=resultado_db.carreiras_favoritas or [],
    )


# ─────────────────────────────────────────────────────────────────────────────
# NOVA ROTA v2: Salvar Carreiras Favoritas
# Chamada pelo JS do resultado.html quando o usuário confirma as 3 escolhas
# ─────────────────────────────────────────────────────────────────────────────

@vocacional_bp.route('/api/carreiras-favoritas', methods=['POST'])
@login_required
def salvar_carreiras_favoritas():
    """
    Salva as 3 carreiras favoritas do usuário em ordem de preferência.
    Body: { "resultado_id": 123, "favoritas": [
              {"posicao": 1, "id": "medicina", "nome": "Medicina", "emoji": "🩺"},
              {"posicao": 2, "id": "psicologia", "nome": "Psicologia", "emoji": "🧠"},
              {"posicao": 3, "id": "biomedicina", "nome": "Biomedicina", "emoji": "🔬"}
           ]}
    """
    try:
        dados = request.get_json()
        resultado_id = dados.get("resultado_id")
        favoritas = dados.get("favoritas", [])

        # Validações
        if not resultado_id or not favoritas:
            return jsonify({"sucesso": False, "erro": "Dados incompletos"}), 400

        if len(favoritas) != 3:
            return jsonify({"sucesso": False, "erro": "Selecione exatamente 3 carreiras"}), 400

        resultado_db = VocacionalResultado.query.get(resultado_id)
        if not resultado_db:
            return jsonify({"sucesso": False, "erro": "Resultado não encontrado"}), 404

        if resultado_db.user_id != current_user.id:
            return jsonify({"sucesso": False, "erro": "Acesso negado"}), 403

        # Valida e limpa as favoritas
        ids_validos = {c["id"] for c in CARREIRAS}
        favoritas_validas = []
        for fav in favoritas:
            if fav.get("id") in ids_validos and fav.get("posicao") in [1, 2, 3]:
                favoritas_validas.append({
                    "posicao": int(fav["posicao"]),
                    "id": fav["id"],
                    "nome": fav.get("nome", ""),
                    "emoji": fav.get("emoji", ""),
                    "area": fav.get("area", ""),
                })

        if len(favoritas_validas) != 3:
            return jsonify({"sucesso": False, "erro": "Carreiras inválidas"}), 400

        # Ordena por posição garantida
        favoritas_validas.sort(key=lambda x: x["posicao"])

        resultado_db.carreiras_favoritas = favoritas_validas
        resultado_db.data_favoritas = datetime.utcnow()
        db.session.commit()

        logger.info(
            f"Carreiras favoritas salvas: user={current_user.id} "
            f"resultado={resultado_id} "
            f"favoritas={[f['id'] for f in favoritas_validas]}"
        )

        return jsonify({
            "sucesso": True,
            "mensagem": "Preferências salvas com sucesso!"
        })

    except Exception as e:
        logger.error(f"Erro ao salvar carreiras favoritas: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({"sucesso": False, "erro": "Erro interno"}), 500


# ─────────────────────────────────────────────────────────────────────────────
# ROTA: Histórico
# ─────────────────────────────────────────────────────────────────────────────

@vocacional_bp.route('/historico')
@login_required
def historico():
    resultados = VocacionalResultado.query.filter_by(
        user_id=current_user.id
    ).order_by(VocacionalResultado.data_realizado.desc()).all()

    return render_template(
        'vocacional/vocacional_historico.html',
        resultados=resultados,
        perfis_riasec=PERFIS_RIASEC,
    )


# ─────────────────────────────────────────────────────────────────────────────
# ROTAS: Progresso parcial (session)
# ─────────────────────────────────────────────────────────────────────────────

@vocacional_bp.route('/api/progresso', methods=['POST'])
@login_required
def salvar_progresso():
    try:
        dados = request.get_json()
        session['vocacional_progresso'] = dados.get('respostas', {})
        session['vocacional_tempo_inicio'] = dados.get('tempo_inicio', 0)
        return jsonify({"sucesso": True})
    except Exception:
        return jsonify({"sucesso": False}), 500


@vocacional_bp.route('/api/progresso', methods=['GET'])
@login_required
def carregar_progresso():
    progresso = session.get('vocacional_progresso', {})
    return jsonify({"respostas": progresso})
