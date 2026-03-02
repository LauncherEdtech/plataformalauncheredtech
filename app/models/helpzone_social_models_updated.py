# app/models/helpzone_social_updated.py
"""
ATUALIZAÇÃO DOS MODELOS: PostMidia e Story
Adicione estas modificações aos seus modelos existentes
"""

# ==================== ATUALIZAÇÃO: POST MÍDIA ====================
"""
Na classe PostMidia, adicione o campo s3_key:
"""

class PostMidia(db.Model):
    """
    Mídia associada a um post (imagem ou vídeo)
    ATUALIZADO: Armazena arquivos no S3 em vez de local
    """
    __tablename__ = 'post_midia'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False, unique=True)
    
    tipo = db.Column(db.String(10), nullable=False)  # 'image' ou 'video'
    
    # ⭐ NOVO: Chave S3 do arquivo
    s3_key = db.Column(db.String(500), index=True)
    
    # LEGADO: URL local (manter para compatibilidade, mas não usar mais)
    url = db.Column(db.String(500))
    
    # Metadados
    tamanho_bytes = db.Column(db.Integer)
    duracao_segundos = db.Column(db.Integer)  # Apenas para vídeos
    
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PostMidia {self.id} - {self.tipo}>'
    
    def get_url(self, expires: int = 3600):
        """
        Retorna URL temporária para acesso ao arquivo
        
        Args:
            expires: Tempo de expiração em segundos (padrão: 1 hora)
        """
        if self.s3_key:
            from app.services import s3_service
            return s3_service.presigned_get_url(self.s3_key, expires=expires)
        
        # Fallback para URL legada
        return self.url


# ==================== ATUALIZAÇÃO: STORY ====================
"""
Na classe Story, adicione o campo s3_key:
"""

class Story(db.Model):
    """
    Stories (conteúdo temporário que expira em 24h)
    ATUALIZADO: Armazena arquivos no S3 em vez de local
    """
    __tablename__ = 'story'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    tipo = db.Column(db.String(10), nullable=False)  # 'imagem' ou 'video'
    
    # ⭐ NOVO: Chave S3 do arquivo
    s3_key = db.Column(db.String(500), index=True)
    
    # LEGADO: URL local (manter para compatibilidade, mas não usar mais)
    url_midia = db.Column(db.String(500))
    
    # Métricas
    visualizacoes = db.Column(db.Integer, default=0)
    
    # Controle de expiração
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    expira_em = db.Column(db.DateTime, nullable=False, index=True)
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    user = db.relationship('User', backref='stories')
    
    __table_args__ = (
        Index('idx_story_user_data', 'user_id', 'data_criacao'),
        Index('idx_story_ativo_expiracao', 'ativo', 'expira_em'),
    )
    
    def __repr__(self):
        return f'<Story {self.id} by User {self.user_id}>'
    
    def get_url(self, expires: int = 7200):
        """
        Retorna URL temporária para acesso ao story
        Stories têm URLs com validade de 2 horas por padrão
        
        Args:
            expires: Tempo de expiração em segundos (padrão: 2 horas)
        """
        if self.s3_key:
            from app.services import s3_service
            return s3_service.presigned_get_url(self.s3_key, expires=expires)
        
        # Fallback para URL legada
        return self.url_midia
    
    def esta_expirado(self):
        """Verifica se o story já expirou"""
        return datetime.utcnow() > self.expira_em
    
    @staticmethod
    def limpar_expirados():
        """
        Remove stories expirados
        Deve ser executado periodicamente (cron job)
        """
        from app import db
        from app.services import s3_service
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # Buscar stories expirados
            stories_expirados = Story.query.filter(
                Story.ativo == True,
                Story.expira_em < datetime.utcnow()
            ).all()
            
            count = len(stories_expirados)
            
            for story in stories_expirados:
                # Remover do S3
                if story.s3_key:
                    success, error = s3_service.delete_media(story.s3_key)
                    if not success:
                        logger.warning(f"Erro ao deletar story {story.id} do S3: {error}")
                
                # Marcar como inativo
                story.ativo = False
            
            db.session.commit()
            logger.info(f"{count} stories expirados foram limpos")
            
            return count
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao limpar stories expirados: {str(e)}")
            return 0


# ==================== EXEMPLO DE USO ====================
"""
# Criar post com imagem
file = request.files['imagem']
s3_key, error = s3_service.upload_helpzone_media(file, current_user.id, 'image', 'helpzone/posts/images')

if not error:
    post = Post(user_id=current_user.id, texto="Meu post", tipo_midia='imagem')
    db.session.add(post)
    db.session.flush()
    
    midia = PostMidia(post_id=post.id, tipo='image', s3_key=s3_key)
    db.session.add(midia)
    db.session.commit()
    
    # Para exibir a imagem:
    url_temporaria = midia.get_url()  # Válida por 1 hora


# Criar story
file = request.files['video']
s3_key, error = s3_service.upload_helpzone_media(file, current_user.id, 'video', 'helpzone/stories/videos')

if not error:
    story = Story(
        user_id=current_user.id,
        tipo='video',
        s3_key=s3_key,
        expira_em=datetime.utcnow() + timedelta(hours=24)
    )
    db.session.add(story)
    db.session.commit()
    
    # Para exibir o story:
    url_temporaria = story.get_url()  # Válida por 2 horas
"""
