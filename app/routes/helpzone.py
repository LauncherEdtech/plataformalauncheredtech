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


# ==================== CRIAR POST ====================
@helpzone_bp.route('/criar-post', methods=['GET', 'POST'])
@login_required
def criar_post():
    """
    Página para criar um novo post
    Aceita texto, imagem ou vídeo
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
        
        # Upload de mídia (se houver)
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
        
        # Atualizar perfil social
        perfil = PerfilSocial.query.filter_by(user_id=current_user.id).first()
        if perfil:
            perfil.total_posts += 1
            perfil.ultima_postagem = datetime.utcnow()
        
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


# ==================== COMENTÁRIOS (NOVO) ====================
@helpzone_bp.route('/api/post/<int:post_id>/comentar', methods=['POST'])
@login_required
def comentar_post(post_id):
    """
    Adicionar comentário a um post
    """
    post = Post.query.get_or_404(post_id)
    
    # Tenta pegar JSON, se falhar, pega Form Data (para suportar ambos)
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
            
    # Criar comentário
    comentario = PostComentario(
        post_id=post_id,
        user_id=current_user.id,
        texto=texto
    )
    db.session.add(comentario)
    
    # Atualizar contador do post
    post.total_comentarios += 1
    
    # Notificar dono do post (se não for o próprio)
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
    """
    Salvar ou remover dos salvos
    """
    post = Post.query.get_or_404(post_id)
    
    salvo = PostSalvo.query.filter_by(
        user_id=current_user.id,
        post_id=post_id
    ).first()
    
    if salvo:
        # Remover dos salvos
        db.session.delete(salvo)
        action = 'removed'
    else:
        # Salvar
        novo_salvo = PostSalvo(user_id=current_user.id, post_id=post_id)
        db.session.add(novo_salvo)
        action = 'saved'
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'action': action
    })

# ==================== EDITAR PERFIL (COM FOTO) ====================
@helpzone_bp.route('/api/perfil/editar', methods=['POST'])
@login_required
def editar_perfil():
    print("--- INICIANDO EDIÇÃO DE PERFIL ---") # DEBUG
    
    ocupacao = request.form.get('ocupacao', '').strip()
    biografia = request.form.get('biografia', '').strip()
    
    print(f"Dados recebidos: Ocupação={ocupacao}, Bio={biografia}") # DEBUG
    
    perfil = PerfilSocial.query.filter_by(user_id=current_user.id).first()
    if not perfil:
        perfil = PerfilSocial(user_id=current_user.id)
        db.session.add(perfil)
    
    perfil.ocupacao = ocupacao
    perfil.biografia = biografia
    
    # --- DEBUG DA FOTO ---
    if 'foto_perfil' not in request.files:
        print("ERRO: Nenhuma parte 'foto_perfil' encontrada na requisição.") # DEBUG
    else:
        arquivo = request.files['foto_perfil']
        print(f"Arquivo recebido: {arquivo.filename}") # DEBUG
        
        if arquivo and arquivo.filename:
            # Extensões permitidas
            ALLOWED = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            ext = arquivo.filename.rsplit('.', 1)[1].lower() if '.' in arquivo.filename else ''
            
            if ext not in ALLOWED:
                print(f"ERRO: Extensão {ext} não permitida.") # DEBUG
                return jsonify({'error': 'Formato inválido'}), 400
            
            # Gera nome e salva
            novo_nome = f"avatar_{current_user.id}_{int(time.time())}.{ext}"
            upload_path = os.path.join(current_app.root_path, 'static/uploads/avatars')
            
            # Garante que a pasta existe
            if not os.path.exists(upload_path):
                print(f"Criando pasta: {upload_path}") # DEBUG
                os.makedirs(upload_path)
            
            caminho_completo = os.path.join(upload_path, novo_nome)
            arquivo.save(caminho_completo)
            print(f"Arquivo salvo com sucesso em: {caminho_completo}") # DEBUG
            
            # Salva no banco (URL relativa para o HTML usar)
            url_db = f"/static/uploads/avatars/{novo_nome}"
            perfil.foto_perfil = url_db
            print(f"Caminho salvo no banco: {url_db}") # DEBUG
        else:
            print("AVISO: O arquivo chegou vazio ou sem nome.") # DEBUG

    try:
        db.session.commit()
        print("--- SUCESSO: Alterações commitadas no banco ---") # DEBUG
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"ERRO DE BANCO: {str(e)}") # DEBUG
        return jsonify({'error': 'Erro ao salvar no banco'}), 500

# ==================== PERFIL DO USUÁRIO ====================
@helpzone_bp.route('/perfil/<int:user_id>')
@login_required
def perfil_usuario(user_id):
    """
    Perfil de um usuário no feed social (Com Abas)
    """
    from app.models.user import User
    
    usuario = User.query.get_or_404(user_id)
    perfil = PerfilSocial.query.filter_by(user_id=user_id).first()
    
    if not perfil:
        perfil = PerfilSocial(user_id=user_id)
        db.session.add(perfil)
        db.session.commit()
    
    # Controle de Abas
    tab = request.args.get('tab', 'posts')
    page = request.args.get('page', 1, type=int)
    
    posts = None
    
    if tab == 'salvos' and current_user.id == user_id:
        # Busca posts salvos (JOIN)
        posts = Post.query.join(PostSalvo).filter(
            PostSalvo.user_id == user_id
        ).order_by(desc(PostSalvo.data_salvo)).paginate(page=page, per_page=18, error_out=False)
    else:
        # Busca posts criados (Padrão)
        posts = Post.query.filter_by(user_id=user_id, ativo=True)\
                          .order_by(desc(Post.data_criacao))\
                          .paginate(page=page, per_page=18, error_out=False)
    
    # Verificar follow
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
@helpzone_bp.route('/buscar', methods=['GET'])
@login_required
def buscar_usuarios():
    """
    Página de busca avançada com tabs:
    - Pessoas: busca por nome
    - Posts: busca por texto ou hashtag
    - Hashtags: busca por tag
    """
    from app.models.user import User
    
    query = request.args.get('q', '').strip()
    tipo = request.args.get('tipo', 'pessoas')  # pessoas, posts, hashtags
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # DEBUG
    current_app.logger.info(f"[BUSCA] Query: '{query}', Tipo: '{tipo}', Page: {page}")
    
    # Variáveis para o template (NOMES CORRETOS!)
    usuarios = None
    posts = None
    hashtags = None
    
    # IDs de quem o usuário atual segue
    seguindo_ids = {s.seguido_id for s in current_user.seguindo.all()}
    
    # =====================================================
    # TAB 1: BUSCAR PESSOAS
    # =====================================================
    if tipo == 'pessoas':
        if query:
            current_app.logger.info(f"[BUSCA PESSOAS] Buscando: {query}")
            usuarios = User.query.filter(
                User.nome_completo.ilike(f'%{query}%'),
                User.id != current_user.id,
                User.is_active == True
            ).paginate(page=page, per_page=per_page, error_out=False)
            
            current_app.logger.info(f"[BUSCA PESSOAS] Encontrados: {usuarios.total}")
        else:
            # Usuários populares
            current_app.logger.info("[BUSCA PESSOAS] Mostrando populares")
            usuarios = User.query.join(PerfilSocial).filter(
                User.id != current_user.id,
                User.is_active == True
            ).order_by(
                PerfilSocial.score_social.desc()
            ).paginate(page=page, per_page=per_page, error_out=False)
            
            current_app.logger.info(f"[BUSCA PESSOAS] Populares: {usuarios.total}")
    
    # =====================================================
    # TAB 2: BUSCAR POSTS
    # =====================================================
    elif tipo == 'posts':
        if query:
            current_app.logger.info(f"[BUSCA POSTS] Query: {query}")
            
            if query.startswith('#'):
                # Buscar por hashtag
                tag = query[1:].lower()
                current_app.logger.info(f"[BUSCA POSTS] Hashtag: #{tag}")
                
                posts = Post.query.join(
                    post_hashtags, Post.id == post_hashtags.c.post_id
                ).join(
                    Hashtag, Hashtag.id == post_hashtags.c.hashtag_id
                ).filter(
                    Hashtag.tag == tag,
                    Post.ativo == True
                ).order_by(
                    Post.data_criacao.desc()
                ).paginate(page=page, per_page=per_page, error_out=False)
                
                current_app.logger.info(f"[BUSCA POSTS] Posts com #{tag}: {posts.total}")
            else:
                # Buscar no texto
                current_app.logger.info(f"[BUSCA POSTS] Texto: {query}")
                
                posts = Post.query.filter(
                    Post.texto.ilike(f'%{query}%'),
                    Post.ativo == True
                ).order_by(
                    Post.data_criacao.desc()
                ).paginate(page=page, per_page=per_page, error_out=False)
                
                current_app.logger.info(f"[BUSCA POSTS] Posts encontrados: {posts.total}")
        else:
            # Posts populares
            current_app.logger.info("[BUSCA POSTS] Mostrando populares")
            
            posts = Post.query.filter(
                Post.ativo == True
            ).order_by(
                Post.total_likes.desc(),
                Post.data_criacao.desc()
            ).paginate(page=page, per_page=per_page, error_out=False)
            
            current_app.logger.info(f"[BUSCA POSTS] Posts populares: {posts.total}")
    
    # =====================================================
    # TAB 3: BUSCAR HASHTAGS
    # =====================================================
    elif tipo == 'hashtags':
        if query:
            # Buscar hashtag
            tag_busca = query[1:] if query.startswith('#') else query
            tag_busca = tag_busca.lower()
            
            current_app.logger.info(f"[BUSCA HASHTAGS] Tag: {tag_busca}")
            
            hashtags = Hashtag.query.filter(
                Hashtag.tag.ilike(f'%{tag_busca}%')
            ).order_by(
                Hashtag.uso_ultima_semana.desc(),
                Hashtag.total_uso.desc()
            ).paginate(page=page, per_page=per_page, error_out=False)
            
            current_app.logger.info(f"[BUSCA HASHTAGS] Encontradas: {hashtags.total}")
        else:
            # Hashtags em alta
            current_app.logger.info("[BUSCA HASHTAGS] Mostrando em alta")
            
            hashtags = Hashtag.query.filter(
                Hashtag.uso_ultima_semana > 0
            ).order_by(
                Hashtag.uso_ultima_semana.desc(),
                Hashtag.total_uso.desc()
            ).paginate(page=page, per_page=per_page, error_out=False)
            
            current_app.logger.info(f"[BUSCA HASHTAGS] Em alta: {hashtags.total}")
    
    # =====================================================
    # HASHTAGS EM ALTA (SIDEBAR)
    # =====================================================
    hashtags_em_alta = Hashtag.query.filter(
        Hashtag.uso_ultima_semana > 0
    ).order_by(
        Hashtag.uso_ultima_semana.desc()
    ).limit(10).all()
    
    current_app.logger.info(f"[SIDEBAR] Hashtags em alta: {len(hashtags_em_alta)}")
    
    # LOG FINAL
    current_app.logger.info(
        f"[BUSCA] Retornando - Usuarios: {usuarios.total if usuarios else 0}, "
        f"Posts: {posts.total if posts else 0}, "
        f"Hashtags: {hashtags.total if hashtags else 0}"
    )
    
    # =====================================================
    # RENDER TEMPLATE (VARIÁVEIS COM NOMES CORRETOS!)
    # =====================================================
    return render_template(
        'helpzone/buscar.html',
        query=query,
        tipo=tipo,
        usuarios=usuarios,              # ← NOME CORRETO!
        posts=posts,                    # ← NOME CORRETO!
        hashtags=hashtags,              # ← NOME CORRETO!
        seguindo_ids=seguindo_ids,
        hashtags_em_alta=hashtags_em_alta
    )

# ==================== DETALHES DE UM POST ====================
@helpzone_bp.route('/post/<int:post_id>')
@login_required
def detalhes_post(post_id):
    """
    Visualizar um post específico com todos os comentários
    """
    post = Post.query.get_or_404(post_id)
    
    # Comentários
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




# ==================== API - SUGESTÕES DE USUÁRIOS ====================
@helpzone_bp.route('/api/sugestoes')
@login_required
def sugestoes_usuarios():
    """
    Retorna sugestões inteligentes de usuários para seguir
    
    Algoritmo:
    1. Usuários que meus amigos seguem (amigos de amigos)
    2. Usuários mais ativos recentemente
    3. Usuários com interesses similares (baseado em posts)
    """
    from app.models.user import User
    
    # IDs de quem já sigo
    seguindo_ids = [s.seguido_id for s in current_user.seguindo.all()]
    seguindo_ids.append(current_user.id)
    
    # Opção 1: Amigos de amigos (usuários que meus amigos seguem)
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
    
    # Opção 2: Usuários mais ativos (caso não tenha amigos de amigos suficientes)
    if len(amigos_de_amigos) < 5:
        usuarios_ativos = User.query\
            .join(PerfilSocial)\
            .filter(~User.id.in_(seguindo_ids))\
            .order_by(desc(PerfilSocial.score_social))\
            .limit(5 - len(amigos_de_amigos))\
            .all()
        
        amigos_de_amigos.extend(usuarios_ativos)
    
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
    """
    Denunciar um post por conteúdo inadequado
    """
    post = Post.query.get_or_404(post_id)
    motivo = request.json.get('motivo', '5')  # Default: Outro
    
    # Mapear motivos
    motivos_map = {
        '1': 'Conteúdo impróprio',
        '2': 'Spam',
        '3': 'Assédio',
        '4': 'Informação falsa',
        '5': 'Outro'
    }
    
    motivo_texto = motivos_map.get(motivo, 'Outro')
    
    # Criar registro de denúncia
    denuncia = DenunciaPost(
        post_id=post_id,
        user_id=current_user.id,
        motivo=motivo_texto,
        data_criacao=datetime.utcnow()
    )
    db.session.add(denuncia)
    
    # Se o post tiver 3+ denúncias, marcar para revisão
    total_denuncias = DenunciaPost.query.filter_by(post_id=post_id).count()
    if total_denuncias >= 3:
        post.requer_revisao = True
        
        # Notificar administradores (implementar depois)
        # notify_admins_post_flagged(post_id)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'mensagem': 'Denúncia registrada. Obrigado por manter nossa comunidade segura!'
    })


# ==================== EDITAR POST ====================
@helpzone_bp.route('/api/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def editar_post(post_id):
    """
    Editar texto de um post existente
    Nota: Não permite editar mídia, apenas texto
    """
    post = Post.query.get_or_404(post_id)
    
    # Verificar se é o autor
    if post.user_id != current_user.id:
        return jsonify({'error': 'Você não pode editar este post'}), 403
    
    if request.method == 'POST':
        novo_texto = request.json.get('texto', '').strip()
        
        if not novo_texto:
            return jsonify({'error': 'Texto não pode estar vazio'}), 400
        
        # Atualizar post
        post.texto = novo_texto
        post.data_atualizacao = datetime.utcnow()
        post.editado = True
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'texto': novo_texto,
            'data_atualizacao': post.data_atualizacao.strftime('%d/%m/%Y %H:%M')
        })
    
    # GET - retornar dados atuais
    return jsonify({
        'texto': post.texto,
        'tipo_midia': post.tipo_midia
    })


# ==================== STORIES (FUNCIONALIDADE FUTURA) ====================
@helpzone_bp.route('/api/stories')
@login_required
def get_stories():
    """
    Retorna stories ativos dos últimos 24h
    """
    data_limite = datetime.utcnow() - timedelta(hours=24)
    
    # Stories de quem eu sigo + próprios
    seguindo_ids = [s.seguido_id for s in current_user.seguindo.all()]
    seguindo_ids.append(current_user.id)
    
    stories = Story.query.filter(
        Story.user_id.in_(seguindo_ids),
        Story.data_criacao >= data_limite,
        Story.ativo == True
    ).order_by(desc(Story.data_criacao)).all()
    
    # Agrupar por usuário
    stories_por_usuario = {}
    for story in stories:
        if story.user_id not in stories_por_usuario:
            stories_por_usuario[story.user_id] = {
                'user_id': story.user_id,
                'username': story.user.nome_completo,
                'avatar': story.user.perfil_social.foto_perfil if story.user.perfil_social else None,
                'stories': [],
                'visto': False  # Implementar lógica de visualização
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


# ==================== CRIAR STORY (ATUALIZADO) ====================
# Adicione ou substitua esta rota em app/routes/helpzone.py

@helpzone_bp.route('/criar-story', methods=['GET', 'POST'])
@login_required
def criar_story():
    """
    Criar um novo story (disponível por 24h)
    GET: Renderiza página de criação
    POST: Processa upload do story
    """
    if request.method == 'GET':
        # Renderizar página de criação
        return render_template('helpzone/criar_story.html')
    
    # POST - Processar upload
    arquivo = request.files.get('arquivo')
    
    if not arquivo or not arquivo.filename:
        return jsonify({'error': 'Arquivo obrigatório', 'success': False}), 400
    
    # Determinar tipo
    if arquivo.mimetype.startswith('image'):
        tipo = 'imagem'
        max_size = 5 * 1024 * 1024  # 5MB
        allowed_exts = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    elif arquivo.mimetype.startswith('video'):
        tipo = 'video'
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
        return jsonify({'error': f'Arquivo muito grande. Máximo: {max_mb}MB', 'success': False}), 400
    
    # Processar upload
    try:
        filename = generate_unique_filename(arquivo.filename)
        upload_path = os.path.join(current_app.root_path, 'static/uploads/stories', str(current_user.id))
        os.makedirs(upload_path, exist_ok=True)
        
        filepath = os.path.join(upload_path, filename)
        arquivo.save(filepath)
        
        midia_url = f"/static/uploads/stories/{current_user.id}/{filename}"
        
        # Criar story no banco
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
        
        current_app.logger.info(f"Story {story.id} criado por usuário {current_user.id}")
        
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

@helpzone_bp.route('/api/story/<int:story_id>/view', methods=['POST'])
@login_required
def visualizar_story(story_id):
    """
    Registrar visualização de story
    """
    story = Story.query.get_or_404(story_id)
    
    # Incrementar visualizações
    story.visualizacoes += 1
    
    # Registrar visualização individual (para não contar duplicatas)
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
    """
    Feed de vídeos curtos verticais (estilo TikTok/Instagram Reels)
    """
    page = request.args.get('page', 1, type=int)
    
    # Buscar apenas posts com vídeo
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
    """
    Analytics detalhado de um post (apenas para o autor)
    """
    post = Post.query.get_or_404(post_id)
    
    if post.user_id != current_user.id:
        return jsonify({'error': 'Acesso negado'}), 403
    
    # Estatísticas de likes
    likes_por_dia = db.session.query(
        func.date(PostLike.data_criacao).label('data'),
        func.count(PostLike.id).label('total')
    ).filter(
        PostLike.post_id == post_id,
        PostLike.tipo == 'like'
    ).group_by(func.date(PostLike.data_criacao)).all()
    
    # Comentários por dia
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
        'alcance': post.total_likes + post.total_comentarios * 2,  # Métrica simples
        'engajamento_taxa': round((post.total_likes + post.total_comentarios) / max(post.user.perfil_social.total_seguidores, 1) * 100, 2),
        'likes_por_dia': [{'data': str(item.data), 'total': item.total} for item in likes_por_dia],
        'comentarios_por_dia': [{'data': str(item.data), 'total': item.total} for item in comentarios_por_dia]
    })




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
            'total_likes': getattr(c, 'total_likes', 0)
        })
    
    return jsonify({
        'success': True,
        'comentarios': comentarios_list
    })


@helpzone_bp.route('/api/post/<int:post_id>/comentar', methods=['POST'])
@login_required
def api_comentar_post(post_id):
    """
    Adiciona um comentário via API (JSON)
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

