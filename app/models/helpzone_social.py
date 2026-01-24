# app/models/helpzone_social.py
"""
Modelos do HelpZone como Feed Social de Estudos
Sistema completo de rede social focada em rotina de estudos
"""

from datetime import datetime
from app import db
from sqlalchemy import func, Index
import re


# ==================== POST ====================
class Post(db.Model):
    """
    Postagem no feed social
    Pode ser texto, imagem ou vídeo (máx 20 segundos)
    """
    __tablename__ = 'post'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Conteúdo
    texto = db.Column(db.Text)  # Texto da postagem (opcional se tiver mídia)
    tipo_midia = db.Column(db.String(10))  # 'texto', 'imagem', 'video'
    
    # Timestamps
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Métricas (desnormalizadas para performance)
    total_likes = db.Column(db.Integer, default=0)
    total_dislikes = db.Column(db.Integer, default=0)
    total_comentarios = db.Column(db.Integer, default=0)
    
    # Visibilidade
    ativo = db.Column(db.Boolean, default=True)  # Se foi deletado/oculto
    
    # Relacionamentos
    user = db.relationship('User', backref=db.backref('posts', lazy='dynamic'))
    midia = db.relationship('PostMidia', backref='post', lazy='joined', uselist=False, cascade='all, delete-orphan')
    likes = db.relationship('PostLike', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    comentarios = db.relationship('PostComentario', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    
    # Índices para performance
    __table_args__ = (
        Index('idx_post_user_data', 'user_id', 'data_criacao'),
        Index('idx_post_data_likes', 'data_criacao', 'total_likes'),
    )
    
    def __repr__(self):
        return f'<Post {self.id} by User {self.user_id}>'
    
    def get_score(self):
        """Calcula score para ranking (likes - dislikes)"""
        return self.total_likes - self.total_dislikes
    
    def user_liked(self, user_id):
        """Verifica se o usuário deu like"""
        return PostLike.query.filter_by(
            post_id=self.id, 
            user_id=user_id, 
            tipo='like'
        ).first() is not None
    
    def user_disliked(self, user_id):
        """Verifica se o usuário deu dislike"""
        return PostLike.query.filter_by(
            post_id=self.id, 
            user_id=user_id, 
            tipo='dislike'
        ).first() is not None
    
    def to_dict(self):
        """Serializa para JSON"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.nome if self.user else 'Anônimo',
            'user_avatar': self.user.avatar_url if hasattr(self.user, 'avatar_url') else None,
            'texto': self.texto,
            'tipo_midia': self.tipo_midia,
            'midia_url': self.midia.url if self.midia else None,
            'data_criacao': self.data_criacao.isoformat(),
            'total_likes': self.total_likes,
            'total_dislikes': self.total_dislikes,
            'total_comentarios': self.total_comentarios,
            'score': self.get_score()
        }

    def processar_hashtags(self):
       '''
       Extrai e associa hashtags ao post
       Deve ser chamado após criar/atualizar um post
       '''
       if not self.texto:
          return
    
        # Extrair hashtags do texto
       hashtags_texto = Hashtag.extrair_hashtags(self.texto)
    
       # Remover hashtags antigas
       self.hashtags.clear()
    
       # Adicionar novas hashtags
       for tag_nome in hashtags_texto:
            hashtag = Hashtag.obter_ou_criar(tag_nome)
            self.hashtags.append(hashtag)
    
       db.session.commit()


    # --- NOVO MÉTODO ---
    def user_saved(self, user_id):
        """Verifica se o usuário salvou este post"""
        return PostSalvo.query.filter_by(post_id=self.id, user_id=user_id).first() is not None
    
    # ... (Mantenha os outros métodos: get_score, user_liked, etc.)
    def user_liked(self, user_id):
        return PostLike.query.filter_by(post_id=self.id, user_id=user_id, tipo='like').first() is not None
    
    def user_disliked(self, user_id):
        return PostLike.query.filter_by(post_id=self.id, user_id=user_id, tipo='dislike').first() is not None




post_hashtags = db.Table('post_hashtags',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('hashtag_id', db.Integer, db.ForeignKey('hashtag.id'), primary_key=True),
    db.Column('data_criacao', db.DateTime, default=datetime.utcnow)
)


class Hashtag(db.Model):
    """
    Hashtags extraídas dos posts
    Rastreia popularidade e uso ao longo do tempo
    """
    __tablename__ = 'hashtag'
    
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(100), nullable=False, unique=True, index=True)  # Ex: "matematica"
    
    # Métricas de popularidade
    total_uso = db.Column(db.Integer, default=0)  # Quantas vezes foi usada
    uso_ultima_semana = db.Column(db.Integer, default=0)  # Uso nos últimos 7 dias
    ultimo_uso = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Timestamps
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento com Posts
    posts = db.relationship('Post', 
                           secondary=post_hashtags,
                           backref=db.backref('hashtags', lazy='dynamic'))
    
    # Índices para performance
    __table_args__ = (
        Index('idx_hashtag_uso_semana', 'uso_ultima_semana', 'total_uso'),
        Index('idx_hashtag_ultimo_uso', 'ultimo_uso'),
    )
    
    def __repr__(self):
        return f'<Hashtag #{self.tag}>'
    
    @staticmethod
    def extrair_hashtags(texto):
        """
        Extrai hashtags de um texto
        Retorna lista de hashtags (sem o #)
        """
        import re
        if not texto:
            return []
        
        # Regex para capturar hashtags (letras, números, acentuadas)
        pattern = r'#([a-záéíóúàâêôãõçA-ZÁÉÍÓÚÀÂÊÔÃÕÇ0-9_]+)'
        hashtags = re.findall(pattern, texto)
        
        # Normalizar (lowercase)
        hashtags = [tag.lower() for tag in hashtags]
        
        # Remover duplicatas mantendo ordem
        hashtags_unicas = []
        for tag in hashtags:
            if tag not in hashtags_unicas:
                hashtags_unicas.append(tag)
        
        return hashtags_unicas
    
    @staticmethod
    def obter_ou_criar(tag_nome):
        """
        Obtém uma hashtag existente ou cria uma nova
        """
        tag_nome = tag_nome.lower().strip()
        
        hashtag = Hashtag.query.filter_by(tag=tag_nome).first()
        
        if not hashtag:
            hashtag = Hashtag(tag=tag_nome)
            db.session.add(hashtag)
        
        # Atualizar métricas
        hashtag.total_uso += 1
        hashtag.ultimo_uso = datetime.utcnow()
        
        return hashtag
    
    @staticmethod
    def atualizar_metricas_semanais():
        """
        Atualiza contadores de uso semanal
        Deve ser executado diariamente (cron job)
        """
        from datetime import timedelta
        
        data_limite = datetime.utcnow() - timedelta(days=7)
        
        # Para cada hashtag, contar posts dos últimos 7 dias
        hashtags = Hashtag.query.all()
        
        for hashtag in hashtags:
            uso_semana = db.session.query(func.count(post_hashtags.c.post_id))\
                .join(Post, Post.id == post_hashtags.c.post_id)\
                .filter(
                    post_hashtags.c.hashtag_id == hashtag.id,
                    Post.data_criacao >= data_limite,
                    Post.ativo == True
                )\
                .scalar()
            
            hashtag.uso_ultima_semana = uso_semana or 0
        
        db.session.commit()
    
    @staticmethod
    def obter_em_alta(limite=10):
        """
        Retorna hashtags mais usadas nos últimos 7 dias
        """
        return Hashtag.query\
            .filter(Hashtag.uso_ultima_semana > 0)\
            .order_by(
                Hashtag.uso_ultima_semana.desc(),
                Hashtag.total_uso.desc()
            )\
            .limit(limite)\
            .all()




# ==================== MÍDIA ====================
class PostMidia(db.Model):
    """
    Arquivos de mídia anexados a posts (imagem ou vídeo)
    """
    __tablename__ = 'post_midia'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False, unique=True)
    
    # Arquivo
    tipo = db.Column(db.String(10), nullable=False)  # 'imagem' ou 'video'
    url = db.Column(db.String(500), nullable=False)  # Caminho do arquivo
    url_thumbnail = db.Column(db.String(500))  # Thumbnail do vídeo
    
    # Metadados
    tamanho_bytes = db.Column(db.Integer)  # Tamanho do arquivo
    duracao_segundos = db.Column(db.Integer)  # Duração do vídeo (máx 20)
    largura = db.Column(db.Integer)  # Dimensões
    altura = db.Column(db.Integer)
    
    # Processamento
    processado = db.Column(db.Boolean, default=False)  # Se passou por otimização
    
    data_upload = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PostMidia {self.id} - {self.tipo}>'


# --- NOVO MODELO: POSTS SALVOS ---
class PostSalvo(db.Model):
    """
    Posts salvos pelo usuário (Bookmarks)
    """
    __tablename__ = 'post_salvo'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    data_salvo = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    user = db.relationship('User', backref=db.backref('posts_salvos', lazy='dynamic'))
    post = db.relationship('Post')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'post_id', name='unique_user_saved_post'),
        Index('idx_saved_user', 'user_id', 'data_salvo'),
    )



# ==================== LIKES/DISLIKES ====================
class PostLike(db.Model):
    """
    Reações em posts (like ou dislike)
    """
    __tablename__ = 'post_like'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    tipo = db.Column(db.String(10), nullable=False)  # 'like' ou 'dislike'
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    user = db.relationship('User', backref='post_likes')
    
    # Garantir uma reação por usuário por post
    __table_args__ = (
        db.UniqueConstraint('post_id', 'user_id', name='unique_post_like_user'),
        Index('idx_like_post', 'post_id'),
        Index('idx_like_user', 'user_id'),
    )
    
    def __repr__(self):
        return f'<PostLike {self.tipo} on Post {self.post_id} by User {self.user_id}>'


# ==================== COMENTÁRIOS ====================
class PostComentario(db.Model):
    """
    Comentários em posts (funcionalidade futura)
    """
    __tablename__ = 'post_comentario'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    texto = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    user = db.relationship('User', backref='comentarios')
    
    __table_args__ = (
        Index('idx_comentario_post', 'post_id', 'data_criacao'),
    )
    
    def __repr__(self):
        return f'<PostComentario {self.id} on Post {self.post_id}>'


# ==================== SEGUIDORES ====================
class Seguidor(db.Model):
    """
    Sistema de seguidores (follow/unfollow)
    """
    __tablename__ = 'seguidor'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Quem segue
    seguidor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Quem é seguido
    seguido_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    data_inicio = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    seguidor = db.relationship('User', 
                               foreign_keys=[seguidor_id], 
                               backref=db.backref('seguindo', lazy='dynamic'))
    seguido = db.relationship('User', 
                              foreign_keys=[seguido_id], 
                              backref=db.backref('seguidores', lazy='dynamic'))
    
    # Garantir um único follow por par de usuários
    __table_args__ = (
        db.UniqueConstraint('seguidor_id', 'seguido_id', name='unique_follow'),
        db.CheckConstraint('seguidor_id != seguido_id', name='no_self_follow'),
        Index('idx_seguidor_seguido', 'seguidor_id', 'seguido_id'),
        Index('idx_seguido_data', 'seguido_id', 'data_inicio'),
    )
    
    def __repr__(self):
        return f'<Seguidor {self.seguidor_id} -> {self.seguido_id}>'


# ==================== NOTIFICAÇÕES SOCIAIS ====================
class NotificacaoSocial(db.Model):
    """
    Notificações de interações sociais
    """
    __tablename__ = 'notificacao_social'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Quem gerou a notificação
    origem_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Tipo de notificação
    tipo = db.Column(db.String(20), nullable=False)  # 'like', 'follow', 'comentario'
    
    # Referência ao conteúdo
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    
    # Mensagem
    mensagem = db.Column(db.String(255), nullable=False)
    
    # Status
    lida = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    user = db.relationship('User', foreign_keys=[user_id], backref='notificacoes_sociais')
    origem_user = db.relationship('User', foreign_keys=[origem_user_id])
    post = db.relationship('Post', backref='notificacoes')
    
    __table_args__ = (
        Index('idx_notif_user_lida', 'user_id', 'lida', 'data_criacao'),
    )
    
    def __repr__(self):
        return f'<NotificacaoSocial {self.tipo} para User {self.user_id}>'


# ==================== DESAFIOS (Fase Futura) ====================
class Desafio(db.Model):
    """
    Desafios entre alunos (funcionalidade futura)
    """
    __tablename__ = 'desafio'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Participantes
    criador_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    desafiado_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Tipo de desafio
    tipo = db.Column(db.String(30), nullable=False)  # 'questoes', 'tempo_estudo', 'aulas', 'redacoes'
    
    # Meta
    meta_quantidade = db.Column(db.Integer)
    meta_descricao = db.Column(db.String(200))
    
    # Período
    data_inicio = db.Column(db.DateTime, nullable=False)
    data_fim = db.Column(db.DateTime, nullable=False)
    
    # Status
    status = db.Column(db.String(20), default='pendente')  # 'pendente', 'aceito', 'recusado', 'finalizado'
    
    # Resultados
    resultado_criador = db.Column(db.Integer, default=0)
    resultado_desafiado = db.Column(db.Integer, default=0)
    vencedor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    criador = db.relationship('User', foreign_keys=[criador_id], backref='desafios_criados')
    desafiado = db.relationship('User', foreign_keys=[desafiado_id], backref='desafios_recebidos')
    vencedor = db.relationship('User', foreign_keys=[vencedor_id])
    
    __table_args__ = (
        Index('idx_desafio_status', 'status', 'data_fim'),
    )
    
    def __repr__(self):
        return f'<Desafio {self.id} - {self.tipo}>'


# ==================== PERFIL SOCIAL (ATUALIZAR ESTA CLASSE) ====================
class PerfilSocial(db.Model):
    """
    Estatísticas sociais do usuário (cache/desnormalização)
    """
    __tablename__ = 'perfil_social'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    
    # --- NOVAS COLUNAS (ADICIONE ISTO) ---
    biografia = db.Column(db.String(300))
    ocupacao = db.Column(db.String(100))
    link_externo = db.Column(db.String(200))
    foto_perfil = db.Column(db.String(500))  # <--- ESSENCIAL PARA SALVAR A FOTO
    
    # Contadores
    total_posts = db.Column(db.Integer, default=0)
    total_seguidores = db.Column(db.Integer, default=0)
    total_seguindo = db.Column(db.Integer, default=0)
    total_likes_recebidos = db.Column(db.Integer, default=0)
    
    # Engajamento
    score_social = db.Column(db.Integer, default=0)
    nivel_influencia = db.Column(db.String(20), default='iniciante')
    
    # Timestamps
    ultima_postagem = db.Column(db.DateTime)
    ultimo_login = db.Column(db.DateTime)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento
    user = db.relationship('User', backref=db.backref('perfil_social', uselist=False))
    
    def __repr__(self):
        return f'<PerfilSocial User {self.user_id}>'
    
    def atualizar_nivel_influencia(self):
        score = (
            self.total_seguidores * 10 +
            self.total_posts * 5 +
            self.total_likes_recebidos * 2
        )
        
        if score >= 1000:
            self.nivel_influencia = 'destaque'
        elif score >= 500:
            self.nivel_influencia = 'influente'
        elif score >= 100:
            self.nivel_influencia = 'ativo'
        else:
            self.nivel_influencia = 'iniciante'
        
        self.score_social = score




class DenunciaPost(db.Model):
    __tablename__ = 'denuncia_post'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    motivo = db.Column(db.String(100), nullable=False)
    resolvida = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    post = db.relationship('Post', backref='denuncias')
    user = db.relationship('User', backref='denuncias_feitas')


class Story(db.Model):
    __tablename__ = 'story'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tipo = db.Column(db.String(10), nullable=False)  # 'imagem' ou 'video'
    url_midia = db.Column(db.String(500), nullable=False)
    visualizacoes = db.Column(db.Integer, default=0)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    expira_em = db.Column(db.DateTime, nullable=False, index=True)
    ativo = db.Column(db.Boolean, default=True)
    
    user = db.relationship('User', backref='stories')
    
    __table_args__ = (
        Index('idx_story_user_data', 'user_id', 'data_criacao'),
    )


class StoryVisualizacao(db.Model):
    __tablename__ = 'story_visualizacao'
    
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    data_visualizacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('story_id', 'user_id', name='unique_story_view'),
    )

