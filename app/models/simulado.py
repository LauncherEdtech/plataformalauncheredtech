# app/models/simulado.py
from datetime import datetime
import math
import numpy as np
from app import db
from flask import current_app

class Simulado(db.Model):
    __tablename__ = 'simulado' 
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.Integer)
    titulo = db.Column(db.String(120))
    areas = db.Column(db.String(120))  # Ex: "Linguagens e Natureza"
    duracao_minutos = db.Column(db.Integer)
    data_agendada = db.Column(db.DateTime, nullable=True)
    data_realizado = db.Column(db.DateTime, nullable=True)
    tempo_realizado = db.Column(db.String(20), nullable=True)  # Ex: "01h46"
    status = db.Column(db.String(20), default="Pendente")  # Pendente, Concluído
    nota_tri = db.Column(db.Float, nullable=True)

  # ✨ NOVOS CAMPOS ADICIONADOS
    tipo = db.Column(db.String(20), default='enem')  # 'enem' ou 'individual'
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    
    # Novos campos para métricas mais detalhadas
    tempo_medio_por_questao = db.Column(db.Float, nullable=True)  # em segundos
    questoes_puladas = db.Column(db.Integer, default=0)
    acertos_total = db.Column(db.Integer, default=0)
    
    # Chaves estrangeiras
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relacionamentos
    questoes = db.relationship('Questao', backref='simulado', lazy='dynamic')
    
    def __repr__(self):
        return f'<Simulado {self.numero}: {self.titulo}>'
    
    def calcular_nota_tri(self):
        """
        Implementa um cálculo TRI (Teoria de Resposta ao Item) simplificado
        baseado na dificuldade das questões e no padrão de acertos.
        """
        questoes = list(self.questoes)
        if not questoes:
            return 0
        
        # Contagem básica de acertos
        acertos = 0
        total = len(questoes)
        
        # Parâmetros para peso das questões por dificuldade
        soma_pesos = 0
        soma_acertos_ponderados = 0
        
        # Análise de consistência - penalização por inconsistência
        # (ex: errar questões fáceis e acertar difíceis)
        inconsistencias = 0
        
        # Ordenar questões por dificuldade
        questoes_ordenadas = sorted(questoes, key=lambda q: q.dificuldade)
        
        for i, questao in enumerate(questoes):
            # Verificar acerto
            acerto = questao.verificar_resposta()
            if acerto:
                acertos += 1
            
            # Peso baseado na dificuldade
            peso = 1 + (questao.dificuldade * 2)  # Questões mais difíceis têm mais peso
            soma_pesos += peso
            
            if acerto:
                soma_acertos_ponderados += peso
            
            # Verificar inconsistências
            # Se uma questão mais difícil foi acertada e uma mais fácil foi errada
            if i > 0 and acerto and not questoes_ordenadas[i-1].verificar_resposta():
                if questao.dificuldade > questoes_ordenadas[i-1].dificuldade + 0.2:
                    inconsistencias += 1
        
        # Calcular taxa básica de acertos
        taxa_acertos = acertos / total if total > 0 else 0
        
        # Calcular taxa ponderada
        taxa_ponderada = soma_acertos_ponderados / soma_pesos if soma_pesos > 0 else 0
        
        # Penalização por inconsistência
        fator_consistencia = max(0, 1 - (inconsistencias * 0.05))
        
        # Fórmula final do TRI
        # Baseada em taxa ponderada, com ajuste de consistência, e escala de 0-1000
        nota_base = taxa_ponderada * 1000
        nota_ajustada = nota_base * fator_consistencia
        
        # Ajustar para escala ENEM (mínimo 400 se tiver pelo menos um acerto)
        nota_final = max(400, min(800, nota_ajustada)) if acertos > 0 else 0
        
        # Salvar o total de acertos para estatísticas
        self.acertos_total = acertos
        
        return round(nota_final, 1)
    
    def calcular_estatisticas(self):
        """
        Calcula métricas adicionais sobre o desempenho no simulado.
        """
        questoes = list(self.questoes)
        if not questoes:
            return
            
        # Calcular tempo médio por questão
        if self.data_realizado and self.tempo_realizado:
            # Converter o tempo total para segundos
            tempo_str = self.tempo_realizado
            horas = int(tempo_str.split('h')[0])
            minutos = int(tempo_str.split('h')[1])
            tempo_total_segundos = (horas * 3600) + (minutos * 60)
            
            # Calcular média
            self.tempo_medio_por_questao = tempo_total_segundos / len(questoes)
            
        # Contar questões não respondidas
        self.questoes_puladas = sum(1 for q in questoes if q.resposta_usuario is None)
        
        # Calcular acertos
        self.acertos_total = sum(1 for q in questoes if q.verificar_resposta())


class Questao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.Integer)
    texto = db.Column(db.Text)
    area = db.Column(db.String(50))  # Linguagens, Matemática, etc.
    dificuldade = db.Column(db.Float)  # Para cálculo TRI
    resposta_correta = db.Column(db.String(1))  # A, B, C, D ou E
    resposta_usuario = db.Column(db.String(1), nullable=True)
    
    # Novos campos para análise detalhada
    tempo_resposta = db.Column(db.Integer, nullable=True)  # tempo em segundos que levou para responder
    
    # Chave estrangeira
    simulado_id = db.Column(db.Integer, db.ForeignKey('simulado.id'))
    
    # Relacionamentos
    alternativas = db.relationship('Alternativa', backref='questao', lazy='dynamic')
    
    def __repr__(self):
        return f'<Questao {self.id}>'
    
    def verificar_resposta(self):
        return self.resposta_usuario == self.resposta_correta


class Alternativa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    letra = db.Column(db.String(1))  # A, B, C, D ou E
    texto = db.Column(db.Text)
    
    # Chave estrangeira
    questao_id = db.Column(db.Integer, db.ForeignKey('questao.id'))
    
    def __repr__(self):
        return f'<Alternativa {self.letra}>'
