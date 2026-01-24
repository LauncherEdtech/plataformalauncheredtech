# app/routes/mapeamento.py
import json
import secrets
from datetime import datetime
from functools import wraps

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, current_app
from flask_login import current_user
from sqlalchemy import text

from app import db

mapeamento_bp = Blueprint("mapeamento", __name__, url_prefix="/mapeamento")

VSL_URL = "https://plataformalauncheredu.com.br/"  # troque se quiser


# =========================
# ADMIN REQUIRED (padrão do seu projeto)
# =========================
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Você precisa fazer login para acessar esta página.", "warning")
            return redirect(url_for("auth.login"))

        if not getattr(current_user, "is_admin", False):
            flash("Acesso negado.", "danger")
            return redirect(url_for("main.index"))

        return f(*args, **kwargs)
    return decorated


# =========================
# PERFIL
# =========================
def classificar_perfil(respostas: dict) -> int:
    """
    Regras:
    - Se não sabe o que estudar (q4 = nao_sei) => Perfil 1
    - Se sabe, mas não corrige erro (q5 != analiso_corrijo) => Perfil 2
    - Se sabe e corrige (q5 = analiso_corrijo) => Perfil 3
    """
    q4 = respostas.get("q4")  # nao_sei | tenho_nocao | sei_claramente
    q5 = respostas.get("q5")  # sigo_sem_analisar | olho_sem_aprofundar | analiso_corrijo

    if q4 == "nao_sei":
        return 1

    if q4 in ("tenho_nocao", "sei_claramente") and q5 in ("sigo_sem_analisar", "olho_sem_aprofundar"):
        return 2

    if q4 in ("tenho_nocao", "sei_claramente") and q5 == "analiso_corrijo":
        return 3

    return 1


def get_anon_id() -> str:
    """
    ID anônimo persistente por sessão (não é dado pessoal).
    """
    anon_id = session.get("map_anon_id")
    if not anon_id:
        anon_id = secrets.token_hex(16)  # 32 chars
        session["map_anon_id"] = anon_id
    return anon_id


def get_ip_address() -> str:
    xff = request.headers.get("X-Forwarded-For", "")
    return xff.split(",")[0].strip() if xff else (request.remote_addr or "")


# =========================
# PÁGINA PÚBLICA
# =========================
@mapeamento_bp.route("/", methods=["GET"])
def index():
    # início (UTC) para calcular duração
    session["mapeamento_inicio_utc"] = datetime.utcnow().isoformat()

    # UTMs (sem PII)
    session["map_utm_source"] = request.args.get("utm_source")
    session["map_utm_medium"] = request.args.get("utm_medium")
    session["map_utm_campaign"] = request.args.get("utm_campaign")
    session["map_utm_content"] = request.args.get("utm_content")
    session["map_utm_term"] = request.args.get("utm_term")

    # referer
    session["map_referer"] = request.headers.get("Referer")

    # anon id
    get_anon_id()

    return render_template("mapeamento/index.html", vsl_url=VSL_URL)


