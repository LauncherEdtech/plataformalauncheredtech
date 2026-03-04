# app/models/questao_diagnostico.py
from app import db
from datetime import datetime

class QuestaoDiagnostico(db.Model):
    """Modelo para questões do diagnóstico ENEM"""
    __tablename__ = 'questoes_diagnostico'
    
    id = db.Column(db.Integer, primary_key=True)
    enunciado = db.Column(db.Text, nullable=False)
    opcao_a = db.Column(db.Text, nullable=False)
    opcao_b = db.Column(db.Text, nullable=False)
    opcao_c = db.Column(db.Text, nullable=False)
    opcao_d = db.Column(db.Text, nullable=False)
    opcao_e = db.Column(db.Text, nullable=False)
    resposta_correta = db.Column(db.String(1), nullable=False)  # A, B, C, D ou E
    dificuldade = db.Column(db.String(10))  # facil, media, dificil
    area = db.Column(db.String(50))  # Ciências da Natureza, Linguagens, etc.
    ordem = db.Column(db.Integer)
    ativa = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<QuestaoDiagnostico {self.id}: {self.area}>'
    
    def get_alternativas_dict(self):
        """Retorna as alternativas como um dicionário"""
        return {
            'A': self.opcao_a,
            'B': self.opcao_b,
            'C': self.opcao_c,
            'D': self.opcao_d,
            'E': self.opcao_e
        }
