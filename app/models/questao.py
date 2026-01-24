# app/models/questao.py
from app import db
from datetime import datetime

class QuestaoBase(db.Model):
    """Modelo base para questões do banco de questões"""
    __tablename__ = 'questoes_base'
    
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text, nullable=False)
    materia = db.Column(db.String(50), nullable=False)  # Português, Matemática, etc.
    topico = db.Column(db.String(100), nullable=False)  # Tópico específico
    subtopico = db.Column(db.String(100), nullable=True)  # Subtópico
    
    # Alternativas
    opcao_a = db.Column(db.Text, nullable=False)
    opcao_b = db.Column(db.Text, nullable=False) 
    opcao_c = db.Column(db.Text, nullable=False)
    opcao_d = db.Column(db.Text, nullable=False)
    opcao_e = db.Column(db.Text, nullable=False)
    
    # Resposta correta e explicação
    resposta_correta = db.Column(db.String(1), nullable=False)  # A, B, C, D ou E
    explicacao = db.Column(db.Text, nullable=False)
    
    # Imagem (se houver)
    imagem_url = db.Column(db.String(255), nullable=True)
    
    # Metadados
    dificuldade = db.Column(db.Float, default=0.5)  # Para cálculo TRI (0.0 a 1.0)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    ativa = db.Column(db.Boolean, default=True)
    
    # Estatísticas de uso
    vezes_utilizada = db.Column(db.Integer, default=0)
    vezes_acertada = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<QuestaoBase {self.id}: {self.materia} - {self.topico}>'
    
    @property
    def percentual_acerto(self):
        """Calcula o percentual de acerto da questão"""
        if self.vezes_utilizada == 0:
            return 0
        return (self.vezes_acertada / self.vezes_utilizada) * 100
    
    def get_alternativas_dict(self):
        """Retorna as alternativas como um dicionário"""
        return {
            'A': self.opcao_a,
            'B': self.opcao_b,
            'C': self.opcao_c,
            'D': self.opcao_d,
            'E': self.opcao_e
        }
    
    def incrementar_uso(self, acertou=False):
        """Incrementa as estatísticas de uso da questão"""
        self.vezes_utilizada += 1
        if acertou:
            self.vezes_acertada += 1
        db.session.commit()


class Questao(db.Model):
    """Modelo para questões em simulados (mantém o modelo original)"""
    __tablename__ = 'questoes'
    
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.Integer)
    texto = db.Column(db.Text)
    area = db.Column(db.String(50))  # Linguagens, Matemática, etc.
    dificuldade = db.Column(db.Float)  # Para cálculo TRI
    resposta_correta = db.Column(db.String(1))  # A, B, C, D ou E
    resposta_usuario = db.Column(db.String(1), nullable=True)
    
    # Referência para a questão base
    questao_base_id = db.Column(db.Integer, db.ForeignKey('questoes_base.id'), nullable=True)
    
    # Tempo de resposta
    tempo_resposta = db.Column(db.Integer, nullable=True)  # tempo em segundos
    
    # Chave estrangeira
    simulado_id = db.Column(db.Integer, db.ForeignKey('simulado.id'))
    
    # Relacionamentos
    alternativas = db.relationship('Alternativa', backref='questao', lazy='dynamic')
    questao_base = db.relationship('QuestaoBase', backref='questoes_simulado')
    
    def __repr__(self):
        return f'<Questao {self.id}>'
    
    def verificar_resposta(self):
        return self.resposta_usuario == self.resposta_correta


class Alternativa(db.Model):
    """Modelo para alternativas (mantém o modelo original)"""
    __tablename__ = 'alternativas'
    
    id = db.Column(db.Integer, primary_key=True)
    letra = db.Column(db.String(1))  # A, B, C, D ou E
    texto = db.Column(db.Text)
    
    # Chave estrangeira
    questao_id = db.Column(db.Integer, db.ForeignKey('questoes.id'))
    
    def __repr__(self):
        return f'<Alternativa {self.letra}>'