# =========================
# ENVIAR (SALVAR RESPOSTAS)
# =========================
@mapeamento_bp.route("/enviar", methods=["POST"])
def enviar():
    if not request.is_json:
        return jsonify({"success": False, "error": "Request must be JSON"}), 400

    payload = request.get_json(silent=True) or {}
    respostas = payload.get("respostas", {})

    if not isinstance(respostas, dict) or not respostas:
        return jsonify({"success": False, "error": "Respostas inválidas"}), 400

    # ✅ transforma em JSON string para salvar no JSONB
    respostas_json = json.dumps(respostas, ensure_ascii=False)

    perfil = classificar_perfil(respostas)

    # tempo em segundos
    tempo_realizado = None
    inicio = session.get("mapeamento_inicio_utc")
    if inicio:
        try:
            inicio_dt = datetime.fromisoformat(inicio)
            tempo_realizado = int((datetime.utcnow() - inicio_dt).total_seconds())
            tempo_realizado = max(0, tempo_realizado)
        except Exception:
            tempo_realizado = None

    # UTMs + referer
    utm_source = session.get("map_utm_source")
    utm_medium = session.get("map_utm_medium")
    utm_campaign = session.get("map_utm_campaign")
    utm_content = session.get("map_utm_content")
    utm_term = session.get("map_utm_term")
    referer = session.get("map_referer")

    # anon id + ip/ua
    anon_id = get_anon_id()
    ip_address = get_ip_address()
    user_agent = request.headers.get("User-Agent", "")

    try:
        result = db.session.execute(text("""
            INSERT INTO mapeamento_direcionamento
                (perfil, tempo_realizado, respostas, anon_id,
                 utm_source, utm_medium, utm_campaign, utm_content, utm_term, referer,
                 ip_address, user_agent, origem_funil)
            VALUES
                (:perfil, :tempo, CAST(:respostas AS jsonb), :anon_id,
                 :utm_source, :utm_medium, :utm_campaign, :utm_content, :utm_term, :referer,
                 :ip, :ua, 'mapa-direcionamento')
            RETURNING id
        """), {
            "perfil": perfil,
            "tempo": tempo_realizado,
            "respostas": respostas_json,
            "anon_id": anon_id,
            "utm_source": utm_source,
            "utm_medium": utm_medium,
            "utm_campaign": utm_campaign,
            "utm_content": utm_content,
            "utm_term": utm_term,
            "referer": referer,
            "ip": ip_address,
            "ua": user_agent
        })

        registro_id = result.scalar()
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao salvar mapeamento: {e}")
        return jsonify({"success": False, "error": f"Erro ao salvar: {e}"}), 500

    # textos por perfil
    textos = {
        1: {
            "titulo": "RESULTADO DO SEU MAPEAMENTO (PERFIL 1)",
            "headline": "Hoje, você estuda, mas sem um direcionamento claro.",
            "texto": (
                "Isso faz com que o esforço se acumule sem gerar evolução real. "
                "Se o ENEM fosse amanhã, você provavelmente não atingiria a nota de corte no seu cenário atual."
            )
        },
        2: {
            "titulo": "RESULTADO DO SEU MAPEAMENTO (PERFIL 2)",
            "headline": "Você já deu passos importantes, mas ainda não tem clareza total do que corrigir primeiro.",
            "texto": (
                "Sem método para acompanhar erros e evolução, o progresso tende a ser lento. "
                "Se o ENEM fosse amanhã, você ainda estaria em risco."
            )
        },
        3: {
            "titulo": "RESULTADO DO SEU MAPEAMENTO (PERFIL 3)",
            "headline": "Você sabe o que precisa estudar, mas manter constância é o maior desafio.",
            "texto": (
                "Sem um sistema que sustente o ritmo, até bons planos acabam falhando ao longo do tempo."
            )
        }
    }

    base = (
        "Independentemente do seu perfil, o ponto decisivo no ENEM não é estudar mais, "
        "mas estudar com direção e constância. O próximo passo é entender como transformar isso em evolução real."
    )

    return jsonify({
        "success": True,
        "id": registro_id,
        "perfil": perfil,
        "resultado": {
            **textos[perfil],
            "base": base,
            "cta_text": "Ver como aplicar isso na prática",
            "cta_url": VSL_URL
        }
    })


# =========================
# REGISTRAR CLIQUE CTA
# =========================
@mapeamento_bp.route("/registrar-clique/<int:registro_id>", methods=["POST"])
def registrar_clique(registro_id):
    try:
        row = db.session.execute(text("""
            SELECT clicou_cta, total_cliques
            FROM mapeamento_direcionamento
            WHERE id = :id
        """), {"id": registro_id}).mappings().first()

        if not row:
            return jsonify({"success": False, "error": "Registro não encontrado"}), 404

        if row["clicou_cta"]:
            # Já clicou antes, só incrementa contador
            db.session.execute(text("""
                UPDATE mapeamento_direcionamento
                SET total_cliques = COALESCE(total_cliques, 0) + 1,
                    data_ultimo_clique = NOW()
                WHERE id = :id
            """), {"id": registro_id})
        else:
            # Primeiro clique
            db.session.execute(text("""
                UPDATE mapeamento_direcionamento
                SET clicou_cta = TRUE,
                    total_cliques = 1,
                    data_primeiro_clique = NOW(),
                    data_ultimo_clique = NOW()
                WHERE id = :id
            """), {"id": registro_id})

        db.session.commit()
        return jsonify({"success": True, "id": registro_id})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao registrar clique: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# =========================
