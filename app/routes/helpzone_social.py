# app/routes/helpzone_social.py
"""
Blueprint do HelpZone Social
Sistema de feed social focado em rotina de estudos com armazenamento em S3
"""

from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from app.models.helpzone_social import (
    Post, PostMidia, PostLike, PostComentario, 
    Story, StoryVisualizacao, Seguidor, PerfilSocial,
    NotificacaoSocial, PostSalvo
)
from app.services import s3_service
import logging

logger = logging.getLogger(__name__)

helpzone_social_bp = Blueprint('helpzone_social', __name__, url_prefix='/helpzone')


# ==================== FEED ====================
@helpzone_social_bp.route('/feed')
@login_required
def feed():
    """Exibe o feed social com posts dos usuários seguidos"""
    try:
        # Obter IDs dos usuários seguidos
        seguindo_ids = [s.seguido_id for s in current_user.seguindo.all()]
        seguindo_ids.append(current_user.id)  # Incluir próprios posts
        
        # Buscar posts recentes
        posts = Post.query.filter(
            Post.user_id.in_(seguindo_ids),
            Post.ativo == True
        ).order_by(Post.data_criacao.desc()).limit(50).all()
        
        # Gerar URLs presigned para as mídias
        for post in posts:
            if post.midia and post.midia.s3_key:
                post.midia.url_temporaria = s3_service.presigned_get_url(post.midia.s3_key, expires=7200)
        
        # Buscar stories ativos (últimas 24h)
        data_limite = datetime.utcnow() - timedelta(hours=24)
        stories = Story.query.filter(
            Story.user_id.in_(seguindo_ids),
            Story.ativo == True,
            Story.data_criacao >= data_limite
        ).order_by(Story.data_criacao.desc()).all()
        
        # Gerar URLs presigned para stories
        for story in stories:
            if story.s3_key:
                story.url_temporaria = s3_service.presigned_get_url(story.s3_key, expires=7200)
        
        return render_template('helpzone_social/feed.html', 
                             posts=posts, 
                             stories=stories)
    
    except Exception as e:
        logger.error(f"Erro ao carregar feed: {str(e)}")
        flash("Erro ao carregar o feed. Tente novamente.", "danger")
        return redirect(url_for('dashboard.index'))


# ==================== CRIAR POST ====================
@helpzone_social_bp.route('/post/criar', methods=['GET', 'POST'])
@login_required
def criar_post():
    """Cria novo post com ou sem mídia"""
    if request.method == 'GET':
        return render_template('helpzone_social/criar_post.html')
    
    try:
        texto = request.form.get('texto', '').strip()
        
        # Validar que tem pelo menos texto ou mídia
        tem_midia = 'midia' in request.files and request.files['midia'].filename
        
        if not texto and not tem_midia:
            return jsonify({
                'success': False,
                'message': 'Post deve ter texto ou mídia'
            }), 400
        
        # Criar post
        post = Post(
            user_id=current_user.id,
            texto=texto,
            tipo_midia='texto'  # Será atualizado se houver mídia
        )
        
        db.session.add(post)
        db.session.flush()  # Para obter o ID do post
        
        # Processar mídia se houver
        if tem_midia:
            file = request.files['midia']
            
            # Detectar tipo de mídia
            mimetype = file.mimetype
            if mimetype.startswith('image/'):
                media_type = 'image'
                post.tipo_midia = 'imagem'
                folder = 'helpzone/posts/images'
            elif mimetype.startswith('video/'):
                media_type = 'video'
                post.tipo_midia = 'video'
                folder = 'helpzone/posts/videos'
            else:
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'message': 'Tipo de arquivo não suportado'
                }), 400
            
            # Upload para S3
            s3_key, error = s3_service.upload_helpzone_media(
                file, 
                current_user.id, 
                media_type,
                folder=folder
            )
            
            if error:
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'message': f'Erro no upload: {error}'
                }), 500
            
            # Criar registro de mídia
            midia = PostMidia(
                post_id=post.id,
                tipo=media_type,
                s3_key=s3_key,
                tamanho_bytes=0  # Poderia calcular se necessário
            )
            db.session.add(midia)
        
        # Processar hashtags
        post.processar_hashtags()
        
        # Atualizar perfil social
        perfil = PerfilSocial.query.filter_by(user_id=current_user.id).first()
        if not perfil:
            perfil = PerfilSocial(user_id=current_user.id)
            db.session.add(perfil)
        
        perfil.total_posts += 1
        perfil.ultima_postagem = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Post {post.id} criado com sucesso por usuário {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Post criado com sucesso!',
            'post_id': post.id
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar post: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao criar post. Tente novamente.'
        }), 500


