# app/models/yampi_shop.py - Sistema de desconto Yampi com diamantes
# ✅ ATUALIZADO: Agora usa price_sale (preço "de") e price_discount (preço "por")

from datetime import datetime, timedelta
from app import db
from flask import current_app
import logging
import json

logger = logging.getLogger(__name__)

class ProdutoYampi(db.Model):
    """
    Representa um produto da loja Yampi que pode ter desconto desbloqueado com diamantes.
    
    ESTRUTURA DE PREÇOS YAMPI:
    - price_sale: Preço "DE" (valor original, será mostrado riscado)
    - price_discount: Preço "POR" (valor promocional que o cliente paga)
    - Porcentagem: Calculada automaticamente entre esses valores
    """
    __tablename__ = 'produto_yampi'
    
    id = db.Column(db.Integer, primary_key=True)
    yampi_id = db.Column(db.String(100), unique=True, nullable=False)
    sku = db.Column(db.String(100), unique=True, nullable=False)
    nome = db.Column(db.String(200), nullable=False)
    
    # Conteúdo
    descricao = db.Column(db.Text)          # HTML da descrição vindo da Yampi
    imagem_url = db.Column(db.String(500))  # Capa principal
    imagens_json = db.Column(db.Text)       # JSON com a galeria completa de imagens
    
    # ===== PREÇOS DA YAMPI (ESTRUTURA REAL) =====
    preco_venda = db.Column(db.Float, nullable=False, default=0)      # price_sale (preço "DE")
    preco_desconto = db.Column(db.Float, nullable=False, default=0)   # price_discount (preço "POR")
    
    # ===== CAMPOS LEGADOS (mantidos para compatibilidade) =====
    preco_original = db.Column(db.Float, nullable=False)
    percentual_desconto = db.Column(db.Integer, nullable=False, default=50)
    
    # Gamificação
    diamantes_necessarios = db.Column(db.Integer, nullable=False, default=1000)
    purchase_url = db.Column(db.String(500))  # Link direto de compra da Yampi
    
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
    def percentual_desconto_yampi(self):
        """
        Calcula o percentual de desconto REAL da Yampi
        Baseado em: ((price_sale - price_discount) / price_sale) * 100
        
        Exemplo: 
        - price_sale = 20.28
        - price_discount = 8.11
        - desconto = ((20.28 - 8.11) / 20.28) * 100 = 60%
        """
        if self.preco_venda > 0 and self.preco_desconto > 0:
            desconto = ((self.preco_venda - self.preco_desconto) / self.preco_venda) * 100
            return int(round(desconto))
        return 0
    
    @property
    def valor_economia_yampi(self):
        """Calcula quanto o usuário economiza comprando com o desconto da Yampi"""
        if self.preco_venda > 0 and self.preco_desconto > 0:
            return self.preco_venda - self.preco_desconto
        return 0
    
    @property
    def preco_com_desconto(self):
        """
        COMPATIBILIDADE: Mantém para não quebrar código antigo
        Retorna o preco_desconto da Yampi
        """
        if self.preco_desconto > 0:
            return self.preco_desconto
        # Fallback para cálculo antigo
        return self.preco_original * (1 - self.percentual_desconto / 100)
    
    @property
    def valor_economia(self):
        """COMPATIBILIDADE: Mantém para não quebrar código antigo"""
        if self.preco_venda > 0 and self.preco_desconto > 0:
            return self.valor_economia_yampi
        return self.preco_original - self.preco_com_desconto
    
    def usuario_pode_desbloquear(self, user):
        """Verifica se o usuário tem saldo (múltiplas compras permitidas)"""
        if not hasattr(user, 'diamantes') or user.diamantes < self.diamantes_necessarios:
            return False, f"Saldo insuficiente ({self.diamantes_necessarios} 💎 necessários)"
        
        return True, "OK"
    
    def to_dict(self, user=None):
        """
        Converte produto para dicionário JSON completo.
        ✅ AGORA INCLUI: preco_venda, preco_desconto, percentual_desconto_yampi
        """
        
        # Processa o JSON de imagens para lista Python
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
            'descricao': self.descricao,
            'imagem_url': self.imagem_url,
            'imagens': lista_imagens,
            
            # ===== PREÇOS DA YAMPI (NOVOS) =====
            'preco_venda': float(self.preco_venda) if self.preco_venda else 0,           # Preço "DE" (riscado)
            'preco_desconto': float(self.preco_desconto) if self.preco_desconto else 0,  # Preço "POR" (destaque)
            'percentual_desconto_yampi': self.percentual_desconto_yampi,                  # % real
            'valor_economia_yampi': float(self.valor_economia_yampi),                     # Economia
            
            # ===== CAMPOS LEGADOS (compatibilidade) =====
            'preco_original': float(self.preco_original),
            'preco_com_desconto': float(self.preco_com_desconto),
            'percentual_desconto': self.percentual_desconto,
            'valor_economia': float(self.valor_economia),
            
            # Outros
            'diamantes_necessarios': self.diamantes_necessarios,
            'categoria': self.categoria,
            'purchase_url': self.purchase_url,
            'ativo': self.ativo
        }
        
        # Adiciona informações do usuário se fornecido
        if user:
            desbloqueio_ativo = DescontoDesbloqueado.query.filter_by(
                user_id=user.id,
                produto_id=self.id,
                usado=False
            ).filter(
                DescontoDesbloqueado.expira_em > datetime.utcnow()
            ).first()
            
            data['desbloqueio_ativo'] = desbloqueio_ativo.to_dict() if desbloqueio_ativo else None
            data['usuario_pode_desbloquear'] = self.usuario_pode_desbloquear(user)[0]
        
        return data


