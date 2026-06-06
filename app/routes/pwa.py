import logging
from datetime import datetime
from sqlalchemy import text
from flask import Blueprint, request, jsonify, send_from_directory, current_app, make_response, render_template
from flask_login import login_required, current_user
from app import db

logger = logging.getLogger(__name__)
pwa_bp = Blueprint('pwa', __name__, url_prefix='/pwa')

@pwa_bp.route('/sw.js')
def service_worker():
    r = make_response(send_from_directory(current_app.static_folder, 'sw.js'))
    r.headers['Content-Type'] = 'application/javascript'
    r.headers['Service-Worker-Allowed'] = '/'
    r.headers['Cache-Control'] = 'no-cache'
    return r

@pwa_bp.route('/firebase-messaging-sw.js')
def firebase_sw():
    r = make_response(send_from_directory(current_app.static_folder, 'firebase-messaging-sw.js'))
    r.headers['Content-Type'] = 'application/javascript'
    r.headers['Service-Worker-Allowed'] = '/'
    r.headers['Cache-Control'] = 'no-cache'
    return r

@pwa_bp.route('/manifest.json')
def manifest():
    r = make_response(send_from_directory(current_app.static_folder, 'manifest.json'))
    r.headers['Content-Type'] = 'application/manifest+json'
    return r

@pwa_bp.route('/salvar-token', methods=['POST'])
@login_required
def salvar_token():
    try:
        data = request.get_json()
        if not data or 'token' not in data:
            return jsonify({'success': False, 'error': 'Token nao fornecido'}), 400
        token = data['token'].strip()
        plataforma = data.get('plataforma', 'unknown')
        user_agent = data.get('user_agent', '')[:500]
        if not token:
            return jsonify({'success': False, 'error': 'Token invalido'}), 400
        db.session.execute(
            text("""
                INSERT INTO user_fcm_tokens (user_id, token, plataforma, user_agent, criado_em, atualizado_em)
                VALUES (:user_id, :token, :plataforma, :user_agent, :now, :now)
                ON CONFLICT ON CONSTRAINT user_fcm_tokens_token_key
                DO UPDATE SET user_id=:user_id, plataforma=:plataforma, user_agent=:user_agent, atualizado_em=:now, ativo=true
            """),
            {'user_id': current_user.id, 'token': token, 'plataforma': plataforma, 'user_agent': user_agent, 'now': datetime.utcnow()}
        )
        db.session.commit()
        logger.info(f"[PWA] Token FCM salvo user {current_user.id} ({plataforma})")
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        logger.error(f"[PWA] Erro salvar token: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@pwa_bp.route('/remover-token', methods=['POST'])
@login_required
def remover_token():
    try:
        data = request.get_json()
        token = data.get('token') if data else None
        if token:
            db.session.execute(text("UPDATE user_fcm_tokens SET ativo=false WHERE token=:token AND user_id=:uid"), {'token': token, 'uid': current_user.id})
        else:
            db.session.execute(text("UPDATE user_fcm_tokens SET ativo=false WHERE user_id=:uid"), {'uid': current_user.id})
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@pwa_bp.route('/offline')
def offline():
    return render_template('pwa/offline.html')
