# CAMINHO: app/routes/pwa.py
# Registre no __init__.py com:
#   _register_bp("app.routes.pwa", "pwa_bp", "pwa", required=False)

import os
import json
import logging
from datetime import datetime

from flask import (
    Blueprint, request, jsonify, send_from_directory,
    current_app, make_response
)
from flask_login import login_required, current_user

from app import db

logger = logging.getLogger(__name__)

pwa_bp = Blueprint('pwa', __name__, url_prefix='/pwa')


# ─────────────────────────────────────────────
# Service Workers (precisam ser servidos da raiz)
# ─────────────────────────────────────────────

@pwa_bp.route('/sw.js')
def service_worker():
    """Serve o Service Worker a partir da raiz /sw.js"""
    response = make_response(
        send_from_directory(current_app.static_folder, 'sw.js')
    )
    response.headers['Content-Type'] = 'application/javascript'
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response


@pwa_bp.route('/firebase-messaging-sw.js')
def firebase_sw():
    """Serve o Service Worker do FCM a partir de /firebase-messaging-sw.js"""
    response = make_response(
        send_from_directory(current_app.static_folder, 'firebase-messaging-sw.js')
    )
    response.headers['Content-Type'] = 'application/javascript'
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response


@pwa_bp.route('/manifest.json')
def manifest():
    """Serve o Web App Manifest"""
    response = make_response(
        send_from_directory(current_app.static_folder, 'manifest.json')
    )
    response.headers['Content-Type'] = 'application/manifest+json'
    return response


# ─────────────────────────────────────────────
# API: Salvar Token FCM do usuário
# ─────────────────────────────────────────────

@pwa_bp.route('/salvar-token', methods=['POST'])
@login_required
def salvar_token():
    """Recebe e salva o token FCM do dispositivo do usuário"""
    try:
        data = request.get_json()
        if not data or 'token' not in data:
            return jsonify({'success': False, 'error': 'Token não fornecido'}), 400

        token = data['token'].strip()
        plataforma = data.get('plataforma', 'unknown')
        user_agent = data.get('user_agent', '')[:500]  # limita tamanho

        if not token:
            return jsonify({'success': False, 'error': 'Token inválido'}), 400

        # Upsert: insere ou atualiza se o token já existir
        db.session.execute(
            """
            INSERT INTO user_fcm_tokens (user_id, token, plataforma, user_agent, criado_em, atualizado_em)
            VALUES (:user_id, :token, :plataforma, :user_agent, :now, :now)
            ON CONFLICT (token)
            DO UPDATE SET
                user_id = :user_id,
                plataforma = :plataforma,
                user_agent = :user_agent,
                atualizado_em = :now,
                ativo = true
            """,
            {
                'user_id': current_user.id,
                'token': token,
                'plataforma': plataforma,
                'user_agent': user_agent,
                'now': datetime.utcnow(),
            }
        )
        db.session.commit()

        logger.info(f"[PWA] Token FCM salvo para usuário {current_user.id} ({plataforma})")
        return jsonify({'success': True, 'message': 'Token salvo com sucesso'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"[PWA] Erro ao salvar token FCM: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ─────────────────────────────────────────────
# API: Remover Token (logout / revogar permissão)
# ─────────────────────────────────────────────

@pwa_bp.route('/remover-token', methods=['POST'])
@login_required
def remover_token():
    """Remove/desativa token FCM (ex: no logout ou quando usuário revoga permissão)"""
    try:
        data = request.get_json()
        token = data.get('token') if data else None

        if token:
            # Remove token específico
            db.session.execute(
                "UPDATE user_fcm_tokens SET ativo = false WHERE token = :token AND user_id = :user_id",
                {'token': token, 'user_id': current_user.id}
            )
        else:
            # Remove todos os tokens do usuário
            db.session.execute(
                "UPDATE user_fcm_tokens SET ativo = false WHERE user_id = :user_id",
                {'user_id': current_user.id}
            )

        db.session.commit()
        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        logger.error(f"[PWA] Erro ao remover token FCM: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ─────────────────────────────────────────────
# Página offline (mostrada quando sem internet)
# ─────────────────────────────────────────────

@pwa_bp.route('/offline')
def offline():
    """Página exibida quando o usuário está offline"""
    from flask import render_template
    return render_template('pwa/offline.html')
