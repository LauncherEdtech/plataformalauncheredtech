from app import db
from datetime import datetime
from flask import current_app


class Estatistica(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    creditos_disponiveis = db.Column(db.Integer, default=0)
    media_notas = db.Column(db.Float, default=0.0)
    melhor_nota = db.Column(db.Float, default=0.0)
    redacoes_enviadas = db.Column(db.Integer, default=0)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Estatisticas do usuário {self.user_id}>'
    
    @classmethod
    def get_or_create(cls, user_id):
        """Retorna as estatísticas do usuário ou cria se não existir."""
        stats = cls.query.filter_by(user_id=user_id).first()
        if not stats:
            stats = cls(user_id=user_id)
            db.session.add(stats)
            db.session.commit()
        return stats