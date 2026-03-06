# app/routes/helpzone.py
"""
Rotas do HelpZone como Feed Social de Estudos
Sistema completo de rede social focada em rotina de estudos
"""

import os
import time
import re
import uuid
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import desc, or_, and_, func
from app import db
from app.models.helpzone_social import (
    Post, PostMidia, PostLike, PostComentario,
    Seguidor, NotificacaoSocial, PerfilSocial, Desafio, PostSalvo,
    Story, StoryVisualizacao, DenunciaPost, Hashtag, post_hashtags
)

helpzone_bp = Blueprint('helpzone', __name__, url_prefix='/helpzone')

# ==================== CONFIGURAÇÕES DE UPLOAD ====================
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'mov'}
MAX_IMAGE_SIZE = 5 * 1024 * 1024   # 5MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB
MAX_VIDEO_DURATION = 20  # 20 segundos


def allowed_file(filename, allowed_extensions):
    """Verifica se a extensão do arquivo é permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def generate_unique_filename(filename):
    """Gera nome único para o arquivo"""
    ext = filename.rsplit('.', 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}_{int(datetime.now().timestamp())}.{ext}"
    return unique_name


# ==================== PÁGINA PRINCIPAL - FEED ====================
@helpzone_bp.route('/')
@helpzone_bp.route('/feed')
@login_required
def feed():
    """
    Feed principal do HelpZone Social
    Mostra posts recentes, de quem você segue e mais populares
    """
    # Garantir que o usuário tem perfil social
    perfil = PerfilSocial.query.filter_by(user_id=current_user.id).first()
    if not perfil:
        perfil = PerfilSocial(user_id=current_user.id)
        db.session.add(perfil)
        db.session.commit()

    # Tipo de feed (recentes, seguindo, populares)
    tipo_feed = request.args.get('tipo', 'recentes')
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Query base
    query = Post.query.filter_by(ativo=True)

    if tipo_feed == 'seguindo':
        seguindo_ids = [s.seguido_id for s in current_user.seguindo.all()]
        query = query.filter(Post.user_id.in_(seguindo_ids))
        query = query.order_by(desc(Post.data_criacao))

    elif tipo_feed == 'populares':
        data_limite = datetime.utcnow() - timedelta(days=7)
        query = query.filter(Post.data_criacao >= data_limite)
        query = query.order_by(desc(Post.total_likes), desc(Post.data_criacao))

    else:  # recentes
        query = query.order_by(desc(Post.data_criacao))

    posts = query.paginate(page=page, per_page=per_page, error_out=False)

    stats = {
        'total_posts': perfil.total_posts,
        'seguidores': perfil.total_seguidores,
        'seguindo': perfil.total_seguindo,
        'likes_recebidos': perfil.total_likes_recebidos,
        'nivel': perfil.nivel_influencia
    }

    notificacoes_count = NotificacaoSocial.query.filter_by(
        user_id=current_user.id,
        lida=False
    ).count()

    return render_template(
        'helpzone/feed.html',
        posts=posts,
        tipo_feed=tipo_feed,
        stats=stats,
        notificacoes_count=notificacoes_count
    )



@helpzone_bp.route('/criar-post', methods=['GET', 'POST'])
@login_required
def criar_post():
    if request.method == 'POST':
        texto = request.form.get('texto', '').strip()
        tipo_midia = request.form.get('tipo_midia', 'texto')

        if not texto and 'arquivo' not in request.files:
            return jsonify({'error': 'Post deve ter texto ou mídia'}), 400

        post = Post(
            user_id=current_user.id,
            texto=texto,
            tipo_midia=tipo_midia
        )
        db.session.add(post)
        db.session.flush()

        if 'arquivo' in request.files:
            arquivo = request.files['arquivo']
            if arquivo and arquivo.filename:
                try:
                    midia_url = processar_upload(arquivo, tipo_midia, post.id)
                    midia = PostMidia(
                        post_id=post.id,
                        tipo=tipo_midia,
                        url=midia_url,
                        processado=True
                    )
                    db.session.add(midia)
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f"Erro ao fazer upload: {e}")
                    return jsonify({'error': 'Erro ao fazer upload do arquivo'}), 500

        perfil = PerfilSocial.query.filter_by(user_id=current_user.id).first()
        if perfil:
            perfil.total_posts += 1
            perfil.ultima_postagem = datetime.utcnow()

        db.session.commit()

        # Hook onboarding
        try:
            from app.services.onboarding_service import verificar_onboarding_ativo, avancar_etapa
            if verificar_onboarding_ativo(current_user.id):
                avancar_etapa(current_user.id, 'criar_post')
        except Exception as e:
            current_app.logger.error(f"❌ Erro no hook de onboarding: {e}")

        # ✅ Retorna JSON para fetch() do JS, redirect para form tradicional
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
           request.content_type and 'multipart' in request.content_type:
            return jsonify({'success': True, 'redirect': url_for('helpzone.feed')})


        # ==================== HOOK ONBOARDING ====================
        try:
            from app.services.onboarding_service import verificar_onboarding_ativo, avancar_etapa
            if verificar_onboarding_ativo(current_user.id):
                current_app.logger.info(f"🎓 Onboarding: usuário {current_user.id} criou primeiro post")
                resultado = avancar_etapa(current_user.id, 'criar_post')
                if resultado.get('status') == 'ativo':
                    current_app.logger.info(f"✅ Onboarding avançado para etapa {resultado.get('etapa')}")
        except Exception as e:
            current_app.logger.error(f"❌ Erro no hook de onboarding: {e}")
        # =========================================================

        flash('Post criado com sucesso!', 'success')
        return redirect(url_for('helpzone.feed'))

    return render_template('helpzone/criar_post.html')


def processar_upload(arquivo, tipo_midia, post_id):
    """
    Processa upload de arquivo (imagem ou vídeo) → S3

    Regra de paths:
      folder = "static/uploads/helpzone/posts"  (sem user_id, sem / inicial)
      s3_service adiciona /{user_id}/ internamente
      key resultante: static/uploads/helpzone/posts/{user_id}/uuid.ext
      URL salva no banco: /{key}  → Nginx serve via proxy_pass para o S3
    """
    if tipo_midia == 'imagem':
        if not allowed_file(arquivo.filename, ALLOWED_IMAGE_EXTENSIONS):
            raise ValueError('Formato de imagem não permitido')
        max_size = MAX_IMAGE_SIZE
    elif tipo_midia == 'video':
        if not allowed_file(arquivo.filename, ALLOWED_VIDEO_EXTENSIONS):
            raise ValueError('Formato de vídeo não permitido')
        max_size = MAX_VIDEO_SIZE
    else:
        raise ValueError('Tipo de mídia inválido')

    # Validar tamanho
    arquivo.seek(0, os.SEEK_END)
    file_size = arquivo.tell()
    arquivo.seek(0)
    if file_size > max_size:
        raise ValueError(f'Arquivo muito grande. Máximo: {max_size / (1024 * 1024):.0f}MB')

    # Upload para S3
    from app.services.s3_service import upload_helpzone_media

    media_type = 'image' if tipo_midia == 'imagem' else 'video'
    key, error = upload_helpzone_media(
        arquivo,
        current_user.id,
        media_type,
        folder="static/uploads/helpzone/posts"
    )
    if error:
        raise Exception(f'Erro no upload S3: {error}')

    # URL relativa — Nginx faz proxy_pass para o S3
    return f"/{key}"


# ==================== LIKE/DISLIKE ====================
@helpzone_bp.route('/api/post/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    tipo = request.json.get('tipo', 'like')  # 'like' ou 'dislike'

    if tipo not in ['like', 'dislike']:
        return jsonify({'error': 'Tipo inválido'}), 400

    like_existente = PostLike.query.filter_by(
        post_id=post_id,
        user_id=current_user.id
    ).first()

    if like_existente:
        if like_existente.tipo == tipo:
            if tipo == 'like':
                post.total_likes = max(0, post.total_likes - 1)
            else:
                post.total_dislikes = max(0, post.total_dislikes - 1)

            db.session.delete(like_existente)
            db.session.commit()

            return jsonify({
                'success': True,
                'action': 'removed',
                'total_likes': post.total_likes,
                'total_dislikes': post.total_dislikes
            })
        else:
            if like_existente.tipo == 'like':
                post.total_likes = max(0, post.total_likes - 1)
                post.total_dislikes += 1
            else:
                post.total_dislikes = max(0, post.total_dislikes - 1)
                post.total_likes += 1

            like_existente.tipo = tipo
            like_existente.data_criacao = datetime.utcnow()
    else:
        novo_like = PostLike(
            post_id=post_id,
            user_id=current_user.id,
            tipo=tipo
        )
        db.session.add(novo_like)

        if tipo == 'like':
            post.total_likes += 1
        else:
            post.total_dislikes += 1

        if tipo == 'like' and post.user_id != current_user.id:
            notif = NotificacaoSocial(
                user_id=post.user_id,
                origem_user_id=current_user.id,
                tipo='like',
                post_id=post_id,
                mensagem=f'{current_user.nome_completo} curtiu seu post'
            )
            db.session.add(notif)

            perfil_autor = PerfilSocial.query.filter_by(user_id=post.user_id).first()
            if perfil_autor:
                perfil_autor.total_likes_recebidos += 1

    db.session.commit()

    return jsonify({
        'success': True,
        'action': 'added',
        'tipo': tipo,
        'total_likes': post.total_likes,
        'total_dislikes': post.total_dislikes
    })


# ==================== COMENTÁRIOS ====================
@helpzone_bp.route('/api/post/<int:post_id>/comentar', methods=['POST'])
@login_required
def comentar_post(post_id):
    post = Post.query.get_or_404(post_id)

    if request.is_json:
        texto = request.json.get('texto', '').strip()
    else:
        texto = request.form.get('texto', '').strip()

    if not texto:
        if request.is_json:
            return jsonify({'error': 'Comentário vazio'}), 400
        else:
            flash('Comentário não pode ser vazio', 'error')
            return redirect(url_for('helpzone.detalhes_post', post_id=post_id))

    comentario = PostComentario(
        post_id=post_id,
        user_id=current_user.id,
        texto=texto
    )
    db.session.add(comentario)

    post.total_comentarios += 1

    if post.user_id != current_user.id:
        notif = NotificacaoSocial(
            user_id=post.user_id,
            origem_user_id=current_user.id,
            tipo='comentario',
            post_id=post_id,
            mensagem=f'{current_user.nome_completo} comentou no seu post'
        )
        db.session.add(notif)

    db.session.commit()

    if request.is_json:
        return jsonify({
            'success': True,
            'comentario': {
                'id': comentario.id,
                'texto': comentario.texto,
                'user': current_user.nome_completo,
                'data': 'Agora mesmo'
            }
        })
    else:
        flash('Comentário adicionado!', 'success')
        return redirect(url_for('helpzone.detalhes_post', post_id=post_id))


# ==================== SEGUIR/DEIXAR DE SEGUIR ====================
@helpzone_bp.route('/api/user/<int:user_id>/follow', methods=['POST'])
@login_required
def follow_user(user_id):
    if user_id == current_user.id:
        return jsonify({'error': 'Você não pode seguir a si mesmo'}), 400

    seguindo = Seguidor.query.filter_by(
        seguidor_id=current_user.id,
        seguido_id=user_id
    ).first()

    if seguindo:
        db.session.delete(seguindo)

        perfil_seguidor = PerfilSocial.query.filter_by(user_id=current_user.id).first()
        if perfil_seguidor:
            perfil_seguidor.total_seguindo = max(0, perfil_seguidor.total_seguindo - 1)

        perfil_seguido = PerfilSocial.query.filter_by(user_id=user_id).first()
        if perfil_seguido:
            perfil_seguido.total_seguidores = max(0, perfil_seguido.total_seguidores - 1)

        db.session.commit()

        return jsonify({
            'success': True,
            'action': 'unfollow',
            'seguindo': False
        })
    else:
        novo_seguidor = Seguidor(
            seguidor_id=current_user.id,
            seguido_id=user_id
        )
        db.session.add(novo_seguidor)

        perfil_seguidor = PerfilSocial.query.filter_by(user_id=current_user.id).first()
        if perfil_seguidor:
            perfil_seguidor.total_seguindo += 1

        perfil_seguido = PerfilSocial.query.filter_by(user_id=user_id).first()
        if perfil_seguido:
            perfil_seguido.total_seguidores += 1

        notif = NotificacaoSocial(
            user_id=user_id,
            origem_user_id=current_user.id,
            tipo='follow',
            mensagem=f'{current_user.nome_completo} começou a seguir você'
        )
        db.session.add(notif)

        db.session.commit()

        return jsonify({
            'success': True,
            'action': 'follow',
            'seguindo': True
        })


# ==================== SALVAR POST ====================
@helpzone_bp.route('/api/post/<int:post_id>/save', methods=['POST'])
@login_required
def salvar_post(post_id):
    post = Post.query.get_or_404(post_id)

    salvo = PostSalvo.query.filter_by(
        user_id=current_user.id,
        post_id=post_id
    ).first()

    if salvo:
        db.session.delete(salvo)
        action = 'removed'
    else:
        novo_salvo = PostSalvo(user_id=current_user.id, post_id=post_id)
        db.session.add(novo_salvo)
        action = 'saved'

    db.session.commit()

    return jsonify({
        'success': True,
        'action': action
    })


# ==================== EDITAR PERFIL (COM FOTO) → S3 ====================
@helpzone_bp.route('/api/perfil/editar', methods=['POST'])
@login_required
def editar_perfil():
    print("--- INICIANDO EDIÇÃO DE PERFIL ---")

    ocupacao = request.form.get('ocupacao', '').strip()
    biografia = request.form.get('biografia', '').strip()

    print(f"Dados recebidos: Ocupação={ocupacao}, Bio={biografia}")

    perfil = PerfilSocial.query.filter_by(user_id=current_user.id).first()
    if not perfil:
        perfil = PerfilSocial(user_id=current_user.id)
        db.session.add(perfil)

    perfil.ocupacao = ocupacao
    perfil.biografia = biografia

    # --- UPLOAD DE FOTO PARA S3 ---
    if 'foto_perfil' not in request.files:
        print("AVISO: Nenhuma foto enviada, mantendo a atual.")
    else:
        arquivo = request.files['foto_perfil']
        print(f"Arquivo recebido: {arquivo.filename}")

        if arquivo and arquivo.filename:
            ALLOWED = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            ext = arquivo.filename.rsplit('.', 1)[1].lower() if '.' in arquivo.filename else ''

            if ext not in ALLOWED:
                print(f"ERRO: Extensão {ext} não permitida.")
                return jsonify({'error': 'Formato inválido'}), 400

            try:
                from app.services.s3_service import upload_helpzone_media

                # folder SEM user_id (a função adiciona /{user_id}/ internamente)
                # folder começa com static/uploads/ para bater com proxy_pass do Nginx
                key, error = upload_helpzone_media(
                    arquivo,
                    current_user.id,
                    'image',
                    folder="static/uploads/helpzone/avatars"
                )
                # key resultante: static/uploads/helpzone/avatars/{user_id}/uuid.jpg

                if error:
                    print(f"ERRO S3: {error}")
                    return jsonify({'error': f'Erro no upload: {error}'}), 500

                # URL = /key → Nginx faz proxy_pass para o S3
                url_db = f"/{key}"
                perfil.foto_perfil = url_db
                print(f"Foto salva no S3. URL no banco: {url_db}")

            except Exception as e:
                print(f"ERRO no upload S3: {str(e)}")
                return jsonify({'error': 'Erro ao fazer upload da foto'}), 500
        else:
            print("AVISO: O arquivo chegou vazio ou sem nome.")

    try:
        db.session.commit()
        print("--- SUCESSO: Alterações commitadas no banco ---")
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"ERRO DE BANCO: {str(e)}")
        return jsonify({'error': 'Erro ao salvar no banco'}), 500


# ==================== PERFIL DO USUÁRIO ====================
@helpzone_bp.route('/perfil/<int:user_id>')
@login_required
def perfil_usuario(user_id):
    from app.models.user import User

    usuario = User.query.get_or_404(user_id)
    perfil = PerfilSocial.query.filter_by(user_id=user_id).first()

    if not perfil:
        perfil = PerfilSocial(user_id=user_id)
        db.session.add(perfil)
        db.session.commit()

    tab = request.args.get('tab', 'posts')
    page = request.args.get('page', 1, type=int)

    if tab == 'salvos' and current_user.id == user_id:
        posts = Post.query.join(PostSalvo).filter(
            PostSalvo.user_id == user_id
        ).order_by(desc(PostSalvo.data_salvo)).paginate(page=page, per_page=18, error_out=False)
    else:
        posts = Post.query.filter_by(user_id=user_id, ativo=True)\
                          .order_by(desc(Post.data_criacao))\
                          .paginate(page=page, per_page=18, error_out=False)

    esta_seguindo = False
    if current_user.id != user_id:
        esta_seguindo = Seguidor.query.filter_by(
            seguidor_id=current_user.id,
            seguido_id=user_id
        ).first() is not None

    return render_template(
        'helpzone/perfil.html',
        usuario=usuario,
        perfil=perfil,
        posts=posts,
        esta_seguindo=esta_seguindo,
        is_own_profile=(current_user.id == user_id),
        active_tab=tab
    )


# ==================== NOTIFICAÇÕES ====================
@helpzone_bp.route('/notificacoes')
@login_required
def notificacoes():
    page = request.args.get('page', 1, type=int)

    notifs = NotificacaoSocial.query.filter_by(user_id=current_user.id)\
                                     .order_by(desc(NotificacaoSocial.data_criacao))\
                                     .paginate(page=page, per_page=30, error_out=False)

    NotificacaoSocial.query.filter_by(user_id=current_user.id, lida=False)\
                            .update({'lida': True})
    db.session.commit()

    return render_template('helpzone/notificacoes.html', notificacoes=notifs)


# ==================== API - FEED JSON ====================
@helpzone_bp.route('/api/feed')
@login_required
def api_feed():
    tipo = request.args.get('tipo', 'recentes')
    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = Post.query.filter_by(ativo=True)

    if tipo == 'seguindo':
        seguindo_ids = [s.seguido_id for s in current_user.seguindo.all()]
        query = query.filter(Post.user_id.in_(seguindo_ids))
    elif tipo == 'populares':
        data_limite = datetime.utcnow() - timedelta(days=7)
        query = query.filter(Post.data_criacao >= data_limite)
        query = query.order_by(desc(Post.total_likes))

    query = query.order_by(desc(Post.data_criacao))
    posts = query.paginate(page=page, per_page=per_page, error_out=False)

    # URLs já vêm do banco com caminho completo — sem necessidade de apply_post_media
    return jsonify({
        'posts': [post.to_dict() for post in posts.items],
        'total': posts.total,
        'page': posts.page,
        'pages': posts.pages,
        'has_next': posts.has_next
    })


# ==================== DELETAR POST ====================
@helpzone_bp.route('/api/post/<int:post_id>/delete', methods=['POST'])
@login_required
def deletar_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.user_id != current_user.id:
        return jsonify({'error': 'Você não pode deletar este post'}), 403

    post.ativo = False

    perfil = PerfilSocial.query.filter_by(user_id=current_user.id).first()
    if perfil:
        perfil.total_posts = max(0, perfil.total_posts - 1)

    db.session.commit()

    return jsonify({'success': True})


# ==================== BUSCAR USUÁRIOS ====================
@helpzone_bp.route('/buscar', methods=['GET'])
@login_required
def buscar_usuarios():
    from app.models.user import User

    query = request.args.get('q', '').strip()
    tipo = request.args.get('tipo', 'pessoas')
    page = request.args.get('page', 1, type=int)
    per_page = 20

    current_app.logger.info(f"[BUSCA] Query: '{query}', Tipo: '{tipo}', Page: {page}")

    usuarios = None
    posts = None
    hashtags = None

    seguindo_ids = {s.seguido_id for s in current_user.seguindo.all()}

    if tipo == 'pessoas':
        if query:
            usuarios = User.query.filter(
                User.nome_completo.ilike(f'%{query}%'),
                User.id != current_user.id,
                User.is_active == True
            ).paginate(page=page, per_page=per_page, error_out=False)
        else:
            usuarios = User.query.join(PerfilSocial).filter(
                User.id != current_user.id,
                User.is_active == True
            ).order_by(
                PerfilSocial.score_social.desc()
            ).paginate(page=page, per_page=per_page, error_out=False)

    elif tipo == 'posts':
        if query:
            if query.startswith('#'):
                tag = query[1:].lower()
                posts = Post.query.join(
                    post_hashtags, Post.id == post_hashtags.c.post_id
                ).join(
                    Hashtag, Hashtag.id == post_hashtags.c.hashtag_id
                ).filter(
                    Hashtag.tag == tag,
                    Post.ativo == True
                ).order_by(Post.data_criacao.desc())\
                 .paginate(page=page, per_page=per_page, error_out=False)
            else:
                posts = Post.query.filter(
                    Post.texto.ilike(f'%{query}%'),
                    Post.ativo == True
                ).order_by(Post.data_criacao.desc())\
                 .paginate(page=page, per_page=per_page, error_out=False)
        else:
            posts = Post.query.filter(
                Post.ativo == True
            ).order_by(
                Post.total_likes.desc(),
                Post.data_criacao.desc()
            ).paginate(page=page, per_page=per_page, error_out=False)

    elif tipo == 'hashtags':
        if query:
            tag_busca = query[1:] if query.startswith('#') else query
            tag_busca = tag_busca.lower()
            hashtags = Hashtag.query.filter(
                Hashtag.tag.ilike(f'%{tag_busca}%')
            ).order_by(
                Hashtag.uso_ultima_semana.desc(),
                Hashtag.total_uso.desc()
            ).paginate(page=page, per_page=per_page, error_out=False)
        else:
            hashtags = Hashtag.query.filter(
                Hashtag.uso_ultima_semana > 0
            ).order_by(
                Hashtag.uso_ultima_semana.desc(),
                Hashtag.total_uso.desc()
            ).paginate(page=page, per_page=per_page, error_out=False)

    hashtags_em_alta = Hashtag.query.filter(
        Hashtag.uso_ultima_semana > 0
    ).order_by(
        Hashtag.uso_ultima_semana.desc()
    ).limit(10).all()

    return render_template(
        'helpzone/buscar.html',
        query=query,
        tipo=tipo,
        usuarios=usuarios,
        posts=posts,
        hashtags=hashtags,
        seguindo_ids=seguindo_ids,
        hashtags_em_alta=hashtags_em_alta
    )


# ==================== DETALHES DE UM POST ====================
@helpzone_bp.route('/post/<int:post_id>')
@login_required
def detalhes_post(post_id):
    post = Post.query.get_or_404(post_id)

    comentarios = PostComentario.query.filter_by(post_id=post_id, ativo=True)\
                                       .order_by(desc(PostComentario.data_criacao))\
                                       .all()

    return render_template(
        'helpzone/detalhes_post.html',
        post=post,
        comentarios=comentarios
    )


# ==================== ESTATÍSTICAS ====================
@helpzone_bp.route('/estatisticas')
@login_required
def estatisticas():
    perfil = PerfilSocial.query.filter_by(user_id=current_user.id).first()

    top_posts = Post.query.filter_by(user_id=current_user.id, ativo=True)\
                          .order_by(desc(Post.total_likes))\
                          .limit(5)\
                          .all()

    data_limite = datetime.utcnow() - timedelta(days=30)
    novos_seguidores = Seguidor.query.filter(
        Seguidor.seguido_id == current_user.id,
        Seguidor.data_inicio >= data_limite
    ).count()

    return render_template(
        'helpzone/estatisticas.html',
        perfil=perfil,
        top_posts=top_posts,
        novos_seguidores=novos_seguidores
    )


# ==================== API - SUGESTÕES DE USUÁRIOS ====================
@helpzone_bp.route('/api/sugestoes')
@login_required
def sugestoes_usuarios():
    from app.models.user import User

    seguindo_ids = [s.seguido_id for s in current_user.seguindo.all()]
    seguindo_ids.append(current_user.id)

    amigos_de_amigos = db.session.query(User)\
        .join(Seguidor, Seguidor.seguido_id == User.id)\
        .filter(
            Seguidor.seguidor_id.in_(seguindo_ids),
            ~User.id.in_(seguindo_ids)
        )\
        .group_by(User.id)\
        .order_by(func.count(Seguidor.id).desc())\
        .limit(3)\
        .all()

    if len(amigos_de_amigos) < 5:
        usuarios_ativos = User.query\
            .join(PerfilSocial)\
            .filter(~User.id.in_(seguindo_ids))\
            .order_by(desc(PerfilSocial.score_social))\
            .limit(5 - len(amigos_de_amigos))\
            .all()

        amigos_de_amigos.extend(usuarios_ativos)

    # URLs de foto já vêm do banco com caminho completo — sem apply_profile_media
    return jsonify({
        'success': True,
        'usuarios': [{
            'id': u.id,
            'nome': u.nome_completo,
            'foto': u.perfil_social.foto_perfil if u.perfil_social else None,
            'ocupacao': u.perfil_social.ocupacao if u.perfil_social else 'Estudante',
            'seguidores': u.perfil_social.total_seguidores if u.perfil_social else 0,
            'bio': u.perfil_social.biografia[:50] + '...' if u.perfil_social and u.perfil_social.biografia else None
        } for u in amigos_de_amigos]
    })


# ==================== DENUNCIAR POST ====================
@helpzone_bp.route('/api/post/<int:post_id>/report', methods=['POST'])
@login_required
def denunciar_post(post_id):
    post = Post.query.get_or_404(post_id)
    motivo = request.json.get('motivo', '5')

    motivos_map = {
        '1': 'Conteúdo impróprio',
        '2': 'Spam',
        '3': 'Assédio',
        '4': 'Informação falsa',
        '5': 'Outro'
    }

    motivo_texto = motivos_map.get(motivo, 'Outro')

    denuncia = DenunciaPost(
        post_id=post_id,
        user_id=current_user.id,
        motivo=motivo_texto,
        data_criacao=datetime.utcnow()
    )
    db.session.add(denuncia)

    total_denuncias = DenunciaPost.query.filter_by(post_id=post_id).count()
    if total_denuncias >= 3:
        post.requer_revisao = True

    db.session.commit()

    return jsonify({
        'success': True,
        'mensagem': 'Denúncia registrada. Obrigado por manter nossa comunidade segura!'
    })


# ==================== EDITAR POST ====================
@helpzone_bp.route('/api/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def editar_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.user_id != current_user.id:
        return jsonify({'error': 'Você não pode editar este post'}), 403

    if request.method == 'POST':
        novo_texto = request.json.get('texto', '').strip()

        if not novo_texto:
            return jsonify({'error': 'Texto não pode estar vazio'}), 400

        post.texto = novo_texto
        post.data_atualizacao = datetime.utcnow()
        post.editado = True

        db.session.commit()

        return jsonify({
            'success': True,
            'texto': novo_texto,
            'data_atualizacao': post.data_atualizacao.strftime('%d/%m/%Y %H:%M')
        })

    return jsonify({
        'texto': post.texto,
        'tipo_midia': post.tipo_midia
    })


# ==================== STORIES - GET ====================
@helpzone_bp.route('/api/stories')
@login_required
def get_stories():
    data_limite = datetime.utcnow() - timedelta(hours=24)

    seguindo_ids = [s.seguido_id for s in current_user.seguindo.all()]
    seguindo_ids.append(current_user.id)

    stories = Story.query.filter(
        Story.user_id.in_(seguindo_ids),
        Story.data_criacao >= data_limite,
        Story.ativo == True
    ).order_by(desc(Story.data_criacao)).all()

    # Agrupar por usuário
    # URLs de foto já vêm do banco com caminho completo — sem apply_profile_media
    stories_por_usuario = {}
    for story in stories:
        if story.user_id not in stories_por_usuario:
            stories_por_usuario[story.user_id] = {
                'user_id': story.user_id,
                'username': story.user.nome_completo,
                'avatar': story.user.perfil_social.foto_perfil if story.user.perfil_social else None,
                'stories': [],
                'visto': False
            }

        stories_por_usuario[story.user_id]['stories'].append({
            'id': story.id,
            'tipo': story.tipo,
            'url': story.url_midia,
            'data_criacao': story.data_criacao.isoformat(),
            'visualizacoes': story.visualizacoes
        })

    return jsonify({
        'success': True,
        'stories': list(stories_por_usuario.values())
    })


# ==================== CRIAR STORY → S3 ====================
@helpzone_bp.route('/criar-story', methods=['GET', 'POST'])
@login_required
def criar_story():
    """
    Criar um novo story (disponível por 24h)
    GET: Renderiza página de criação
    POST: Processa upload do story → S3
    """
    if request.method == 'GET':
        return render_template('helpzone/criar_story.html')

    # POST - Processar upload
    arquivo = request.files.get('arquivo')

    if not arquivo or not arquivo.filename:
        return jsonify({'error': 'Arquivo obrigatório', 'success': False}), 400

    # Determinar tipo
    if arquivo.mimetype.startswith('image'):
        tipo = 'imagem'
        media_type = 'image'
        max_size = 5 * 1024 * 1024   # 5MB
        allowed_exts = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    elif arquivo.mimetype.startswith('video'):
        tipo = 'video'
        media_type = 'video'
        max_size = 10 * 1024 * 1024  # 10MB
        allowed_exts = {'mp4', 'webm', 'mov'}
    else:
        return jsonify({'error': 'Formato não suportado', 'success': False}), 400

    # Validar extensão
    ext = arquivo.filename.rsplit('.', 1)[1].lower() if '.' in arquivo.filename else ''
    if ext not in allowed_exts:
        return jsonify({'error': f'Extensão .{ext} não permitida', 'success': False}), 400

    # Validar tamanho
    arquivo.seek(0, os.SEEK_END)
    file_size = arquivo.tell()
    arquivo.seek(0)
    if file_size > max_size:
        max_mb = max_size / (1024 * 1024)
        return jsonify({'error': f'Arquivo muito grande. Máximo: {max_mb:.0f}MB', 'success': False}), 400

    try:
        from app.services.s3_service import upload_helpzone_media

        # folder SEM user_id (a função adiciona /{user_id}/ internamente)
        # folder começa com static/uploads/ para bater com proxy_pass do Nginx
        key, error = upload_helpzone_media(
            arquivo,
            current_user.id,
            media_type,
            folder="static/uploads/helpzone/stories"
        )
        # key resultante: static/uploads/helpzone/stories/{user_id}/uuid.ext

        if error:
            current_app.logger.error(f"Erro S3 ao criar story: {error}")
            return jsonify({'error': 'Erro ao fazer upload', 'success': False}), 500

        # URL = /key → Nginx faz proxy_pass para o S3
        midia_url = f"/{key}"

        from app.models.helpzone_social import Story
        story = Story(
            user_id=current_user.id,
            tipo=tipo,
            url_midia=midia_url,
            expira_em=datetime.utcnow() + timedelta(hours=24),
            ativo=True
        )
        db.session.add(story)
        db.session.commit()

        current_app.logger.info(f"Story {story.id} criado por usuário {current_user.id} → {midia_url}")

        return jsonify({
            'success': True,
            'story_id': story.id,
            'url': midia_url,
            'expira_em': story.expira_em.isoformat()
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar story: {str(e)}")
        return jsonify({'error': 'Erro ao processar arquivo', 'success': False}), 500


# ==================== VISUALIZAR STORY ====================
@helpzone_bp.route('/api/story/<int:story_id>/view', methods=['POST'])
@login_required
def visualizar_story(story_id):
    story = Story.query.get_or_404(story_id)

    story.visualizacoes += 1

    visualizacao = StoryVisualizacao.query.filter_by(
        story_id=story_id,
        user_id=current_user.id
    ).first()

    if not visualizacao:
        visualizacao = StoryVisualizacao(
            story_id=story_id,
            user_id=current_user.id
        )
        db.session.add(visualizacao)

    db.session.commit()

    return jsonify({'success': True})


# ==================== REELS ====================
@helpzone_bp.route('/reels')
@login_required
def reels():
    page = request.args.get('page', 1, type=int)

    reels = Post.query.filter_by(
        ativo=True,
        tipo_midia='video'
    ).order_by(desc(Post.data_criacao))\
     .paginate(page=page, per_page=10, error_out=False)

    return render_template('helpzone/reels.html', reels=reels)


# ==================== ANALYTICS DE POSTS ====================
@helpzone_bp.route('/api/post/<int:post_id>/analytics')
@login_required
def analytics_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.user_id != current_user.id:
        return jsonify({'error': 'Acesso negado'}), 403

    likes_por_dia = db.session.query(
        func.date(PostLike.data_criacao).label('data'),
        func.count(PostLike.id).label('total')
    ).filter(
        PostLike.post_id == post_id,
        PostLike.tipo == 'like'
    ).group_by(func.date(PostLike.data_criacao)).all()

    comentarios_por_dia = db.session.query(
        func.date(PostComentario.data_criacao).label('data'),
        func.count(PostComentario.id).label('total')
    ).filter(
        PostComentario.post_id == post_id
    ).group_by(func.date(PostComentario.data_criacao)).all()

    return jsonify({
        'success': True,
        'post_id': post_id,
        'total_likes': post.total_likes,
        'total_comentarios': post.total_comentarios,
        'total_salvamentos': PostSalvo.query.filter_by(post_id=post_id).count(),
        'alcance': post.total_likes + post.total_comentarios * 2,
        'engajamento_taxa': round(
            (post.total_likes + post.total_comentarios) /
            max(post.user.perfil_social.total_seguidores, 1) * 100, 2
        ),
        'likes_por_dia': [{'data': str(item.data), 'total': item.total} for item in likes_por_dia],
        'comentarios_por_dia': [{'data': str(item.data), 'total': item.total} for item in comentarios_por_dia]
    })


# ==================== API PARA MODAL DE COMENTÁRIOS ====================
@helpzone_bp.route('/api/post/<int:post_id>/detalhes', methods=['GET'])
@login_required
def api_detalhes_post(post_id):
    post = Post.query.get_or_404(post_id)

    midia_info = None
    if post.midia:
        midia_info = {
            'tipo': post.midia.tipo,
            'url': post.midia.url
        }

    perfil = PerfilSocial.query.filter_by(user_id=post.user_id).first()
    foto_perfil = perfil.foto_perfil if perfil and perfil.foto_perfil else None

    return jsonify({
        'success': True,
        'post': {
            'id': post.id,
            'texto': post.texto,
            'user': {
                'id': post.user.id,
                'nome': post.user.nome_completo,
                'foto_perfil': foto_perfil
            },
            'midia': midia_info,
            'total_likes': post.total_likes,
            'total_comentarios': post.total_comentarios,
            'data_criacao': post.data_criacao.strftime('%d/%m/%Y às %H:%M')
        }
    })


@helpzone_bp.route('/api/post/<int:post_id>/comentarios', methods=['GET'])
@login_required
def api_comentarios_post(post_id):
    comentarios = PostComentario.query.filter_by(post_id=post_id, ativo=True)\
                                       .order_by(PostComentario.data_criacao)\
                                       .all()

    comentarios_list = []
    for c in comentarios:
        perfil = PerfilSocial.query.filter_by(user_id=c.user_id).first()
        foto_perfil = perfil.foto_perfil if perfil and perfil.foto_perfil else None

        tempo_delta = datetime.utcnow() - c.data_criacao
        if tempo_delta.days > 0:
            tempo = f"{tempo_delta.days}d"
        elif tempo_delta.seconds >= 3600:
            tempo = f"{tempo_delta.seconds // 3600}h"
        elif tempo_delta.seconds >= 60:
            tempo = f"{tempo_delta.seconds // 60}min"
        else:
            tempo = "agora"

        comentarios_list.append({
            'id': c.id,
            'texto': c.texto,
            'user': {
                'id': c.user.id,
                'nome': c.user.nome_completo,
                'foto_perfil': foto_perfil
            },
            'tempo': tempo,
            'is_owner': c.user_id == current_user.id,
            'total_likes': getattr(c, 'total_likes', 0)
        })

    return jsonify({
        'success': True,
        'comentarios': comentarios_list
    })


@helpzone_bp.route('/api/post/<int:post_id>/comentar', methods=['POST'])
@login_required
def api_comentar_post(post_id):
    post = Post.query.get_or_404(post_id)

    data = request.get_json()
    texto = data.get('texto', '').strip()

    if not texto:
        return jsonify({'error': 'Comentário não pode estar vazio'}), 400

    comentario = PostComentario(
        post_id=post_id,
        user_id=current_user.id,
        texto=texto
    )
    db.session.add(comentario)

    post.total_comentarios += 1

    if post.user_id != current_user.id:
        notif = NotificacaoSocial(
            user_id=post.user_id,
            origem_user_id=current_user.id,
            tipo='comentario',
            post_id=post_id,
            mensagem=f'{current_user.nome_completo} comentou em seu post'
        )
        db.session.add(notif)

    db.session.commit()

    return jsonify({
        'success': True,
        'comentario': {
            'id': comentario.id,
            'texto': comentario.texto,
            'tempo': 'agora'
        }
    })