class DescontoDesbloqueado(db.Model):
    """
    Registro de um desconto desbloqueado por um usuário usando diamantes
    """
    __tablename__ = 'desconto_desbloqueado'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto_yampi.id'), nullable=False)
    
    # Informações do desconto
    link_checkout = db.Column(db.String(1000), nullable=False)
    diamantes_gastos = db.Column(db.Integer, nullable=False)
    percentual_desconto = db.Column(db.Integer, nullable=False)  # ✅ Campo obrigatório no banco
    
    # Controle
    usado = db.Column(db.Boolean, default=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    expira_em = db.Column(db.DateTime, nullable=False)
    data_uso = db.Column(db.DateTime, nullable=True)  # ✅ Compatível com banco existente
    
    @property
    def esta_valido(self):
        """Verifica se o desconto ainda está dentro do prazo"""
        return not self.usado and datetime.utcnow() < self.expira_em
    
    @staticmethod
    def criar_desbloqueio(user, produto, link_checkout, validade_horas=24):
        """
        Cria um novo desbloqueio de desconto
        
        Args:
            user: Objeto User
            produto: Objeto ProdutoYampi
            link_checkout: URL do checkout da Yampi
            validade_horas: Horas de validade do link
        
        Returns:
            tuple: (DescontoDesbloqueado ou None, mensagem)
        """
        try:
            # Debita os diamantes
            if user.diamantes < produto.diamantes_necessarios:
                return None, "Saldo insuficiente"
            
            user.diamantes -= produto.diamantes_necessarios
            
            # Cria o desbloqueio
            desbloqueio = DescontoDesbloqueado(
                user_id=user.id,
                produto_id=produto.id,
                link_checkout=link_checkout,
                diamantes_gastos=produto.diamantes_necessarios,
                percentual_desconto=produto.percentual_desconto,  # ✅ Campo obrigatório
                expira_em=datetime.utcnow() + timedelta(hours=validade_horas)
            )
            
            db.session.add(desbloqueio)
            db.session.commit()
            
            logger.info(f"✅ Desconto desbloqueado: User {user.id} | Produto {produto.nome} | {produto.diamantes_necessarios}💎")
            
            return desbloqueio, "Desconto desbloqueado com sucesso!"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Erro ao criar desbloqueio: {e}")
            return None, f"Erro ao processar: {str(e)}"
    
    def marcar_como_usado(self):
        """Marca o desconto como utilizado"""
        try:
            self.usado = True
            self.data_uso = datetime.utcnow()  # ✅ Usar data_uso
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao marcar desconto como usado: {e}")
            return False
    
    def to_dict(self):
        """Converte para dicionário"""
        return {
            'id': self.id,
            'produto': self.produto.to_dict() if self.produto else None,
            'link_checkout': self.link_checkout,
            'diamantes_gastos': self.diamantes_gastos,
            'usado': self.usado,
            'esta_valido': self.esta_valido,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'expira_em': self.expira_em.isoformat() if self.expira_em else None,
            'data_uso': self.data_uso.isoformat() if self.data_uso else None  # ✅ Usar data_uso
        }
