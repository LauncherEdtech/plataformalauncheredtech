# app/models/redacao.py
# VERSÃO CORRIGIDA - Premiação com DIAMANTES ao invés de XP

from datetime import datetime
import json
from app import db
from flask import current_app
import logging

# Configurar logger
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class Redacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=True)  # Título opcional como no ENEM
    conteudo = db.Column(db.Text, nullable=False)  # Conteúdo continua obrigatório
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Campos de avaliação
    nota_final = db.Column(db.Integer, nullable=True)  # Nota final de 0-1000
    parecer_geral = db.Column(db.Text, nullable=True)  # Feedback geral
    
    # Notas por competência (0-200 pontos cada)
    competencia1 = db.Column(db.Integer, nullable=True)  # Domínio da norma culta
    competencia2 = db.Column(db.Integer, nullable=True)  # Compreensão da proposta
    competencia3 = db.Column(db.Integer, nullable=True)  # Organização textual e coerência
    competencia4 = db.Column(db.Integer, nullable=True)  # Mecanismos linguísticos
    competencia5 = db.Column(db.Integer, nullable=True)  # Proposta de intervenção
    
    # Feedbacks detalhados por competência
    feedback_comp1 = db.Column(db.Text, nullable=True)
    feedback_comp2 = db.Column(db.Text, nullable=True)
    feedback_comp3 = db.Column(db.Text, nullable=True)
    feedback_comp4 = db.Column(db.Text, nullable=True)
    feedback_comp5 = db.Column(db.Text, nullable=True)
    
    # Pontos fortes e fracos (armazenados como JSON)
    pontos_fortes_comp1 = db.Column(db.Text, nullable=True)  # JSON array
    pontos_fortes_comp2 = db.Column(db.Text, nullable=True)  # JSON array
    pontos_fortes_comp3 = db.Column(db.Text, nullable=True)  # JSON array
    pontos_fortes_comp4 = db.Column(db.Text, nullable=True)  # JSON array
    pontos_fortes_comp5 = db.Column(db.Text, nullable=True)  # JSON array
    
    pontos_fracos_comp1 = db.Column(db.Text, nullable=True)  # JSON array
    pontos_fracos_comp2 = db.Column(db.Text, nullable=True)  # JSON array
    pontos_fracos_comp3 = db.Column(db.Text, nullable=True)  # JSON array
    pontos_fracos_comp4 = db.Column(db.Text, nullable=True)  # JSON array
    pontos_fracos_comp5 = db.Column(db.Text, nullable=True)  # JSON array
    
    # Sugestões de melhoria (armazenadas como JSON)
    sugestoes_comp1 = db.Column(db.Text, nullable=True)  # JSON array
    sugestoes_comp2 = db.Column(db.Text, nullable=True)  # JSON array
    sugestoes_comp3 = db.Column(db.Text, nullable=True)  # JSON array
    sugestoes_comp4 = db.Column(db.Text, nullable=True)  # JSON array
    sugestoes_comp5 = db.Column(db.Text, nullable=True)  # JSON array
    
    # Armazenar dados de processamento
    tema = db.Column(db.String(255), nullable=True)  # Tema da redação
    prompt_usado = db.Column(db.Text, nullable=True)  # Prompt enviado para a API
    resposta_api = db.Column(db.Text, nullable=True)  # Resposta bruta da API
    
    # Acompanhamento de status
    status = db.Column(db.String(50), default="Enviada")  # Enviada, Em análise, Avaliada, Erro
    
    # Moedas concedidas
    moedas_concedidas = db.Column(db.Boolean, default=False)  # Indica se já foram concedidas moedas
    
    # Chave estrangeira
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __repr__(self):
        titulo_display = self.titulo or f"Redação #{self.id}"
        return f'<Redacao {self.id}: {titulo_display}>'
    
    @property
    def titulo_display(self):
        """Retorna o título da redação ou um título padrão se não houver"""
        if self.titulo and self.titulo.strip():
            return self.titulo
        return f"Redação de {self.data_envio.strftime('%d/%m/%Y')}"
    
    def calcular_nota_final(self):
        """Calcula a nota final baseada nas competências"""
        logger.info(f"Calculando nota final para redação ID {self.id}")
        if None in [self.competencia1, self.competencia2, self.competencia3, self.competencia4, self.competencia5]:
            logger.warning(f"Redação ID {self.id} possui competências não avaliadas")
            return None
        
        nota = self.competencia1 + self.competencia2 + self.competencia3 + self.competencia4 + self.competencia5
        logger.info(f"Nota final calculada: {nota} para redação ID {self.id}")
        return nota
    
    def get_pontos_fortes(self, competencia):
        """Obtém os pontos fortes para uma competência específica"""
        column_name = f"pontos_fortes_comp{competencia}"
        json_data = getattr(self, column_name)
        
        if not json_data:
            return []
            
        try:
            return json.loads(json_data)
        except json.JSONDecodeError:
            logger.error(f"Erro ao decodificar pontos fortes da competência {competencia}")
            return []
    
    def get_pontos_fracos(self, competencia):
        """Obtém os pontos fracos para uma competência específica"""
        column_name = f"pontos_fracos_comp{competencia}"
        json_data = getattr(self, column_name)
        
        if not json_data:
            return []
            
        try:
            return json.loads(json_data)
        except json.JSONDecodeError:
            logger.error(f"Erro ao decodificar pontos fracos da competência {competencia}")
            return []
    
    def get_sugestoes(self, competencia):
        """Obtém as sugestões para uma competência específica"""
        column_name = f"sugestoes_comp{competencia}"
        json_data = getattr(self, column_name)
        
        if not json_data:
            return []
            
        try:
            return json.loads(json_data)
        except json.JSONDecodeError:
            logger.error(f"Erro ao decodificar sugestões da competência {competencia}")
            return []
    

    def conceder_moedas(self):
        """
        ✅ VERSÃO FINAL CORRIGIDA: Concede DIAMANTES usando campo 'descricao'
        """
        from app.models.user import User
        from app.models.estudo import Moeda
        
        # Verifica se os diamantes já foram concedidos
        if self.moedas_concedidas:
            logger.info(f"💎 Diamantes já concedidos anteriormente para redação ID {self.id}")
            return False
        
        # Verifica se a nota está definida
        if not self.nota_final:
            self.nota_final = self.calcular_nota_final()
            if not self.nota_final:
                logger.warning(f"⚠️ Não foi possível calcular a nota final para redação ID {self.id}")
                return False
        
        # ✅ CÁLCULO DE DIAMANTES (nota/10, mínimo 10)
        diamantes = max(self.nota_final // 10, 10)
        
        logger.info(f"💰 Calculando diamantes para redação ID {self.id}: {diamantes} 💎 (Nota: {self.nota_final})")
        
        # Adiciona os diamantes ao usuário
        usuario = User.query.get(self.user_id)
        if not usuario:
            logger.error(f"❌ Usuário ID {self.user_id} não encontrado ao conceder diamantes")
            return False
        
        logger.info(f"👤 Concedendo {diamantes} diamantes ao usuário {usuario.nome_completo} (ID: {self.user_id})")
        
        # ✅ ATUALIZAR O CAMPO user.diamantes (ESSENCIAL PARA O FRONTEND!)
        usuario.diamantes = (usuario.diamantes or 0) + diamantes
        logger.info(f"💎 Saldo atualizado: {usuario.diamantes} diamantes total")
        
        # ✅ CRIAR REGISTRO DE MOEDA (para histórico)
        moeda = Moeda(
            user_id=self.user_id,
            quantidade=diamantes,
            tipo="redacao",
            descricao=f"Redação: {self.titulo_display} (Nota: {self.nota_final})",
            data=datetime.utcnow()
        )
        db.session.add(moeda)
        
        # Marcar como concedido
        self.moedas_concedidas = True
        
        try:
            db.session.commit()
            logger.info(f"✅ {diamantes} diamantes concedidos com sucesso! Total agora: {usuario.diamantes} 💎")
            return diamantes
        except Exception as e:
            logger.error(f"❌ Erro ao salvar diamantes: {e}")
            db.session.rollback()
            return False
    
    def to_dict(self):
        """Converte a redação para dicionário (útil para JSONs)"""
        return {
            'id': self.id,
            'titulo': self.titulo_display,
            'titulo_original': self.titulo,
            'tema': self.tema,
            'conteudo': self.conteudo,
            'data_envio': self.data_envio.isoformat() if self.data_envio else None,
            'nota_final': self.nota_final,
            'competencia1': self.competencia1,
            'competencia2': self.competencia2,
            'competencia3': self.competencia3,
            'competencia4': self.competencia4,
            'competencia5': self.competencia5,
            'status': self.status,
            'moedas_concedidas': self.moedas_concedidas
        }
