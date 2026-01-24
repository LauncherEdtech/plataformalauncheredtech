from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)

    phone = db.Column(db.String(20), nullable=False)  # Novo campo para telefone com DDD

    password_hash = db.Column(db.Text, nullable=False)

	
    credits = db.Column(db.Integer, default=1)  # Inicia com 1 crédito
    
    essays = db.relationship('Essay', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class CompetenceFeedback(db.Model):
    __tablename__ = 'competence_feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    essay_id = db.Column(db.Integer, db.ForeignKey('essays.id'), nullable=False)
    numero = db.Column(db.Integer, nullable=False)
    nome = db.Column(db.String(255), nullable=False)
    nota = db.Column(db.Integer, nullable=False)
    justificativa = db.Column(db.Text, nullable=True)
    pontos_fortes = db.Column(db.Text, nullable=True)
    pontos_fracos = db.Column(db.Text, nullable=True)
    sugestoes = db.Column(db.Text, nullable=True)


class Essay(db.Model):
    __tablename__ = 'essays'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=True)
    text = db.Column(db.Text, nullable=False)
    feedback = db.Column(db.JSON, nullable=True)  # (opcional, se ainda quiser salvar o JSON completo)
    score_total = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Notas por competência (0-200) – (podem continuar, se desejar)
    comp1_score = db.Column(db.Integer, nullable=True)
    comp2_score = db.Column(db.Integer, nullable=True)
    comp3_score = db.Column(db.Integer, nullable=True)
    comp4_score = db.Column(db.Integer, nullable=True)
    comp5_score = db.Column(db.Integer, nullable=True)
    
    # Novo relacionamento com a tabela de feedback de competências:
    competence_feedbacks = db.relationship('CompetenceFeedback', backref='essay', lazy=True)
