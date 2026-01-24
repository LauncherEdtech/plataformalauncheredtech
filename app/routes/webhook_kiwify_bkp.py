# app/routes/webhook_kiwify.py
"""
Webhook Kiwify - Integração oficial com os 3 produtos:
1. Taxa de Resgate (Plataforma Launcher)
2. Plano Mensal (Plataforma Launcher - Mensal)
3. Plano Anual (Plataforma Launcher - Anual)
"""

# ============================================
# 🔥 VERSÃO FINAL - WEBHOOK KIWIFY INTEGRADO
# ============================================

from flask import Blueprint, request, jsonify
from app.models.user import User
from app import db
from app.services.email_service import EmailService
import logging, json
from datetime import datetime

logger = logging.getLogger(__name__)
webhook_bp = Blueprint('webhook', __name__, url_prefix='/webhook')

# 💳 Mapear produtos Kiwify (para logs e identificação)
PRODUTOS_KIWIFY = {
    'taxa_resgate': {
        'nome': 'Taxa de Resgate (Plataforma Launcher)',
        'url': 'https://pay.kiwify.com.br/2HipOfz',
        'acao': 'liberar_resgate'
    },
    'plano_mensal': {
        'nome': 'Plataforma Launcher (Mensal)',
        'url': 'https://pay.kiwify.com.br/jCQpKD3',
        'acao': 'ativar_plano_mensal'
    },
    'plano_anual': {
        'nome': 'Plataforma Launcher',
        'url': 'https://pay.kiwify.com.br/SVj90JQ',
        'acao': 'ativar_plano_anual'
    }
}


# ============================================
# 🔍 Extrair dados da Kiwify com segurança
# ============================================
def extrair_dados_kiwify(payload: dict):
    try:
        customer = payload.get("customer") or payload.get("Customer") or {}
        product = payload.get("product") or payload.get("Product") or {}
        order = payload.get("order") or payload.get("Order") or {}

        nome = customer.get("full_name") or customer.get("name") or "Usuário"
        email = (customer.get("email") or "").strip().lower()
        cpf = "".join(filter(str.isdigit, str(customer.get("cpf") or customer.get("CPF") or "")))

        product_name = (
            product.get("name")
            or product.get("product_name")
            or order.get("product_name")
            or ""
        ).lower()

        product_id = (
            product.get("id")
            or product.get("product_id")
            or order.get("product_id")
            or ""
        )

        logger.info(f"🧩 Produto recebido: {product_name} | ID: {product_id}")

        return {
            "nome": nome,
            "email": email,
            "cpf": cpf,
            "produto_nome": product_name,
            "produto_id": product_id,
            "status": payload.get("order_status", "").lower(),
        }

    except Exception as e:
        logger.error(f"❌ Erro ao extrair dados da Kiwify: {e}")
        return None


# ============================================
# 🎯 Identificar tipo de produto
# ============================================
def identificar_produto(nome_produto: str):
    if not nome_produto:
        return None
    nome_produto = nome_produto.lower()
    if "resgate" in nome_produto:
        return "taxa_resgate"
    elif "mensal" in nome_produto:
        return "plano_mensal"
    elif "anual" in nome_produto or "launcher" in nome_produto:
        return "plano_anual"
    return None


# ============================================
# 💡 Ativar plano usando método do modelo User
# ============================================
def processar_ativacao_plano(usuario: User, tipo: str, produto_id=None):
    try:
        if tipo not in ["mensal", "anual"]:
            logger.error(f"Tipo de plano inválido recebido: {tipo}")
            return False

        sucesso = usuario.ativar_plano(tipo, produto_id)
        if sucesso:
            EmailService.enviar_email_plano_ativado(
                usuario.email,
                getattr(usuario, "nome_completo", usuario.email.split("@")[0]),
                tipo.capitalize(),
                30 if tipo == "mensal" else 365
            )
            logger.info(f"✅ Plano {tipo} ativado para {usuario.email}")
            return True
        else:
            logger.error(f"Falha ao ativar plano {tipo} para {usuario.email}")
            return False

    except Exception as e:
        logger.error(f"❌ Erro ao processar ativação do plano: {e}")
        return False


