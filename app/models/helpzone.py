# app/models/helpzone.py

from datetime import datetime
from app import db
from flask import current_app, url_for
from sqlalchemy import func

class Duvida(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    resolvida = db.Column(db.Boolean, default=False)
    area = db.Column(db.String(50))  # Ex: #quimica, #redacao, #matematica
    
    # Chaves estrangeiras
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relacionamentos
    respostas = db.relationship('Resposta', backref='duvida', lazy='dynamic')
    votos = db.relationship('DuvidaVoto', backref='duvida', lazy='dynamic')
    
    def __repr__(self):
        return f'<Dúvida {self.id}: {self.titulo}>'
    
    def total_votos(self):
        return sum([voto.valor for voto in self.votos])
    
class Resposta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conteudo = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    solucao = db.Column(db.Boolean, default=False)  # Marca se é a resposta aceita
    
    # Chaves estrangeiras
    duvida_id = db.Column(db.Integer, db.ForeignKey('duvida.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relacionamentos
    votos = db.relationship('RespostaVoto', backref='resposta', lazy='dynamic')
    
    def __repr__(self):
        return f'<Resposta {self.id} para Dúvida {self.duvida_id}>'
    
    def total_votos(self):
        return sum([voto.valor for voto in self.votos])

class DuvidaVoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    valor = db.Column(db.Integer, default=0)  # 1 = upvote, -1 = downvote
    
    # Chaves estrangeiras
    duvida_id = db.Column(db.Integer, db.ForeignKey('duvida.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    __table_args__ = (
        db.UniqueConstraint('duvida_id', 'user_id', name='unique_duvida_vote'),
    )

class RespostaVoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    valor = db.Column(db.Integer, default=0)  # 1 = upvote, -1 = downvote
    
    # Chaves estrangeiras
    resposta_id = db.Column(db.Integer, db.ForeignKey('resposta.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    __table_args__ = (
        db.UniqueConstraint('resposta_id', 'user_id', name='unique_resposta_vote'),
    )

class Notificacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    conteudo = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255))
    lida = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Notificacao {self.id}>'

class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    icon = db.Column(db.String(100), nullable=False)  # Nome do ícone Bootstrap ou caminho da imagem
    cor = db.Column(db.String(20), nullable=False, default="primary")  # Classe de cor Bootstrap
    req_quantidade = db.Column(db.Integer, default=0)  # Quantidade necessária para conquistar
    req_tipo = db.Column(db.String(20), nullable=False)  # respostas, solucoes, votos, etc.
    
    def __repr__(self):
        return f'<Badge {self.nome}>'

class UserBadge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    badge_id = db.Column(db.Integer, db.ForeignKey('badge.id'))
    data_conquista = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    badge = db.relationship('Badge', backref='usuarios_que_conquistaram', lazy='joined')
    
    def __repr__(self):
        return f'<UserBadge {self.user_id} - {self.badge_id}>'