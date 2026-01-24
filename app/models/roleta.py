# app/models/roleta.py
from datetime import datetime, timedelta
from app import db

class RoletaPrimeiroAcesso(db.Model):
    """
    Controla a roleta do primeiro acesso e o prêmio ganho
    """
    __tablename__ = 'roleta_primeiro_acesso'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    data_giro = db.Column(db.DateTime, default=datetime.utcnow)
    produto_ganho_id = db.Column(db.Integer, db.ForeignKey('produto.id'))
    data_liberacao_resgate = db.Column(db.DateTime)  # Data que pode resgatar
    foi_resgatado = db.Column(db.Boolean, default=False)
    resgate_id = db.Column(db.Integer, db.ForeignKey('resgate.id'), nullable=True)
    
    # Relacionamentos
    usuario = db.relationship('User', backref='roleta_primeiro_acesso')
    produto_ganho = db.relationship('Produto', backref='ganhadores_roleta')
    
    def __init__(self, user_id, produto_id, dias_espera=8):
        self.user_id = user_id
        self.produto_ganho_id = produto_id
        self.data_giro = datetime.utcnow()
        self.data_liberacao_resgate = datetime.utcnow() + timedelta(days=dias_espera)
        self.foi_resgatado = False
    
    @property
    def pode_resgatar(self):
        """Verifica se já passou o tempo de espera"""
        if self.foi_resgatado:
            return False
        return datetime.utcnow() >= self.data_liberacao_resgate
    
    @property
    def dias_restantes(self):
        """Retorna quantos dias faltam para poder resgatar"""
        if self.pode_resgatar:
            return 0
        delta = self.data_liberacao_resgate - datetime.utcnow()
        return max(0, delta.days + 1)  # +1 para arredondar para cima
    
    @property
    def horas_restantes(self):
        """Retorna quantas horas faltam para poder resgatar"""
        if self.pode_resgatar:
            return 0
        delta = self.data_liberacao_resgate - datetime.utcnow()
        return max(0, int(delta.total_seconds() / 3600))
    
    def to_dict(self):
        return {
            'id': self.id,
            'produto': self.produto_ganho.nome if self.produto_ganho else None,
            'data_giro': self.data_giro.isoformat() if self.data_giro else None,
            'pode_resgatar': self.pode_resgatar,
            'dias_restantes': self.dias_restantes,
            'horas_restantes': self.horas_restantes,
            'foi_resgatado': self.foi_resgatado,
            'data_liberacao': self.data_liberacao_resgate.isoformat() if self.data_liberacao_resgate else None
        }
