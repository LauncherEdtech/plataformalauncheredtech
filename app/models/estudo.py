# app/models/estudo.py
from datetime import datetime
from app import db
from sqlalchemy.orm import backref

# ==========================
# Núcleo: Matérias / Módulos / Aulas
# ==========================
class Materia(db.Model):
    __tablename__ = 'materia'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    icone = db.Column(db.String(10), default='📖')
    cor = db.Column(db.String(7), default='#00b4d8')
    capa_url = db.Column(db.String(200))   # imagem de capa
    ordem = db.Column(db.Integer, default=0)
    ativa = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    # 🔑 CHAVE PARA SEÇÕES INDEPENDENTES
    # NULL = matéria do núcleo global
    # Valor = matéria exclusiva desta seção
    secao_id = db.Column(db.Integer, db.ForeignKey('secao.id'), nullable=True)

    # relacionamentos
    modulos = db.relationship(
        'Modulo', backref='materia', lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<Materia {self.nome}>'

    @property
    def imagem_url(self):
        return self.capa_url or 'images/covers/placeholder-subject.jpg'

    @property
    def total_modulos(self):
        return self.modulos.count()

    @property
    def escopo_descricao(self):
        """Retorna descrição do escopo da matéria"""
        if self.secao_id:
            return f"Seção: {self.secao.titulo if hasattr(self, 'secao') else 'N/A'}"
        return "Núcleo Global"

    def progresso_usuario(self, user_id):
        from app.models.estudo import Modulo, Aula, ProgressoAula
        total_aulas = db.session.query(Aula).join(Modulo).filter(
            Modulo.materia_id == self.id,
            Aula.ativa == True
        ).count()
        if total_aulas == 0:
            return 0
        aulas_concluidas = db.session.query(ProgressoAula).join(Aula).join(Modulo).filter(
            Modulo.materia_id == self.id,
            ProgressoAula.user_id == user_id,
            ProgressoAula.concluida == True
        ).count()
        return (aulas_concluidas / total_aulas) * 100


class Modulo(db.Model):
    __tablename__ = 'modulo'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text)
    materia_id = db.Column(db.Integer, db.ForeignKey('materia.id'), nullable=False)
    ordem = db.Column(db.Integer, default=0)
    duracao_estimada = db.Column(db.Integer)  # em minutos
    dificuldade = db.Column(db.String(20), default='medio')  # facil/medio/dificil
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    aulas = db.relationship(
        'Aula', backref='modulo', lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<Modulo {self.titulo}>'

    def progresso_usuario(self, user_id):
        from app.models.estudo import Aula, ProgressoAula
        total_aulas = self.aulas.filter_by(ativa=True).count()
        if total_aulas == 0:
            return 0
        aulas_concluidas = db.session.query(ProgressoAula).join(Aula).filter(
            Aula.modulo_id == self.id,
            ProgressoAula.user_id == user_id,
            ProgressoAula.concluida == True
        ).count()
        return (aulas_concluidas / total_aulas) * 100


class Aula(db.Model):
    __tablename__ = 'aula'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text)
    conteudo = db.Column(db.Text)
    modulo_id = db.Column(db.Integer, db.ForeignKey('modulo.id'), nullable=False)
    ordem = db.Column(db.Integer, default=0)
    duracao_estimada = db.Column(db.Integer)  # em minutos
    tipo = db.Column(db.String(20), default='texto')  # texto, video, pdf...
    url_video = db.Column(db.String(500))
    url_pdf = db.Column(db.String(500))
    ativa = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    materiais = db.relationship(
        'MaterialAula', backref='aula', lazy='dynamic',
        cascade='all, delete-orphan'
    )
    progressos = db.relationship(
        'ProgressoAula', backref='aula', lazy='dynamic',
        cascade='all, delete-orphan'
    )
    sessoes = db.relationship(
        'SessaoEstudo', backref='aula', lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<Aula {self.titulo}>'

    def progresso_usuario(self, user_id):
        from app.models.estudo import ProgressoAula
        if not self.duracao_estimada:
            return 0
        progresso = ProgressoAula.query.filter_by(
            user_id=user_id, aula_id=self.id
        ).first()
        if not progresso:
            return 0
        total = self.duracao_estimada * 60
        return min((progresso.tempo_assistido / total) * 100, 100)


class MaterialAula(db.Model):
    __tablename__ = 'material_aula'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    arquivo = db.Column(db.String(500))
    tipo = db.Column(db.String(10))
    aula_id = db.Column(db.Integer, db.ForeignKey('aula.id'), nullable=False)
    data_upload = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<MaterialAula {self.nome}>'


class ProgressoAula(db.Model):
    __tablename__ = 'progresso_aula'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    aula_id = db.Column(db.Integer, db.ForeignKey('aula.id'), nullable=False)
    tempo_assistido = db.Column(db.Integer, default=0)  # em segundos
    concluida = db.Column(db.Boolean, default=False)
    data_inicio = db.Column(db.DateTime, default=datetime.utcnow)
    data_conclusao = db.Column(db.DateTime)
    ultima_atividade = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    anotacoes = db.Column(db.Text)

    __table_args__ = (db.UniqueConstraint('user_id', 'aula_id', name='unique_user_aula'),)

    usuario = db.relationship('User', backref=db.backref('progressos_aula', lazy='dynamic'))

    def __repr__(self):
        return f'<ProgressoAula {self.user_id}-{self.aula_id}>'


class SessaoEstudo(db.Model):
    __tablename__ = 'sessao_estudo'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    aula_id = db.Column(db.Integer, db.ForeignKey('aula.id'), nullable=False)
    inicio = db.Column(db.DateTime, default=datetime.utcnow)
    fim = db.Column(db.DateTime)
    tempo_ativo = db.Column(db.Integer, default=0)  # em segundos
    ativa = db.Column(db.Boolean, default=True)
    moedas_ganhas = db.Column(db.Integer, default=0)

    usuario = db.relationship('User', backref=db.backref('sessoes_estudo', lazy='dynamic'))

    def __repr__(self):
        return f'<SessaoEstudo {self.id}>'

    def finalizar(self):
        if self.ativa:
            self.fim = datetime.utcnow()
            self.ativa = False
            if self.inicio:
                self.tempo_ativo = int((self.fim - self.inicio).total_seconds())


class Moeda(db.Model):
    __tablename__ = 'moeda'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)  # + ganho / - gasto
    tipo = db.Column(db.String(50))  # estudo, simulado, helpzone, compra...
    descricao = db.Column(db.String(200))
    data = db.Column(db.DateTime, default=datetime.utcnow)


