# app/routes/webhook_kiwify.py
"""
Webhook Kiwify - Integração oficial com os 3 produtos:
1. Taxa de Resgate (Plataforma Launcher)
2. Plano Mensal (Plataforma Launcher - Mensal)
3. Plano Anual (Plataforma Launcher - Anual)

VERSÃO CORRIGIDA:
- Trata username duplicado
- Envia email de boas-vindas para novos usuários
- Envia email de plano ativado para usuários existentes
- Usa senha baseada no CPF
"""

from flask import Blueprint, request, jsonify
from app.models.user import User
from app import db
from app.services.email_service import EmailService
import logging, json
from datetime import datetime
from sqlalchemy.exc import IntegrityError

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
# 📋 Extrair dados da Kiwify com segurança
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
# 👤 Buscar ou criar usuário (com tratamento de duplicidade)
# ============================================
def buscar_ou_criar_usuario(email, nome, cpf):
    """
    Busca usuário por email. Se não existir, cria um novo.
    Retorna: (usuario, eh_novo, erro)
    """
    try:
        # 1. Buscar por email
        usuario = User.query.filter_by(email=email).first()
        
        if usuario:
            logger.info(f"👤 Usuário existente encontrado: {email}")
            return usuario, False, None
        
        # 2. Criar novo usuário
        logger.info(f"🆕 Criando novo usuário: {email}")
        
        # Gerar username único
        username_base = email.split("@")[0]
        username = username_base
        contador = 1
        
        # Verificar se username já existe e adicionar contador se necessário
        while User.query.filter_by(username=username).first():
            username = f"{username_base}{contador}"
            contador += 1
            logger.info(f"🔄 Username {username_base} já existe, tentando: {username}")
        
        # Gerar senha inicial baseada no CPF
        senha_inicial = ''.join(filter(str.isdigit, cpf)) if cpf and len(cpf) == 11 else "launcher123"
        
        # Criar usuário
        novo_usuario = User(
            email=email,
            nome_completo=nome,
            cpf=cpf,
            username=username,
            is_active=True,
        )
        novo_usuario.set_password(senha_inicial)
        
        db.session.add(novo_usuario)
        db.session.commit()
        
        logger.info(f"✅ Novo usuário criado com sucesso: {email} | Username: {username}")
        return novo_usuario, True, None
        
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"❌ Erro de integridade ao criar usuário: {e}")
        # Tentar buscar novamente (pode ter sido criado por outro processo)
        usuario = User.query.filter_by(email=email).first()
        if usuario:
            return usuario, False, None
        return None, False, str(e)
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Erro inesperado ao criar usuário: {e}")
        return None, False, str(e)


# ============================================
# 💡 Ativar plano usando método do modelo User
# ============================================
def processar_ativacao_plano(usuario: User, tipo: str, produto_id=None, eh_novo_usuario=False):
    """
    Ativa plano e envia email apropriado
    - Novo usuário: Email de boas-vindas com credenciais
    - Usuário existente: Email de plano ativado
    """
    try:
        if tipo not in ["mensal", "anual"]:
            logger.error(f"Tipo de plano inválido recebido: {tipo}")
            return False

        # Ativar plano
        sucesso = usuario.ativar_plano(tipo, produto_id)
        if not sucesso:
            logger.error(f"Falha ao ativar plano {tipo} para {usuario.email}")
            return False

        logger.info(f"✅ Plano {tipo} ativado para {usuario.email}")

        # Determinar qual email enviar
        nome = getattr(usuario, "nome_completo", usuario.email.split("@")[0])
        dias = 30 if tipo == "mensal" else 365
        
        if eh_novo_usuario:
            # Novo usuário: Email de boas-vindas com credenciais + plano
            logger.info(f"📧 Enviando email de boas-vindas para novo usuário: {usuario.email}")
            EmailService.enviar_email_boas_vindas_compra(
                usuario.email,
                nome,
                getattr(usuario, "cpf", ""),
                tipo_plano=f"Plano {tipo.capitalize()}"
            )
        else:
            # Usuário existente: Email de plano ativado
            logger.info(f"📧 Enviando email de plano ativado para usuário existente: {usuario.email}")
            EmailService.enviar_email_plano_ativado(
                usuario.email,
                nome,
                tipo.capitalize(),
                dias
            )
        
        return True

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
        usuario, eh_novo, erro = buscar_ou_criar_usuario(
            dados_extraidos["email"],
            dados_extraidos["nome"],
            dados_extraidos["cpf"]
        )
        
        if not usuario:
            logger.error(f"❌ Falha ao buscar/criar usuário: {erro}")
            return jsonify({"error": f"Erro ao processar usuário: {erro}"}), 500

        # Executar ação conforme produto
        if produto_tipo == "taxa_resgate":
            liberar_resgate(usuario)
        elif produto_tipo == "plano_mensal":
            processar_ativacao_plano(usuario, "mensal", dados_extraidos["produto_id"], eh_novo)
        elif produto_tipo == "plano_anual":
            processar_ativacao_plano(usuario, "anual", dados_extraidos["produto_id"], eh_novo)
        else:
            logger.warning(f"Produto sem ação mapeada: {produto_tipo}")
            return jsonify({"error": "Produto sem ação"}), 400

        return jsonify({
            "success": True,
            "usuario": usuario.email,
            "produto": produto_tipo,
            "novo_usuario": eh_novo,
            "status": "processado",
        }), 200

    except Exception as e:
        logger.error(f"❌ Erro no webhook: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.session.rollback()
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

    processar_ativacao_plano(usuario, tipo, eh_novo_usuario=False)
    return jsonify({"success": True, "msg": f"Plano {tipo} ativado para {email}"}), 200
