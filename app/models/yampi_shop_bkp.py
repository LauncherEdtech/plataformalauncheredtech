# app/models/yampi_shop.py - Sistema de desconto Yampi com diamantes
# Atualizado para incluir descrição HTML e múltiplas imagens

from datetime import datetime, timedelta
from app import db
from flask import current_app
import logging
import json # ✅ Necessário para processar o JSON das imagens

logger = logging.getLogger(__name__)

class ProdutoYampi(db.Model):
    """
    Representa um produto da loja Yampi que pode ter desconto desbloqueado com diamantes.
    """
    __tablename__ = 'produto_yampi'
    
    id = db.Column(db.Integer, primary_key=True)
    yampi_id = db.Column(db.String(100), unique=True, nullable=False)
    sku = db.Column(db.String(100), unique=True, nullable=False)
    nome = db.Column(db.String(200), nullable=False)
    
    # ✅ CAMPOS NOVOS (Verificados)
    descricao = db.Column(db.Text)          # HTML da descrição vindo da Yampi
    imagem_url = db.Column(db.String(500))  # Capa principal
    imagens_json = db.Column(db.Text)       # JSON com a galeria completa de imagens
    
    # Preços e Gamificação
    preco_original = db.Column(db.Float, nullable=False)
    percentual_desconto = db.Column(db.Integer, nullable=False, default=50)
    diamantes_necessarios = db.Column(db.Integer, nullable=False, default=1000)
    purchase_url = db.Column(db.String(500)) #Link de compra da Yampi
    # Controle
    ativo = db.Column(db.Boolean, default=True)
    ordem = db.Column(db.Integer, default=0)
    categoria = db.Column(db.String(50), default='Geral')
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    desbloqueios = db.relationship('DescontoDesbloqueado', backref='produto', lazy='dynamic')
    
    @property
    def preco_com_desconto(self):
        """Calcula o preço final com base no desconto configurado"""
        return self.preco_original * (1 - self.percentual_desconto / 100)
    
    @property
    def valor_economia(self):
        """Calcula quanto o usuário está economizando"""
        return self.preco_original - self.preco_com_desconto
    
    def usuario_pode_desbloquear(self, user):
        """Verifica se o usuário tem saldo (múltiplas compras permitidas)"""
        # Verifica saldo de diamantes
        if not hasattr(user, 'diamantes') or user.diamantes < self.diamantes_necessarios:
            return False, f"Saldo insuficiente ({self.diamantes_necessarios} 💎 necessários)"
        
        # --- ALTERAÇÃO: Removida a verificação de desbloqueio existente ---
        # Agora o usuário pode comprar quantas vezes quiser se tiver saldo.
        
        return True, "OK"
    
    def to_dict(self, user=None):
        """
        Converte produto para dicionário JSON completo para uso no Template/Front-end.
        Aqui incluímos a 'descricao' e processamos o 'imagens_json'.
        """
        
        # ✅ Processa o JSON de imagens para lista Python
        lista_imagens = []
        if self.imagens_json:
            try:
                lista_imagens = json.loads(self.imagens_json)
            except Exception as e:
                logger.warning(f"Erro ao decodificar JSON de imagens do produto {self.id}: {e}")
                lista_imagens = []
        
        # Se não tiver lista válida, usa a imagem de capa como item único
        if not lista_imagens and self.imagem_url:
            lista_imagens = [{'url': self.imagem_url, 'thumb': {'url': self.imagem_url}}]

        data = {
            'id': self.id,
            'yampi_id': self.yampi_id,
            'sku': self.sku,
            'nome': self.nome,
            'descricao': self.descricao, # ✅ DESCRIÇÃO HTML INCLUÍDA AQUI
            'imagem_url': self.imagem_url,
            'imagens': lista_imagens,    # ✅ Lista processada para a galeria
            'preco_original': float(self.preco_original),
            'preco_com_desconto': float(self.preco_com_desconto),
            'percentual_desconto': self.percentual_desconto,
            'valor_economia': float(self.valor_economia),
            'diamantes_necessarios': self.diamantes_necessarios,
            'categoria': self.categoria,
            'purchase_url': self.purchase_url,
            'ativo': self.ativo
        }
        
        if user:
            pode, mensagem = self.usuario_pode_desbloquear(user)
            data['pode_desbloquear'] = pode
            data['mensagem_status'] = mensagem
        
        return data


class DescontoDesbloqueado(db.Model):
    """
    Registra os cupons gerados pelos usuários.
    """
    __tablename__ = 'desconto_desbloqueado'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto_yampi.id'), nullable=False)
    
    diamantes_gastos = db.Column(db.Integer, nullable=False)
    percentual_desconto = db.Column(db.Integer, nullable=False)
    
    usado = db.Column(db.Boolean, default=False)
    data_uso = db.Column(db.DateTime, nullable=True)
    
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    expira_em = db.Column(db.DateTime, nullable=False)
    link_checkout = db.Column(db.String(500))
    
    usuario = db.relationship('User', backref='descontos_desbloqueados')
    
    @property
    def esta_valido(self):
        """Verifica se o cupom ainda pode ser usado"""
        return not self.usado and self.expira_em > datetime.utcnow()
    
    @property
    def tempo_restante(self):
        """Retorna o tempo restante em minutos"""
        if not self.esta_valido: return 0
        return int((self.expira_em - datetime.utcnow()).total_seconds() / 60)
    
    @classmethod
    def criar_desbloqueio(cls, user, produto, link_checkout, validade_horas=24):
        """
        Cria um novo registro de desbloqueio e debita os diamantes do usuário.
        """
        try:
            # 1. Valida novamente antes de gastar
            pode, msg = produto.usuario_pode_desbloquear(user)
            if not pode: return None, msg
            
            # 2. Debita diamantes (assumindo que user.gastar_diamantes retorna True/False)
            if not user.gastar_diamantes(produto.diamantes_necessarios, f"Shop: {produto.nome}"):
                return None, "Erro ao debitar diamantes"
            
            # 3. Cria o registro
            desbloqueio = cls(
                user_id=user.id,
                produto_id=produto.id,
                diamantes_gastos=produto.diamantes_necessarios,
                percentual_desconto=produto.percentual_desconto,
                link_checkout=link_checkout,
                expira_em=datetime.utcnow() + timedelta(hours=validade_horas)
            )
            db.session.add(desbloqueio)
            db.session.commit()
            
            return desbloqueio, "Sucesso"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao criar desbloqueio: {e}")
            return None, str(e)

    def to_dict(self):
        """Converte desbloqueio para dicionário"""
        return {
            'id': self.id,
            'produto': self.produto.to_dict() if self.produto else None,
            'link_checkout': self.link_checkout,
            'expira_em': self.expira_em.isoformat(),
            'tempo_restante': self.tempo_restante
        }