# ==========================
# SEÇÕES INDEPENDENTES
# ==========================
class Secao(db.Model):
    __tablename__ = 'secao'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(120), nullable=False)
    subtitulo = db.Column(db.String(180))
    descricao = db.Column(db.Text)
    icone = db.Column(db.String(12), default='🧩')
    cor = db.Column(db.String(7), default='#00b4d8')
    grid_cols = db.Column(db.Integer, default=4)
    ordem = db.Column(db.Integer, default=0)
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    # 🔗 Relacionamento direto com matérias exclusivas
    materias = db.relationship(
        'Materia',
        backref='secao',
        lazy='dynamic',
        foreign_keys='Materia.secao_id'
    )

    def __repr__(self):
        return f'<Secao {self.titulo}>'

    @property
    def total_materias(self):
        """Total de matérias exclusivas desta seção"""
        return self.materias.filter(Materia.ativa == True).count()

    @property
    def total_modulos(self):
        """Total de módulos em todas as matérias desta seção"""
        from app.models.estudo import Modulo
        return db.session.query(Modulo).join(Materia).filter(
            Materia.secao_id == self.id,
            Materia.ativa == True,
            Modulo.ativo == True
        ).count()

    @property
    def total_aulas(self):
        """Total de aulas em todas as matérias desta seção"""
        from app.models.estudo import Aula, Modulo
        return db.session.query(Aula).join(Modulo).join(Materia).filter(
            Materia.secao_id == self.id,
            Materia.ativa == True,
            Modulo.ativo == True,
            Aula.ativa == True
        ).count()

    def get_materias_ativas(self):
        """Retorna matérias ativas ordenadas"""
        return self.materias.filter(Materia.ativa == True).order_by(Materia.ordem, Materia.id)




# === ADICIONAR NO FINAL DO ARQUIVO estudo.py ===

from datetime import datetime, timedelta
from sqlalchemy import JSON