# ADMIN — ESTATÍSTICAS
# =========================
@mapeamento_bp.route("/admin/estatisticas")
@admin_required
def admin_estatisticas():
    try:
        # Total de mapeamentos
        total = db.session.execute(
            text("SELECT COUNT(*) FROM mapeamento_direcionamento")
        ).scalar() or 0

        # Total que clicaram no CTA
        clicaram = db.session.execute(
            text("SELECT COUNT(*) FROM mapeamento_direcionamento WHERE clicou_cta = TRUE")
        ).scalar() or 0

        # CTR
        ctr = round((clicaram / total * 100), 1) if total > 0 else 0

        # Distribuição por perfil - ✅ CORRIGIDO: converter para lista de dicts
        perfis_raw = db.session.execute(text("""
            SELECT perfil, COUNT(*) AS total
            FROM mapeamento_direcionamento
            GROUP BY perfil
            ORDER BY perfil
        """)).mappings().all()
        
        # ✅ Converter RowMapping para dict
        perfis = [dict(row) for row in perfis_raw]

        # Volume por dia (últimos 7 dias) - filtra em UTC, agrupa em BRT
        por_dia_raw = db.session.execute(text("""
            SELECT
                DATE(data_realizacao AT TIME ZONE 'America/Sao_Paulo') AS data,
                COUNT(*) AS total
            FROM mapeamento_direcionamento
            WHERE data_realizacao >= (NOW() - INTERVAL '7 days')
            GROUP BY DATE(data_realizacao AT TIME ZONE 'America/Sao_Paulo')
            ORDER BY data ASC
        """)).mappings().all()
        
        # ✅ Converter para formato serializável
        labels_dias = [str(row["data"]) for row in por_dia_raw]
        valores_dias = [int(row["total"]) for row in por_dia_raw]

        # Tempo médio
        tempo_medio = db.session.execute(text("""
            SELECT AVG(tempo_realizado) AS media
            FROM mapeamento_direcionamento
            WHERE tempo_realizado IS NOT NULL
        """)).scalar()
        tempo_medio = int(tempo_medio) if tempo_medio else 0

        return render_template(
            "mapeamento/admin_estatisticas.html",
            total=total,
            clicaram=clicaram,
            ctr=ctr,
            perfis=perfis,
            labels_dias=labels_dias,
            valores_dias=valores_dias,
            tempo_medio=tempo_medio
        )

    except Exception as e:
        current_app.logger.error(f"Erro ao carregar estatísticas: {e}")
        flash("Erro ao carregar estatísticas do mapeamento.", "danger")
        return redirect(url_for("main.index"))


# =========================
# ADMIN — REGISTROS (SEM PII)
# =========================
@mapeamento_bp.route("/admin/registros")
@admin_required
def admin_registros():
    try:
        registros = db.session.execute(
            text("""
                SELECT
                    id,
                    perfil,
                    tempo_realizado,
                    clicou_cta,
                    total_cliques,
                    utm_source,
                    utm_medium,
                    utm_campaign,
                    utm_content,
                    utm_term,
                    origem_funil,

                    -- ✅ Datas em horário de Brasília (UTC-3)
                    to_char(
                        data_realizacao AT TIME ZONE 'America/Sao_Paulo',
                        'DD/MM/YYYY HH24:MI'
                    ) AS data_realizacao_br,

                    to_char(
                        data_ultimo_clique AT TIME ZONE 'America/Sao_Paulo',
                        'DD/MM/YYYY HH24:MI'
                    ) AS data_ultimo_clique_br,

                    -- ✅ Datas ISO para ordenação (também em Brasília)
                    to_char(
                        data_realizacao AT TIME ZONE 'America/Sao_Paulo',
                        'YYYY-MM-DD HH24:MI:SS'
                    ) AS data_realizacao_sort,

                    to_char(
                        data_ultimo_clique AT TIME ZONE 'America/Sao_Paulo',
                        'YYYY-MM-DD HH24:MI:SS'
                    ) AS data_ultimo_clique_sort

                FROM mapeamento_direcionamento
                ORDER BY data_realizacao DESC
                LIMIT 200
            """)
        ).mappings().all()

        return render_template(
            "mapeamento/admin_registros.html",
            registros=registros
        )

    except Exception as e:
        current_app.logger.error(f"Erro ao carregar registros do mapeamento: {e}")
        flash("Erro ao carregar registros do mapeamento.", "danger")
        return redirect(url_for("main.index"))