# ============================================
# 🎁 Liberar Taxa de Resgate da Roleta
# ============================================
def liberar_resgate(usuario: User):
    try:
        usuario.liberar_resgate_roleta()
        EmailService.enviar_email_taxa_resgate(usuario.email, usuario.nome_completo)
        logger.info(f"🎁 Taxa de resgate confirmada para {usuario.email}")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao liberar resgate: {e}")
        return False


# ============================================
# 🚀 Webhook principal
# ============================================
@webhook_bp.route("/kiwify", methods=["POST"])
def webhook_kiwify():
    try:
        if not request.is_json:
            return jsonify({"error": "Requisição inválida"}), 400

        dados = request.get_json()
        logger.info(f"📥 Webhook recebido: {json.dumps(dados, indent=2)[:800]}")

        dados_extraidos = extrair_dados_kiwify(dados)
        if not dados_extraidos:
            return jsonify({"error": "Dados inválidos"}), 400

        # Ignorar eventos não pagos
        if dados_extraidos["status"] not in ["paid", "complete", "approved"]:
            logger.info(f"⏸️ Ignorando evento com status: {dados_extraidos['status']}")
            return jsonify({"ignored": True})

        produto_tipo = identificar_produto(dados_extraidos["produto_nome"])
        if not produto_tipo:
            logger.warning(f"⚠️ Produto não identificado: {dados_extraidos['produto_nome']}")
            return jsonify({"error": "Produto não identificado"}), 400

        # Buscar ou criar usuário
        usuario = User.query.filter_by(email=dados_extraidos["email"]).first()
        if not usuario:
            usuario = User(
                email=dados_extraidos["email"],
                nome_completo=dados_extraidos["nome"],
                cpf=dados_extraidos["cpf"],
                username=dados_extraidos["email"].split("@")[0],
                is_active=True,
            )
            usuario.set_password("launcher123")
            db.session.add(usuario)
            db.session.commit()
            logger.info(f"👤 Usuário criado: {usuario.email}")

        # Executar ação conforme produto
        if produto_tipo == "taxa_resgate":
            liberar_resgate(usuario)
        elif produto_tipo == "plano_mensal":
            processar_ativacao_plano(usuario, "mensal", dados_extraidos["produto_id"])
        elif produto_tipo == "plano_anual":
            processar_ativacao_plano(usuario, "anual", dados_extraidos["produto_id"])
        else:
            logger.warning(f"Produto sem ação mapeada: {produto_tipo}")
            return jsonify({"error": "Produto sem ação"}), 400

        return jsonify({
            "success": True,
            "usuario": usuario.email,
            "produto": produto_tipo,
            "status": "processado",
        }), 200

    except Exception as e:
        logger.error(f"❌ Erro no webhook: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


# ============================================
# 🧪 Rota de teste rápido
# ============================================
@webhook_bp.route("/kiwify/test", methods=["GET"])
def webhook_test():
    return jsonify({
        "status": "ativo",
        "produtos": list(PRODUTOS_KIWIFY.keys()),
        "url": request.url_root + "webhook/kiwify"
    })


# ============================================
# 🧩 Simulação manual de plano (para debug)
# ============================================
@webhook_bp.route("/kiwify/simular/<email>/<tipo>", methods=["GET"])
def simular_pagamento(email, tipo):
    """Simula a confirmação de pagamento manualmente (debug)"""
    usuario = User.query.filter_by(email=email).first()
    if not usuario:
        return jsonify({"error": "Usuário não encontrado"}), 404

    if tipo not in ["mensal", "anual"]:
        return jsonify({"error": "Tipo inválido"}), 400

    processar_ativacao_plano(usuario, tipo)
    return jsonify({"success": True, "msg": f"Plano {tipo} ativado para {email}"}), 200
