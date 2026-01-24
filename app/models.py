from datetime import datetime

class FormsQuestao(db.Model):
    __tablename__ = 'forms_questoes'
    
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text, nullable=False)
    resposta_correta = db.Column(db.String(1), nullable=False)
    explicacao = db.Column(db.Text, nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamento com alternativas
    alternativas = db.relationship('FormsAlternativa', backref='questao', cascade='all, delete-orphan')

class FormsAlternativa(db.Model):
    __tablename__ = 'forms_alternativas'
    
    id = db.Column(db.Integer, primary_key=True)
    questao_id = db.Column(db.Integer, db.ForeignKey('forms_questoes.id'), nullable=False)
    letra = db.Column(db.String(1), nullable=False)  # A, B, C, D, E
    texto = db.Column(db.Text, nullable=False)

class FormsParticipante(db.Model):
    __tablename__ = 'forms_participantes'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    ano_escolar = db.Column(db.String(50), nullable=False)
    curso_desejado = db.Column(db.String(200), nullable=False)
    numero_sorte = db.Column(db.String(6), unique=True, nullable=False)
    acertos = db.Column(db.Integer, default=0)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Armazenar respostas
    respostas = db.Column(db.JSON)  # {'questao_id': 'letra_resposta'}
