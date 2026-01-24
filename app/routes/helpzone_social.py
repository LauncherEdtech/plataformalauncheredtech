# app/routes/helpzone_social.py
"""
Rotas do HelpZone como Feed Social de Estudos
Sistema completo de rede social focada em rotina de estudos
"""

import os
import uuid
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import desc, or_, and_, func
from app import db
from app.models.helpzone_social import (
    Post, PostMidia, PostLike, PostComentario, 
    Seguidor, NotificacaoSocial, PerfilSocial, Desafio
)

helpzone_bp = Blueprint('helpzone', __name__, url_prefix='/helpzone')

# ==================== CONFIGURAÇÕES DE UPLOAD ====================
UPLOAD_FOLDER = 'static/uploads/helpzone'
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'mov'}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
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
        # Posts de quem eu sigo
        seguindo_ids = [s.seguido_id for s in current_user.seguindo.all()]
        query = query.filter(Post.user_id.in_(seguindo_ids))
        query = query.order_by(desc(Post.data_criacao))
        
    elif tipo_feed == 'populares':
        # Posts mais curtidos nas últimas 7 dias
        data_limite = datetime.utcnow() - timedelta(days=7)
        query = query.filter(Post.data_criacao >= data_limite)
        query = query.order_by(desc(Post.total_likes), desc(Post.data_criacao))
        
    else:  # recentes
        # Todos os posts recentes
        query = query.order_by(desc(Post.data_criacao))
    
    # Paginação
    posts = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Estatísticas do usuário
    stats = {
        'total_posts': perfil.total_posts,
        'seguidores': perfil.total_seguidores,
        'seguindo': perfil.total_seguindo,
        'likes_recebidos': perfil.total_likes_recebidos,
        'nivel': perfil.nivel_influencia
    }
    
    # Notificações não lidas
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


# ==================== CRIAR POST (COM EXTRAÇÃO DE HASHTAGS) ====================
@helpzone_bp.route('/criar-post', methods=['GET', 'POST'])
@login_required
def criar_post():
    """
    Página para criar um novo post
    Aceita texto, imagem ou vídeo
    EXTRAI AUTOMATICAMENTE HASHTAGS DO TEXTO
    """
    if request.method == 'POST':
        texto = request.form.get('texto', '').strip()
        tipo_midia = request.form.get('tipo_midia', 'texto')
        
        # Validação básica
        if not texto and 'arquivo' not in request.files:
            return jsonify({'error': 'Post deve ter texto ou mídia'}), 400
        
        # Criar post
        post = Post(
            user_id=current_user.id,
            texto=texto,
            tipo_midia=tipo_midia
        )
        db.session.add(post)
        db.session.flush()  # Para obter o ID do post
        
        # =====================================================
        # EXTRAÇÃO E PROCESSAMENTO DE HASHTAGS (NOVO!)
        # =====================================================
        if texto:
            # Extrair hashtags do texto usando regex
            import re
            pattern = r'#([a-záéíóúàâêôãõçA-ZÁÉÍÓÚÀÂÊÔÃÕÇ0-9_]+)'
            hashtags_encontradas = re.findall(pattern, texto)
            
            # Normalizar e remover duplicatas
            hashtags_unicas = list(set([tag.lower() for tag in hashtags_encontradas]))
            
            # Processar cada hashtag
            for tag_nome in hashtags_unicas:
                # Buscar ou criar hashtag
                hashtag = Hashtag.query.filter_by(tag=tag_nome).first()
                
                if not hashtag:
                    # Criar nova hashtag
                    hashtag = Hashtag(
                        tag=tag_nome,
                        total_uso=1,
                        ultimo_uso=datetime.utcnow()
                    )
                    db.session.add(hashtag)
                    db.session.flush()  # Para obter o ID
                else:
                    # Atualizar hashtag existente
                    hashtag.total_uso += 1
                    hashtag.ultimo_uso = datetime.utcnow()
                
                # Criar associação post-hashtag
                db.session.execute(
                    post_hashtags.insert().values(
                        post_id=post.id,
                        hashtag_id=hashtag.id,
                        data_criacao=datetime.utcnow()
                    )
                )
            
            # Log de hashtags extraídas
            if hashtags_unicas:
                current_app.logger.info(
                    f"[HASHTAGS] Post {post.id}: extraídas {len(hashtags_unicas)} hashtags: {', '.join(hashtags_unicas)}"
                )
        
        # =====================================================
        # UPLOAD DE MÍDIA (se houver)
        # =====================================================
        if 'arquivo' in request.files:
            arquivo = request.files['arquivo']
            if arquivo and arquivo.filename:
                try:
                    midia_url = processar_upload(arquivo, tipo_midia, post.id)
                    
                    # Criar registro de mídia
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
        
        # =====================================================
        # ATUALIZAR PERFIL SOCIAL
        # =====================================================
        perfil = PerfilSocial.query.filter_by(user_id=current_user.id).first()
        if perfil:
            perfil.total_posts += 1
            perfil.ultima_postagem = datetime.utcnow()
        
        # Commit final
        db.session.commit()
        
        flash('Post criado com sucesso!', 'success')
        return redirect(url_for('helpzone.feed'))
    
    return render_template('helpzone/criar_post.html')