class Cronograma(db.Model):
    """Cronograma personalizado do usuário"""
    __tablename__ = 'cronograma'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Configurações do cronograma
    objetivo = db.Column(db.String(200))  # Ex: "Passar no ENEM", "Concurso Público"
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim_prevista = db.Column(db.Date)
    data_prova = db.Column(db.Date)  # Data da prova/objetivo (se houver)
    
    # Rotina do usuário
    horas_disponiveis_semana = db.Column(db.Integer)  # Total de horas por semana
    dias_estudo = db.Column(JSON)  # Lista: ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]
    horas_por_dia = db.Column(JSON)  # Dict: {"seg": 2, "ter": 3, ...}
    periodo_preferencia = db.Column(db.String(20))  # manhã, tarde, noite, flexível
    
    # Preferências
    nivel_atual = db.Column(db.String(20), default='intermediario')  # iniciante, intermediario, avancado
    priorizar_dificuldade = db.Column(db.Boolean, default=True)  # Começar do mais fácil?
    incluir_revisoes = db.Column(db.Boolean, default=True)
    
    # Metadados
    ativo = db.Column(db.Boolean, default=True)
    concluido = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    ultima_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    


    incluir_simulados = db.Column(db.Boolean, default=True)
    incluir_redacoes = db.Column(db.Boolean, default=True)


    # Relacionamentos
    itens = db.relationship('ItemCronograma', backref='cronograma', lazy='dynamic', 
                           cascade='all, delete-orphan', order_by='ItemCronograma.data_prevista')
    usuario = db.relationship('User', backref=db.backref('cronogramas', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Cronograma {self.id} - {self.usuario.username if self.usuario else "Unknown"}>'
    
    @property
    def progresso_geral(self):
        """Calcula o progresso geral do cronograma"""
        total = self.itens.count()
        if total == 0:
            return 0
        concluidos = self.itens.filter_by(concluido=True).count()
        return (concluidos / total) * 100
    
    @property
    def itens_atrasados(self):
        """Retorna itens atrasados"""
        hoje = datetime.now().date()
        return self.itens.filter(
            ItemCronograma.data_prevista < hoje,
            ItemCronograma.concluido == False
        ).count()
    
    @property
    def proxima_aula(self):
        """Retorna a próxima aula não concluída"""
        return self.itens.filter_by(concluido=False).order_by(
            ItemCronograma.data_prevista, ItemCronograma.ordem_no_dia
        ).first()
    
    @property
    def aulas_hoje(self):
        """Retorna aulas previstas para hoje"""
        hoje = datetime.now().date()
        return self.itens.filter_by(data_prevista=hoje, concluido=False).all()
    
    def get_aulas_semana(self):
        """Retorna aulas da semana atual"""
        hoje = datetime.now().date()
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        fim_semana = inicio_semana + timedelta(days=6)
        
        return self.itens.filter(
            ItemCronograma.data_prevista.between(inicio_semana, fim_semana)
        ).all()


class ItemCronograma(db.Model):
    """Item individual do cronograma (uma aula)"""
    __tablename__ = 'item_cronograma'
    
    id = db.Column(db.Integer, primary_key=True)
    cronograma_id = db.Column(db.Integer, db.ForeignKey('cronograma.id'), nullable=False)
    aula_id = db.Column(db.Integer, db.ForeignKey('aula.id'), nullable=False)
    
    # Planejamento
    data_prevista = db.Column(db.Date, nullable=False)
    ordem_no_dia = db.Column(db.Integer, default=1)  # Se há múltiplas aulas no dia
    tempo_previsto = db.Column(db.Integer)  # Tempo em minutos
    
    # Status
    concluido = db.Column(db.Boolean, default=False)
    data_conclusao = db.Column(db.DateTime)
    tempo_real = db.Column(db.Integer)  # Tempo real gasto em minutos
    
    # Tipo de atividade
    tipo_item = db.Column(db.String(20), default='aula')  # aula, revisao, simulado
    
    # Notas/observações do usuário
    observacoes = db.Column(db.Text)
    
    # Relacionamento com a aula
    aula = db.relationship('Aula', backref='itens_cronograma')
    
    __table_args__ = (
        db.Index('idx_cronograma_data', 'cronograma_id', 'data_prevista'),
    )
    
    def __repr__(self):
        return f'<ItemCronograma {self.id} - Aula {self.aula_id} em {self.data_prevista}>'
    
    def marcar_concluido(self):
        """Marca o item como concluído"""
        self.concluido = True
        self.data_conclusao = datetime.utcnow()
    
    @property
    def esta_atrasado(self):
        """Verifica se o item está atrasado"""
        if self.concluido:
            return False
        return self.data_prevista < datetime.now().date()
    
    @property
    def dias_para_vencimento(self):
        """Retorna quantos dias faltam para o vencimento"""
        if self.concluido:
            return None
        delta = self.data_prevista - datetime.now().date()
        return delta.days










