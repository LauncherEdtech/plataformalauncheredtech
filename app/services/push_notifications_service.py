# CAMINHO: app/services/push_notification_service.py
# Instale a dependência: pip install firebase-admin

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Inicialização do Firebase Admin SDK
# ─────────────────────────────────────────────
_firebase_initialized = False

def _init_firebase():
    global _firebase_initialized
    if _firebase_initialized:
        return True

    try:
        import firebase_admin
        from firebase_admin import credentials

        # Caminho para o arquivo JSON de credenciais do Firebase Admin
        # ⚠️  Baixe este arquivo em: Firebase Console > Configurações > Contas de Serviço
        cred_path = os.environ.get(
            'FIREBASE_CREDENTIALS_PATH',
            'firebase-credentials.json'  # coloque na raiz do projeto
        )

        if not os.path.exists(cred_path):
            logger.error(f"[FCM] Arquivo de credenciais não encontrado: {cred_path}")
            return False

        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        logger.info("[FCM] Firebase Admin SDK inicializado com sucesso!")
        return True

    except ImportError:
        logger.error("[FCM] firebase-admin não instalado. Execute: pip install firebase-admin")
        return False
    except Exception as e:
        logger.error(f"[FCM] Erro ao inicializar Firebase Admin: {e}")
        return False


# ─────────────────────────────────────────────
# Enviar notificação para UM usuário
# ─────────────────────────────────────────────
def enviar_notificacao_usuario(
    user_id: int,
    titulo: str,
    mensagem: str,
    url: str = '/dashboard',
    tag: str = 'geral',
    dados_extras: Optional[dict] = None
) -> dict:
    """
    Envia push notification para todos os dispositivos de um usuário.
    
    Args:
        user_id: ID do usuário
        titulo: Título da notificação
        mensagem: Corpo da notificação
        url: URL para abrir ao clicar (relativa, ex: '/simulados')
        tag: Tag para agrupar notificações do mesmo tipo
        dados_extras: Dados adicionais para o payload
    
    Returns:
        dict com success, enviados, falhas
    """
    if not _init_firebase():
        return {'success': False, 'error': 'Firebase não inicializado'}

    try:
        from firebase_admin import messaging
        from app import db

        # Busca tokens ativos do usuário
        result = db.session.execute(
            "SELECT token FROM user_fcm_tokens WHERE user_id = :user_id AND ativo = true",
            {'user_id': user_id}
        )
        tokens = [row[0] for row in result.fetchall()]

        if not tokens:
            logger.warning(f"[FCM] Usuário {user_id} sem tokens FCM ativos")
            return {'success': False, 'error': 'Sem tokens ativos para este usuário'}

        enviados = 0
        falhas = []

        for token in tokens:
            try:
                msg = messaging.Message(
                    notification=messaging.Notification(
                        title=titulo,
                        body=mensagem,
                    ),
                    data={
                        'url': url,
                        'tag': tag,
                        **(dados_extras or {}),
                    },
                    webpush=messaging.WebpushConfig(
                        notification=messaging.WebpushNotification(
                            title=titulo,
                            body=mensagem,
                            icon='/static/images/icons/icon-192x192.png',
                            badge='/static/images/icons/icon-72x72.png',
                            vibrate=[200, 100, 200],
                            tag=tag,
                            require_interaction=False,
                        ),
                        fcm_options=messaging.WebpushFCMOptions(link=url),
                    ),
                    token=token,
                )
                messaging.send(msg)
                enviados += 1

            except Exception as e:
                erro_str = str(e)
                falhas.append({'token': token[:20] + '...', 'erro': erro_str})
                # Token inválido/expirado → desativa no banco
                if 'registration-token-not-registered' in erro_str or 'invalid-registration-token' in erro_str:
                    _desativar_token(token)

        logger.info(f"[FCM] Usuário {user_id}: {enviados} enviado(s), {len(falhas)} falha(s)")
        return {
            'success': enviados > 0,
            'enviados': enviados,
            'falhas': falhas,
        }

    except Exception as e:
        logger.error(f"[FCM] Erro ao enviar notificação para usuário {user_id}: {e}")
        return {'success': False, 'error': str(e)}