def processar_upload(arquivo, tipo_midia, post_id):
    """
    Processa upload de arquivo (imagem ou vídeo)
    """
    # Validar tipo de arquivo
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
        raise ValueError(f'Arquivo muito grande. Máximo: {max_size / (1024*1024)}MB')
    
    # Gerar nome único
    filename = generate_unique_filename(arquivo.filename)
    
    # Criar diretórios se não existirem
    upload_path = os.path.join(current_app.root_path, UPLOAD_FOLDER, str(current_user.id))
    os.makedirs(upload_path, exist_ok=True)
    
    # Salvar arquivo
    filepath = os.path.join(upload_path, filename)
    arquivo.save(filepath)
    
    # Retornar URL relativa
    relative_url = f"/static/uploads/helpzone/{current_user.id}/{filename}"
    return relative_url


# ==================== EDITAR POST (COM ATUALIZAÇÃO DE HASHTAGS) ====================
@helpzone_bp.route('/editar-post/<int:post_id>', methods=['POST'])
@login_required
def editar_post(post_id):
    """
    Edita um post existente
    ATUALIZA HASHTAGS AUTOMATICAMENTE
    """
    post = Post.query.get_or_404(post_id)
    
    # Verificar permissão
    if post.user_id != current_user.id:
        return jsonify({'error': 'Sem permissão para editar este post'}), 403
    
    novo_texto = request.json.get('texto', '').strip()
    
    if not novo_texto:
        return jsonify({'error': 'Texto não pode estar vazio'}), 400
    
    # =====================================================
    # REMOVER HASHTAGS ANTIGAS
    # =====================================================
    # Obter hashtags antigas do post
    hashtags_antigas = db.session.query(Hashtag).join(
        post_hashtags, Hashtag.id == post_hashtags.c.hashtag_id
    ).filter(
        post_hashtags.c.post_id == post_id
    ).all()
    
    # Deletar associações antigas
    db.session.execute(
        post_hashtags.delete().where(post_hashtags.c.post_id == post_id)
    )
    
    # Atualizar contadores das hashtags antigas
    for hashtag in hashtags_antigas:
        hashtag.total_uso = max(0, hashtag.total_uso - 1)
    
    # =====================================================
    # EXTRAIR E PROCESSAR NOVAS HASHTAGS
    # =====================================================
    import re
    pattern = r'#([a-záéíóúàâêôãõçA-ZÁÉÍÓÚÀÂÊÔÃÕÇ0-9_]+)'
    hashtags_encontradas = re.findall(pattern, novo_texto)
    hashtags_unicas = list(set([tag.lower() for tag in hashtags_encontradas]))
    
    for tag_nome in hashtags_unicas:
        # Buscar ou criar hashtag
        hashtag = Hashtag.query.filter_by(tag=tag_nome).first()
        
        if not hashtag:
            hashtag = Hashtag(
                tag=tag_nome,
                total_uso=1,
                ultimo_uso=datetime.utcnow()
            )
            db.session.add(hashtag)
            db.session.flush()
        else:
            hashtag.total_uso += 1
            hashtag.ultimo_uso = datetime.utcnow()
        
        # Criar nova associação
        db.session.execute(
            post_hashtags.insert().values(
                post_id=post_id,
                hashtag_id=hashtag.id,
                data_criacao=datetime.utcnow()
            )
        )
    
    # Atualizar texto do post
    post.texto = novo_texto
    post.data_atualizacao = datetime.utcnow()
    
    db.session.commit()
    
    current_app.logger.info(
        f"[HASHTAGS] Post {post_id} editado: {len(hashtags_unicas)} hashtags atualizadas"
    )
    
    return jsonify({
        'success': True,
        'texto': novo_texto,
        'hashtags': hashtags_unicas
    })