# ==================== CRIAR STORY ====================
@helpzone_social_bp.route('/story/criar', methods=['GET', 'POST'])
@login_required
def criar_story():
    """Cria novo story (imagem ou vídeo curto)"""
    if request.method == 'GET':
        return render_template('helpzone_social/criar_story.html')
    
    try:
        # Story DEVE ter mídia
        if 'midia' not in request.files or not request.files['midia'].filename:
            return jsonify({
                'success': False,
                'message': 'Story deve ter uma imagem ou vídeo'
            }), 400
        
        file = request.files['midia']
        
        # Detectar tipo de mídia
        mimetype = file.mimetype
        if mimetype.startswith('image/'):
            media_type = 'image'
            tipo_story = 'imagem'
            folder = 'helpzone/stories/images'
        elif mimetype.startswith('video/'):
            media_type = 'video'
            tipo_story = 'video'
            folder = 'helpzone/stories/videos'
        else:
            return jsonify({
                'success': False,
                'message': 'Story deve ser imagem ou vídeo'
            }), 400
        
        # Upload para S3
        s3_key, error = s3_service.upload_helpzone_media(
            file,
            current_user.id,
            media_type,
            folder=folder
        )
        
        if error:
            return jsonify({
                'success': False,
                'message': f'Erro no upload: {error}'
            }), 500
        
        # Criar story (expira em 24h)
        story = Story(
            user_id=current_user.id,
            tipo=tipo_story,
            s3_key=s3_key,
            expira_em=datetime.utcnow() + timedelta(hours=24)
        )
        
        db.session.add(story)
        db.session.commit()
        
        logger.info(f"Story {story.id} criado com sucesso por usuário {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Story criado com sucesso!',
            'story_id': story.id
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar story: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao criar story. Tente novamente.'
        }), 500


# ==================== DELETAR POST ====================
@helpzone_social_bp.route('/post/<int:post_id>/deletar', methods=['POST'])
@login_required
def deletar_post(post_id):
    """Deleta um post (apenas o próprio autor pode deletar)"""
    try:
        post = Post.query.get_or_404(post_id)
        
        # Verificar permissão
        if post.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Você não tem permissão para deletar este post'
            }), 403
        
        # Remover mídia do S3 se houver
        if post.midia and post.midia.s3_key:
            success, error = s3_service.delete_media(post.midia.s3_key)
            if not success:
                logger.warning(f"Erro ao deletar mídia do S3: {error}")
        
        # Soft delete do post
        post.ativo = False
        
        # Atualizar contador do perfil
        perfil = PerfilSocial.query.filter_by(user_id=current_user.id).first()
        if perfil and perfil.total_posts > 0:
            perfil.total_posts -= 1
        
        db.session.commit()
        
        logger.info(f"Post {post_id} deletado por usuário {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Post deletado com sucesso'
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao deletar post {post_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao deletar post'
        }), 500


