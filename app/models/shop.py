# app/models/shop.py - MODELO PRODUTO ATUALIZADO PARA DIAMANTES

from datetime import datetime
from app import db
from flask import current_app

class Produto(db.Model):
    """
    Modelo para produtos disponíveis na loja.
    *** VERSÃO ATUALIZADA COM DIAMANTES ***
    """
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    imagem = db.Column(db.String(255), default='default.jpg')
    
    # NOVO: Preço em diamantes (moeda consumível)
    preco_diamantes = db.Column(db.Integer, nullable=False, default=50)
    
    # LEGADO: Manter preco_xp para compatibilidade (será removido gradualmente)
    preco_xp = db.Column(db.Integer, nullable=True)
    
    estoque = db.Column(db.Integer, default=100)
    disponivel = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    categoria = db.Column(db.String(50), default='Outros')
    
    # Relacionamentos
    resgates = db.relationship('Resgate', backref='produto', lazy='dynamic')
    
    def __repr__(self):
        return f'<Produto {self.id}: {self.nome}>'
    
    @property
    def preco_display(self):
        """Retorna o preço a ser exibido (diamantes ou XP convertido)"""
        if self.preco_diamantes:
            return self.preco_diamantes
        elif self.preco_xp:
            # Converter XP para diamantes na exibição
            return self.preco_xp // 2
        else:
            return 50  # Valor padrão
    
    @property
    def preco_final(self):
        """Retorna o preço final em diamantes para processamento"""
        return self.preco_display
    
    @property
    def status_estoque(self):
        """Retorna o status do estoque (Disponível, Poucas unidades, Esgotado)"""
        if not self.disponivel or self.estoque <= 0:
            return "Esgotado"
        elif self.estoque <= 10:
            return "Poucas unidades"
        else:
            return "Disponível"
    
    @property
    def status_estoque_class(self):
        """Retorna classe CSS baseada no status do estoque"""
        status = self.status_estoque
        if status == "Esgotado":
            return "danger"
        elif status == "Poucas unidades":
            return "warning"
        else:
            return "success"
    
    def pode_ser_resgatado_por(self, user):
        """Verifica se um usuário pode resgatar este produto"""
        if not self.disponivel or self.estoque <= 0:
            return False, "Produto indisponível"
        
        if not user.pode_gastar_diamantes(self.preco_final):
            return False, f"Diamantes insuficientes. Necessário: {self.preco_final} 💎"
        
        # Verificar se já tem resgate ativo
        resgate_ativo = Resgate.query.filter_by(
            user_id=user.id,
            produto_id=self.id,
            status='Pendente'
        ).first()
        
        if resgate_ativo:
            return False, "Você já possui um resgate ativo deste produto"
        
        return True, "OK"
    
    def to_dict(self):
        """Converte produto para dicionário (útil para APIs)"""
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'preco_diamantes': self.preco_final,
            'estoque': self.estoque,
            'disponivel': self.disponivel,
            'categoria': self.categoria,
            'status_estoque': self.status_estoque,
            'imagem_url': f'/static/images/produtos/{self.imagem}'
        }

class Resgate(db.Model):
    """
    Modelo para resgates de produtos pelos usuários.
    Registra quando um usuário troca seus diamantes por um produto.
    """
    id = db.Column(db.Integer, primary_key=True)
    data_resgate = db.Column(db.DateTime, default=datetime.utcnow)
    data_envio = db.Column(db.DateTime, nullable=True)     # Data real de envio
    data_entrega = db.Column(db.DateTime, nullable=True)   # Data real de entrega
    status = db.Column(db.String(20), default='Pendente')  # Pendente, Enviado, Entregue, Cancelado
    endereco_entrega = db.Column(db.Text)

    # Campos adicionais para informações de contato
    nome_contato = db.Column(db.String(255))
    email_contato = db.Column(db.String(255))
    telefone_contato = db.Column(db.String(20))
    
    # NOVO: Campo para armazenar quantos diamantes foram gastos
    diamantes_gastos = db.Column(db.Integer, nullable=True)
    
    # Chaves estrangeiras
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relacionamentos
    usuario = db.relationship('User', backref='resgates', foreign_keys=[user_id])
    
    def __repr__(self):
        return f'<Resgate {self.id} - Produto {self.produto_id} por Usuário {self.user_id}>'
    
    @property
    def status_class(self):
        """Retorna classe CSS baseada no status"""
        status_classes = {
            'Pendente': 'warning',
            'Enviado': 'info', 
            'Entregue': 'success',
            'Cancelado': 'danger'
        }
        return status_classes.get(self.status, 'secondary')
    
    @property
    def status_icon(self):
        """Retorna ícone baseado no status"""
        status_icons = {
            'Pendente': 'clock',
            'Enviado': 'truck',
            'Entregue': 'check-circle',
            'Cancelado': 'x-circle'
        }
        return status_icons.get(self.status, 'circle')
    
    def calcular_diamantes_gastos(self):
        """Calcula quantos diamantes foram gastos (baseado no preço do produto)"""
        if self.diamantes_gastos:
            return self.diamantes_gastos
        elif self.produto:
            return self.produto.preco_final
        else:
            return 0
    
    def pode_ser_cancelado(self):
        """Verifica se o resgate pode ser cancelado"""
        return self.status == 'Pendente'
    
    def to_dict(self):
        """Converte resgate para dicionário"""
        return {
            'id': self.id,
            'produto': self.produto.to_dict() if self.produto else None,
            'status': self.status,
            'status_class': self.status_class,
            'data_resgate': self.data_resgate.isoformat() if self.data_resgate else None,
            'data_envio': self.data_envio.isoformat() if self.data_envio else None,
            'data_entrega': self.data_entrega.isoformat() if self.data_entrega else None,
            'diamantes_gastos': self.calcular_diamantes_gastos(),
            'pode_cancelar': self.pode_ser_cancelado()
        }