# ==================== LIKE/DISLIKE ====================
@helpzone_bp.route('/api/post/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    """
    Dar like em um post
    """
    post = Post.query.get_or_404(post_id)
    tipo = request.json.get('tipo', 'like')  # 'like' ou 'dislike'
    
    if tipo not in ['like', 'dislike']:
        return jsonify({'error': 'Tipo inválido'}), 400
    
    # Verificar se já existe reação
    like_existente = PostLike.query.filter_by(
        post_id=post_id,
        user_id=current_user.id
    ).first()
    
    if like_existente:
        # Se for a mesma reação, remove (toggle)
        if like_existente.tipo == tipo:
            # Atualizar contador
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
            # Trocar tipo de reação
            # Atualizar contadores
            if like_existente.tipo == 'like':
                post.total_likes = max(0, post.total_likes - 1)
                post.total_dislikes += 1
            else:
                post.total_dislikes = max(0, post.total_dislikes - 1)
                post.total_likes += 1
            
            like_existente.tipo = tipo
            like_existente.data_criacao = datetime.utcnow()
    else:
        # Criar nova reação
        novo_like = PostLike(
            post_id=post_id,
            user_id=current_user.id,
            tipo=tipo
        )
        db.session.add(novo_like)
        
        # Atualizar contador
        if tipo == 'like':
            post.total_likes += 1
        else:
            post.total_dislikes += 1
        
        # Criar notificação se for like (não para dislike)
        if tipo == 'like' and post.user_id != current_user.id:
            notif = NotificacaoSocial(
                user_id=post.user_id,
                origem_user_id=current_user.id,
                tipo='like',
                post_id=post_id,
                mensagem=f'{current_user.nome_completo} curtiu seu post'
            )
            db.session.add(notif)
            
            # Atualizar perfil social do autor
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

# ==================== SEGUIR/DEIXAR DE SEGUIR ====================
@helpzone_bp.route('/api/user/<int:user_id>/follow', methods=['POST'])
@login_required
def follow_user(user_id):
    """
    Seguir ou deixar de seguir um usuário
    """
    if user_id == current_user.id:
        return jsonify({'error': 'Você não pode seguir a si mesmo'}), 400
    
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
        # Seguir
        novo_seguidor = Seguidor(
            seguidor_id=current_user.id,
            seguido_id=user_id
        )
        db.session.add(novo_seguidor)
        
        # Atualizar contadores
        perfil_seguidor = PerfilSocial.query.filter_by(user_id=current_user.id).first()
        if perfil_seguidor:
            perfil_seguidor.total_seguindo += 1
        
        perfil_seguido = PerfilSocial.query.filter_by(user_id=user_id).first()
        if perfil_seguido:
            perfil_seguido.total_seguidores += 1
        
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
            'action': 'follow',
            'seguindo': True
        })


# ==================== PERFIL DO USUÁRIO ====================
@helpzone_bp.route('/perfil/<int:user_id>')
@login_required
def perfil_usuario(user_id):
    """
    Perfil de um usuário no feed social
    """
    from app.models.user import User
    
    usuario = User.query.get_or_404(user_id)
    perfil = PerfilSocial.query.filter_by(user_id=user_id).first()
    
    if not perfil:
        perfil = PerfilSocial(user_id=user_id)
        db.session.add(perfil)
        db.session.commit()
    
    # Posts do usuário
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(user_id=user_id, ativo=True)\
                      .order_by(desc(Post.data_criacao))\
                      .paginate(page=page, per_page=20, error_out=False)
    
    # Verificar se o usuário atual segue este perfil
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
        is_own_profile=(current_user.id == user_id)
    )


# ==================== NOTIFICAÇÕES ====================
@helpzone_bp.route('/notificacoes')
@login_required
def notificacoes():
    """
    Lista todas as notificações do usuário
    """
    page = request.args.get('page', 1, type=int)
    
    notifs = NotificacaoSocial.query.filter_by(user_id=current_user.id)\
                                     .order_by(desc(NotificacaoSocial.data_criacao))\
                                     .paginate(page=page, per_page=30, error_out=False)
    
    # Marcar todas como lidas
    NotificacaoSocial.query.filter_by(user_id=current_user.id, lida=False)\
                            .update({'lida': True})
    db.session.commit()
    
    return render_template('helpzone/notificacoes.html', notificacoes=notifs)


# ==================== API - FEED JSON ====================
@helpzone_bp.route('/api/feed')
@login_required
def api_feed():
    """
    Retorna feed em formato JSON (para carregamento dinâmico)
    """
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
    """
    Deleta um post (apenas o autor pode deletar)
    """
    post = Post.query.get_or_404(post_id)
    
    if post.user_id != current_user.id:
        return jsonify({'error': 'Você não pode deletar este post'}), 403
    
    # Marcar como inativo (soft delete)
    post.ativo = False
    
    # Atualizar perfil
    perfil = PerfilSocial.query.filter_by(user_id=current_user.id).first()
    if perfil:
        perfil.total_posts = max(0, perfil.total_posts - 1)
    
    db.session.commit()
    
    return jsonify({'success': True})


# ==================== BUSCAR USUÁRIOS ====================

# ==================== BUSCAR USUÁRIOS ====================
@helpzone_bp.route('/buscar', methods=['GET'])
@login_required
def buscar_usuarios():
    """
    Página de busca avançada com tabs:
    - Pessoas: busca por nome
    - Posts: busca por texto ou hashtag
    - Hashtags: busca por tag
    """
    query = request.args.get('q', '').strip()
    tipo = request.args.get('tipo', 'pessoas')  # pessoas, posts, hashtags
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    resultados = []
    total = 0
    
    # =====================================================
    # TAB 1: BUSCAR PESSOAS
    # =====================================================
    if tipo == 'pessoas':
        if query:
            # Buscar por nome_completo (NÃO User.nome que não existe!)
            usuarios = User.query.filter(
                User.nome_completo.ilike(f'%{query}%'),
                User.id != current_user.id,
                User.is_active == True
            ).paginate(page=page, per_page=per_page, error_out=False)
            
            resultados = [{
                'id': u.id,
                'nome': u.nome_completo,
                'username': u.username,
                'avatar': obter_avatar_url(u.id),
                'nivel': obter_nivel_usuario(u.xp_total),
                'seguidores': PerfilSocial.query.filter_by(user_id=u.id).first().total_seguidores if PerfilSocial.query.filter_by(user_id=u.id).first() else 0,
                'posts': PerfilSocial.query.filter_by(user_id=u.id).first().total_posts if PerfilSocial.query.filter_by(user_id=u.id).first() else 0,
                'seguindo': Seguidor.query.filter_by(
                    seguidor_id=current_user.id,
                    seguido_id=u.id
                ).first() is not None
            } for u in usuarios.items]
            
            total = usuarios.total
        else:
            # Sem query: mostrar usuários populares
            usuarios_populares = User.query.join(PerfilSocial).filter(
                User.id != current_user.id,
                User.is_active == True
            ).order_by(
                PerfilSocial.score_social.desc()
            ).limit(20).all()
            
            resultados = [{
                'id': u.id,
                'nome': u.nome_completo,
                'username': u.username,
                'avatar': obter_avatar_url(u.id),
                'nivel': obter_nivel_usuario(u.xp_total),
                'seguidores': PerfilSocial.query.filter_by(user_id=u.id).first().total_seguidores if PerfilSocial.query.filter_by(user_id=u.id).first() else 0,
                'posts': PerfilSocial.query.filter_by(user_id=u.id).first().total_posts if PerfilSocial.query.filter_by(user_id=u.id).first() else 0,
                'seguindo': Seguidor.query.filter_by(
                    seguidor_id=current_user.id,
                    seguido_id=u.id
                ).first() is not None
            } for u in usuarios_populares]
            
            total = len(resultados)
    
    # =====================================================
    # TAB 2: BUSCAR POSTS
    # =====================================================
    elif tipo == 'posts':
        if query:
            # Se começa com #, buscar por hashtag
            if query.startswith('#'):
                tag = query[1:].lower()  # Remove o # e normaliza
                
                # Buscar posts que têm essa hashtag
                posts_query = Post.query.join(
                    post_hashtags, Post.id == post_hashtags.c.post_id
                ).join(
                    Hashtag, Hashtag.id == post_hashtags.c.hashtag_id
                ).filter(
                    Hashtag.tag == tag,
                    Post.ativo == True
                ).order_by(
                    Post.data_criacao.desc()
                ).paginate(page=page, per_page=per_page, error_out=False)
            else:
                # Buscar no texto do post
                posts_query = Post.query.filter(
                    Post.texto.ilike(f'%{query}%'),
                    Post.ativo == True
                ).order_by(
                    Post.data_criacao.desc()
                ).paginate(page=page, per_page=per_page, error_out=False)
            
            # Formatar resultados dos posts
            resultados = []
            for p in posts_query.items:
                autor = User.query.get(p.user_id)
                midia = PostMidia.query.filter_by(post_id=p.id).first()
                
                # Obter hashtags do post
                hashtags_post = db.session.query(Hashtag.tag).join(
                    post_hashtags, Hashtag.id == post_hashtags.c.hashtag_id
                ).filter(
                    post_hashtags.c.post_id == p.id
                ).all()
                
                resultados.append({
                    'id': p.id,
                    'texto': p.texto[:200] if p.texto else '',
                    'autor': autor.nome_completo if autor else 'Desconhecido',
                    'autor_id': p.user_id,
                    'avatar': obter_avatar_url(p.user_id),
                    'data_criacao': p.data_criacao,
                    'total_likes': p.total_likes,
                    'total_comentarios': p.total_comentarios,
                    'tipo_midia': p.tipo_midia,
                    'midia_url': midia.url if midia else None,
                    'hashtags': [h.tag for h in hashtags_post]
                })
            
            total = posts_query.total
        else:
            # Sem query: mostrar posts populares (mais likes)
            posts_populares = Post.query.filter(
                Post.ativo == True
            ).order_by(
                Post.total_likes.desc(),
                Post.data_criacao.desc()
            ).limit(20).all()
            
            resultados = []
            for p in posts_populares:
                autor = User.query.get(p.user_id)
                midia = PostMidia.query.filter_by(post_id=p.id).first()
                
                # Obter hashtags do post
                hashtags_post = db.session.query(Hashtag.tag).join(
                    post_hashtags, Hashtag.id == post_hashtags.c.hashtag_id
                ).filter(
                    post_hashtags.c.post_id == p.id
                ).all()
                
                resultados.append({
                    'id': p.id,
                    'texto': p.texto[:200] if p.texto else '',
                    'autor': autor.nome_completo if autor else 'Desconhecido',
                    'autor_id': p.user_id,
                    'avatar': obter_avatar_url(p.user_id),
                    'data_criacao': p.data_criacao,
                    'total_likes': p.total_likes,
                    'total_comentarios': p.total_comentarios,
                    'tipo_midia': p.tipo_midia,
                    'midia_url': midia.url if midia else None,
                    'hashtags': [h.tag for h in hashtags_post]
                })
            
            total = len(resultados)
    
    # =====================================================
    # TAB 3: BUSCAR HASHTAGS
    # =====================================================
    elif tipo == 'hashtags':
        if query:
            # Remover # se o usuário digitou
            tag_busca = query[1:] if query.startswith('#') else query
            tag_busca = tag_busca.lower()
            
            # Buscar hashtags
            hashtags_query = Hashtag.query.filter(
                Hashtag.tag.ilike(f'%{tag_busca}%')
            ).order_by(
                Hashtag.uso_ultima_semana.desc(),
                Hashtag.total_uso.desc()
            ).paginate(page=page, per_page=per_page, error_out=False)
            
            resultados = [{
                'id': h.id,
                'tag': h.tag,
                'total_uso': h.total_uso,
                'uso_ultima_semana': h.uso_ultima_semana,
                'ultimo_uso': h.ultimo_uso
            } for h in hashtags_query.items]
            
            total = hashtags_query.total
        else:
            # Sem query: mostrar hashtags em alta (usa a view do banco)
            hashtags_em_alta = db.session.execute(
                db.text("SELECT * FROM hashtags_em_alta LIMIT 20")
            ).fetchall()
            
            resultados = [{
                'id': h[0],
                'tag': h[1],
                'total_uso': h[2],
                'uso_ultima_semana': h[3],
                'ultimo_uso': h[4]
            } for h in hashtags_em_alta]
            
            total = len(resultados)
    
    # Obter hashtags em alta para sidebar (sempre mostrar)
    hashtags_sidebar = db.session.execute(
        db.text("SELECT tag, uso_ultima_semana FROM hashtags_em_alta LIMIT 10")
    ).fetchall()
    
    return render_template(
        'helpzone/buscar.html',
        query=query,
        tipo=tipo,
        resultados=resultados,
        total=total,
        page=page,
        hashtags_em_alta=hashtags_sidebar
    )


# ==================== API DE BUSCA RÁPIDA (Autocomplete) ====================
@helpzone_bp.route('/api/busca-rapida', methods=['GET'])
@login_required
def busca_rapida():
    """
    API para autocomplete no campo de busca
    Retorna usuários e hashtags mais relevantes
    """
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify({'usuarios': [], 'hashtags': []})
    
    # Buscar top 5 usuários
    usuarios = User.query.filter(
        User.nome_completo.ilike(f'%{query}%'),
        User.id != current_user.id,
        User.is_active == True
    ).limit(5).all()
    
    usuarios_resultado = [{
        'id': u.id,
        'nome': u.nome_completo,
        'username': u.username,
        'avatar': obter_avatar_url(u.id)
    } for u in usuarios]
    
    # Buscar top 5 hashtags
    tag_busca = query[1:] if query.startswith('#') else query
    hashtags = Hashtag.query.filter(
        Hashtag.tag.ilike(f'%{tag_busca}%')
    ).order_by(
        Hashtag.uso_ultima_semana.desc()
    ).limit(5).all()
    
    hashtags_resultado = [{
        'tag': h.tag,
        'total_uso': h.total_uso
    } for h in hashtags]
    
    return jsonify({
        'usuarios': usuarios_resultado,
        'hashtags': hashtags_resultado
    })


# ==================== FUNÇÕES AUXILIARES ====================
def obter_avatar_url(user_id):
    """
    Retorna URL do avatar do usuário
    """
    # Verificar se tem avatar customizado
    avatar_path = f"/static/uploads/avatars/{user_id}.jpg"
    avatar_file = os.path.join(current_app.root_path, avatar_path.lstrip('/'))
    
    if os.path.exists(avatar_file):
        return avatar_path
    
    # Avatar padrão
    return "/static/images/avatar-default.png"


def obter_nivel_usuario(xp_total):
    """
    Calcula o nível do usuário baseado no XP
    """
    if xp_total < 100:
        return 1
    elif xp_total < 500:
        return 2
    elif xp_total < 1000:
        return 3
    elif xp_total < 2500:
        return 4
    elif xp_total < 5000:
        return 5
    elif xp_total < 10000:
        return 6
    elif xp_total < 20000:
        return 7
    elif xp_total < 50000:
        return 8
    elif xp_total < 100000:
        return 9
    else:
        return 10

# ==================== DETALHES DE UM POST ====================
@helpzone_bp.route('/post/<int:post_id>')
@login_required
def detalhes_post(post_id):
    """
    Visualizar um post específico com todos os comentários
    """
    post = Post.query.get_or_404(post_id)
    
    # Comentários (implementação futura)
    comentarios = PostComentario.query.filter_by(post_id=post_id, ativo=True)\
                                       .order_by(PostComentario.data_criacao)\
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
    """
    Estatísticas gerais do HelpZone Social
    """
    # Stats do usuário
    perfil = PerfilSocial.query.filter_by(user_id=current_user.id).first()
    
    # Top posts do usuário
    top_posts = Post.query.filter_by(user_id=current_user.id, ativo=True)\
                          .order_by(desc(Post.total_likes))\
                          .limit(5)\
                          .all()
    
    # Evolução de seguidores (últimos 30 dias)
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





# ==================== API PARA MODAL DE COMENTÁRIOS ====================

@helpzone_bp.route('/api/post/<int:post_id>/detalhes', methods=['GET'])
@login_required
def api_detalhes_post(post_id):
    """
    Retorna detalhes do post em JSON para o modal
    """
    post = Post.query.get_or_404(post_id)
    
    # URL da mídia
    midia_info = None
    if post.midia:
        midia_info = {
            'tipo': post.midia.tipo,
            'url': post.midia.url
        }
    
    # Informações do usuário
    perfil = PerfilSocial.query.filter_by(user_id=post.user_id).first()
    foto_perfil = None
    if perfil and perfil.foto_perfil:
        foto_perfil = perfil.foto_perfil
    
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
    """
    Retorna lista de comentários em JSON para o modal
    """
    comentarios = PostComentario.query.filter_by(post_id=post_id, ativo=True)\
                                       .order_by(PostComentario.data_criacao)\
                                       .all()
    
    comentarios_list = []
    for c in comentarios:
        # Foto de perfil do usuário que comentou
        perfil = PerfilSocial.query.filter_by(user_id=c.user_id).first()
        foto_perfil = None
        if perfil and perfil.foto_perfil:
            foto_perfil = perfil.foto_perfil
        
        # Calcular tempo relativo
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
            'total_likes': c.total_likes if hasattr(c, 'total_likes') else 0
        })
    
    return jsonify({
        'success': True,
        'comentarios': comentarios_list
    })


@helpzone_bp.route('/api/post/<int:post_id>/comentar', methods=['POST'])
@login_required
def api_comentar_post(post_id):
    """
    Adiciona um comentário via API
    """
    post = Post.query.get_or_404(post_id)
    
    data = request.get_json()
    texto = data.get('texto', '').strip()
    
    if not texto:
        return jsonify({'error': 'Comentário não pode estar vazio'}), 400
    
    # Criar comentário
    comentario = PostComentario(
        post_id=post_id,
        user_id=current_user.id,
        texto=texto
    )
    db.session.add(comentario)
    
    # Atualizar contador de comentários do post
    post.total_comentarios += 1
    
    # Criar notificação para o autor do post (se não for ele mesmo)
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