# ==================== LIKES ====================
@helpzone_social_bp.route('/post/<int:post_id>/like', methods=['POST'])
@login_required
def toggle_like(post_id):
    """Toggle like/dislike em um post"""
    try:
        post = Post.query.get_or_404(post_id)
        tipo = request.json.get('tipo', 'like')  # 'like' ou 'dislike'
        
        # Verificar se já existe
        existing = PostLike.query.filter_by(
            post_id=post_id,
            user_id=current_user.id
        ).first()
        
        if existing:
            # Se é do mesmo tipo, remover
            if existing.tipo == tipo:
                db.session.delete(existing)
                
                # Atualizar contador
                if tipo == 'like':
                    post.total_likes = max(0, post.total_likes - 1)
                else:
                    post.total_dislikes = max(0, post.total_dislikes - 1)
                
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'action': 'removed',
                    'total_likes': post.total_likes,
                    'total_dislikes': post.total_dislikes
                })
            else:
                # Trocar tipo
                old_tipo = existing.tipo
                existing.tipo = tipo
                
                # Atualizar contadores
                if old_tipo == 'like':
                    post.total_likes = max(0, post.total_likes - 1)
                    post.total_dislikes += 1
                else:
                    post.total_dislikes = max(0, post.total_dislikes - 1)
                    post.total_likes += 1
                
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'action': 'changed',
                    'total_likes': post.total_likes,
                    'total_dislikes': post.total_dislikes
                })
        else:
            # Criar novo
            like = PostLike(
                post_id=post_id,
                user_id=current_user.id,
                tipo=tipo
            )
            db.session.add(like)
            
            # Atualizar contador
            if tipo == 'like':
                post.total_likes += 1
            else:
                post.total_dislikes += 1
            
            db.session.commit()
            
            # Criar notificação para o autor do post (se não for ele mesmo)
            if post.user_id != current_user.id and tipo == 'like':
                notif = NotificacaoSocial(
                    user_id=post.user_id,
                    origem_user_id=current_user.id,
                    tipo='like',
                    post_id=post_id,
                    mensagem=f'{current_user.nome} curtiu seu post'
                )
                db.session.add(notif)
                db.session.commit()
            
            return jsonify({
                'success': True,
                'action': 'added',
                'total_likes': post.total_likes,
                'total_dislikes': post.total_dislikes
            })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao processar like no post {post_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao processar like'
        }), 500


# ==================== COMENTÁRIOS ====================
@helpzone_social_bp.route('/post/<int:post_id>/comentar', methods=['POST'])
@login_required
def comentar_post(post_id):
    """Adiciona comentário em um post"""
    try:
        post = Post.query.get_or_404(post_id)
        texto = request.json.get('texto', '').strip()
        
        if not texto:
            return jsonify({
                'success': False,
                'message': 'Comentário não pode ser vazio'
            }), 400
        
        # Criar comentário
        comentario = PostComentario(
            post_id=post_id,
            user_id=current_user.id,
            texto=texto
        )
        db.session.add(comentario)
        
        # Atualizar contador
        post.total_comentarios += 1
        
        db.session.commit()
        
        # Criar notificação para o autor do post
        if post.user_id != current_user.id:
            notif = NotificacaoSocial(
                user_id=post.user_id,
                origem_user_id=current_user.id,
                tipo='comentario',
                post_id=post_id,
                mensagem=f'{current_user.nome} comentou em seu post'
            )
            db.session.add(notif)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Comentário adicionado',
            'comentario': {
                'id': comentario.id,
                'texto': comentario.texto,
                'user_nome': current_user.nome,
                'data_criacao': comentario.data_criacao.isoformat()
            }
        })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao comentar post {post_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao adicionar comentário'
        }), 500


# ==================== VISUALIZAR POST ====================
@helpzone_social_bp.route('/post/<int:post_id>')
@login_required
def ver_post(post_id):
    """Visualiza um post específico com todos os comentários"""
    try:
        post = Post.query.get_or_404(post_id)
        
        # Gerar URL presigned para mídia
        if post.midia and post.midia.s3_key:
            post.midia.url_temporaria = s3_service.presigned_get_url(post.midia.s3_key, expires=7200)
        
        # Buscar comentários
        comentarios = PostComentario.query.filter_by(post_id=post_id)\
            .order_by(PostComentario.data_criacao.desc()).all()
        
        return render_template('helpzone_social/detalhes_post.html',
                             post=post,
                             comentarios=comentarios)
    
    except Exception as e:
        logger.error(f"Erro ao visualizar post {post_id}: {str(e)}")
        flash("Erro ao carregar post", "danger")
        return redirect(url_for('helpzone_social.feed'))


