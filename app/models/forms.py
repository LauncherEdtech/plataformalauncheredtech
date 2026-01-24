"""
Models para o Formulário ENEM - Ação nas Escolas
"""
from app import db
from datetime import datetime


class FormsQuestao(db.Model):
    """Questões do formulário ENEM"""
    __tablename__ = 'forms_questoes'
    
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text, nullable=False)
    resposta_correta = db.Column(db.String(1), nullable=False)
    explicacao = db.Column(db.Text, nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamento com alternativas
    alternativas = db.relationship('FormsAlternativa', backref='questao', 
                                   cascade='all, delete-orphan', lazy='joined')
    
    def __repr__(self):
        return f'<FormsQuestao {self.id}>'


class FormsAlternativa(db.Model):
    """Alternativas das questões"""
    __tablename__ = 'forms_alternativas'
    
    id = db.Column(db.Integer, primary_key=True)
    questao_id = db.Column(db.Integer, db.ForeignKey('forms_questoes.id'), nullable=False)
    letra = db.Column(db.String(1), nullable=False)  # A, B, C, D, E
    texto = db.Column(db.Text, nullable=False)
    
    def __repr__(self):
        return f'<FormsAlternativa {self.letra}>'


class FormsParticipante(db.Model):
    """Participantes do formulário"""
    __tablename__ = 'forms_participantes'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False, index=True)
    telefone = db.Column(db.String(20), nullable=False)
    ano_escolar = db.Column(db.String(50), nullable=False)
    curso_desejado = db.Column(db.String(200), nullable=False)
    numero_sorte = db.Column(db.String(6), unique=True, nullable=False, index=True)
    acertos = db.Column(db.Integer, default=0)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # JSON com as respostas do participante
    respostas = db.Column(db.JSON)
    
    def __repr__(self):
        return f'<FormsParticipante {self.nome} - {self.numero_sorte}>'