# ─────────────────────────────────────────────
# Enviar notificação em MASSA (todos usuários ou grupo)
# ─────────────────────────────────────────────
def enviar_notificacao_massa(
    titulo: str,
    mensagem: str,
    url: str = '/dashboard',
    tag: str = 'geral',
    filtro_plataforma: Optional[str] = None
) -> dict:
    """
    Envia notificação para todos os usuários com tokens ativos.
    Usa multicast do FCM (máx 500 tokens por lote).
    
    Args:
        filtro_plataforma: 'android', 'ios', 'desktop', ou None para todos
    """
    if not _init_firebase():
        return {'success': False, 'error': 'Firebase não inicializado'}

    try:
        from firebase_admin import messaging
        from app import db

        query = "SELECT token FROM user_fcm_tokens WHERE ativo = true"
        params = {}

        if filtro_plataforma:
            query += " AND plataforma = :plataforma"
            params['plataforma'] = filtro_plataforma

        result = db.session.execute(query, params)
        todos_tokens = [row[0] for row in result.fetchall()]

        if not todos_tokens:
            return {'success': False, 'error': 'Nenhum token ativo encontrado'}

        total_enviados = 0
        total_falhas = 0

        # Processa em lotes de 500 (limite do FCM multicast)
        for i in range(0, len(todos_tokens), 500):
            lote = todos_tokens[i:i + 500]

            msg = messaging.MulticastMessage(
                notification=messaging.Notification(title=titulo, body=mensagem),
                data={'url': url, 'tag': tag},
                webpush=messaging.WebpushConfig(
                    notification=messaging.WebpushNotification(
                        title=titulo,
                        body=mensagem,
                        icon='/static/images/icons/icon-192x192.png',
                        badge='/static/images/icons/icon-72x72.png',
                        tag=tag,
                    ),
                ),
                tokens=lote,
            )

            response = messaging.send_each_for_multicast(msg)
            total_enviados += response.success_count
            total_falhas += response.failure_count

            # Desativa tokens inválidos
            for idx, resp in enumerate(response.responses):
                if not resp.success:
                    erro = str(resp.exception) if resp.exception else ''
                    if 'not-registered' in erro or 'invalid-registration-token' in erro:
                        _desativar_token(lote[idx])

        logger.info(f"[FCM] Massa: {total_enviados} enviados, {total_falhas} falhas de {len(todos_tokens)} tokens")
        return {
            'success': True,
            'total_tokens': len(todos_tokens),
            'enviados': total_enviados,
            'falhas': total_falhas,
        }

    except Exception as e:
        logger.error(f"[FCM] Erro ao enviar notificação em massa: {e}")
        return {'success': False, 'error': str(e)}


# ─────────────────────────────────────────────
# Utilitários pré-definidos (use estes no código)
# ─────────────────────────────────────────────

def notif_resultado_redacao(user_id: int, nota: float):
    return enviar_notificacao_usuario(
        user_id=user_id,
        titulo='📝 Redação Corrigida!',
        mensagem=f'Sua redação foi corrigida. Nota: {nota:.0f}/1000. Veja o feedback completo!',
        url='/redacao',
        tag='redacao',
    )


def notif_lembrete_simulado(user_id: int, nome_simulado: str):
    return enviar_notificacao_usuario(
        user_id=user_id,
        titulo='📊 Simulado Agendado',
        mensagem=f'Seu simulado "{nome_simulado}" está te esperando! Hora de estudar.',
        url='/simulados',
        tag='simulado',
    )


def notif_streak_em_risco(user_id: int, sequencia: int):
    return enviar_notificacao_usuario(
        user_id=user_id,
        titulo='🔥 Sua sequência está em risco!',
        mensagem=f'Você tem {sequencia} dias seguidos de estudo. Não perca agora!',
        url='/dashboard',
        tag='streak',
    )


def notif_resposta_helpzone(user_id: int, pergunta_titulo: str, pergunta_id: int):
    return enviar_notificacao_usuario(
        user_id=user_id,
        titulo='💬 Nova resposta na HelpZone!',
        mensagem=f'Alguém respondeu sua dúvida: "{pergunta_titulo[:50]}..."',
        url=f'/helpzone/duvida/{pergunta_id}',
        tag='helpzone',
    )


def notif_novo_conteudo(user_id: int, materia: str):
    return enviar_notificacao_usuario(
        user_id=user_id,
        titulo='📚 Novo conteúdo disponível!',
        mensagem=f'Novas aulas de {materia} foram adicionadas. Bora estudar?',
        url='/estudo',
        tag='conteudo',
    )


def notif_xp_ganho(user_id: int, xp: int, motivo: str):
    return enviar_notificacao_usuario(
        user_id=user_id,
        titulo=f'⭐ +{xp} XP ganhos!',
        mensagem=f'Você ganhou {xp} XP por {motivo}. Continue assim!',
        url='/dashboard',
        tag='xp',
    )


# ─────────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────────

def _desativar_token(token: str):
    """Marca token como inativo no banco quando FCM reportar erro"""
    try:
        from app import db
        db.session.execute(
            "UPDATE user_fcm_tokens SET ativo = false WHERE token = :token",
            {'token': token}
        )
        db.session.commit()
        logger.info(f"[FCM] Token desativado: {token[:20]}...")
    except Exception as e:
        logger.error(f"[FCM] Erro ao desativar token: {e}")
        db.session.rollback()