# ==================== PERFIL PÚBLICO ====================
@helpzone_social_bp.route('/perfil/<int:user_id>')
@login_required
def ver_perfil(user_id):
    """Visualiza perfil público de um usuário"""
    try:
        from app.models.user import User
        user = User.query.get_or_404(user_id)
        
        # Buscar posts do usuário
        posts = Post.query.filter_by(user_id=user_id, ativo=True)\
            .order_by(Post.data_criacao.desc()).limit(20).all()
        
        # Gerar URLs presigned
        for post in posts:
            if post.midia and post.midia.s3_key:
                post.midia.url_temporaria = s3_service.presigned_get_url(post.midia.s3_key, expires=7200)
        
        # Buscar ou criar perfil social
        perfil = PerfilSocial.query.filter_by(user_id=user_id).first()
        if not perfil:
            perfil = PerfilSocial(user_id=user_id)
            db.session.add(perfil)
            db.session.commit()
        
        # Verificar se está seguindo
        seguindo = Seguidor.query.filter_by(
            seguidor_id=current_user.id,
            seguido_id=user_id
        ).first() is not None
        
        return render_template('helpzone_social/user_profile.html',
                             user=user,
                             perfil=perfil,
                             posts=posts,
                             seguindo=seguindo)
    
    except Exception as e:
        logger.error(f"Erro ao visualizar perfil {user_id}: {str(e)}")
        flash("Erro ao carregar perfil", "danger")
        return redirect(url_for('helpzone_social.feed'))


# ==================== SEGUIR/DEIXAR DE SEGUIR ====================
@helpzone_social_bp.route('/usuario/<int:user_id>/seguir', methods=['POST'])
@login_required
def toggle_seguir(user_id):
    """Toggle seguir/deixar de seguir um usuário"""
    try:
        if user_id == current_user.id:
            return jsonify({
                'success': False,
                'message': 'Você não pode seguir a si mesmo'
            }), 400
        
        # Verificar se já segue
        seguindo = Seguidor.query.filter_by(
            seguidor_id=current_user.id,
            seguido_id=user_id
        ).first()
        
        if seguindo:
            # Deixar de seguir
            db.session.delete(seguindo)
            
            # Atualizar contadores
            perfil_seguidor = PerfilSocial.query.filter_by(user_id=current_user.id).first()
            perfil_seguido = PerfilSocial.query.filter_by(user_id=user_id).first()
            
            if perfil_seguidor:
                perfil_seguidor.total_seguindo = max(0, perfil_seguidor.total_seguindo - 1)
            if perfil_seguido:
                perfil_seguido.total_seguidores = max(0, perfil_seguido.total_seguidores - 1)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'action': 'unfollowed',
                'message': 'Você deixou de seguir este usuário'
            })
        else:
            # Seguir
            novo_seguidor = Seguidor(
                seguidor_id=current_user.id,
                seguido_id=user_id
            )
            db.session.add(novo_seguidor)
            
            # Atualizar contadores
            perfil_seguidor = PerfilSocial.query.filter_by(user_id=current_user.id).first()
            perfil_seguido = PerfilSocial.query.filter_by(user_id=user_id).first()
            
            if not perfil_seguidor:
                perfil_seguidor = PerfilSocial(user_id=current_user.id)
                db.session.add(perfil_seguidor)
            
            if not perfil_seguido:
                perfil_seguido = PerfilSocial(user_id=user_id)
                db.session.add(perfil_seguido)
            
            perfil_seguidor.total_seguindo += 1
            perfil_seguido.total_seguidores += 1
            
            db.session.commit()
            
            # Criar notificação
            notif = NotificacaoSocial(
                user_id=user_id,
                origem_user_id=current_user.id,
                tipo='follow',
                mensagem=f'{current_user.nome} começou a seguir você'
            )
            db.session.add(notif)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'action': 'followed',
                'message': 'Você está seguindo este usuário'
            })
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao processar seguir/deixar de seguir usuário {user_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro ao processar ação'
        }), 500
