# app/models/notificacao.py
from datetime import datetime
from app import db

class Notificacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(50), default='info')  # 'info', 'success', 'warning', 'error', 'conquista'
    icone = db.Column(db.String(10), default='🔔')
    lida = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_leitura = db.Column(db.DateTime)
    
    # Dados adicionais em JSON (opcional)
    dados_extras = db.Column(db.Text)  # JSON string
    
    def to_dict(self):
        return {
            'id': self.id,
            'titulo': self.titulo,
            'mensagem': self.mensagem,
            'tipo': self.tipo,
            'icone': self.icone,
            'lida': self.lida,
            'data_criacao': self.data_criacao.isoformat(),
            'data_leitura': self.data_leitura.isoformat() if self.data_leitura else None
        }

class Conquista(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)  # 'primeira_aula', 'sequencia_7', etc.
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    icone = db.Column(db.String(10), default='🏆')
    moedas_bonus = db.Column(db.Integer, default=0)
    ativa = db.Column(db.Boolean, default=True)
    
    # Relacionamento com usuários que conquistaram
    usuarios_conquistaram = db.relationship('UserConquista', backref='conquista', lazy='dynamic')

class UserConquista(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    conquista_id = db.Column(db.Integer, db.ForeignKey('conquista.id'), nullable=False)
    data_conquista = db.Column(db.DateTime, default=datetime.utcnow)
    notificada = db.Column(db.Boolean, default=False)
    
    # Índice único para evitar duplicatas
    __table_args__ = (db.UniqueConstraint('user_id', 'conquista_id'),)

# Funções auxiliares para o sistema de notificações

def criar_notificacao(user_id, titulo, mensagem, tipo='info', icone=None):
    """Cria uma nova notificação para o usuário"""
    notificacao = Notificacao(
        user_id=user_id,
        titulo=titulo,
        mensagem=mensagem,
        tipo=tipo,
        icone=icone or ('🔔' if tipo == 'info' else 
                       '✅' if tipo == 'success' else 
                       '⚠️' if tipo == 'warning' else 
                       '❌' if tipo == 'error' else 
                       '🏆' if tipo == 'conquista' else '🔔')
    )
    
    db.session.add(notificacao)
    db.session.commit()
    return notificacao

def verificar_conquistas_usuario(user_id):
    """Verifica e desbloqueia conquistas para o usuário"""
    from app.models.estudo import ProgressoAula, SessaoEstudo
    from app.models.user import User
    from sqlalchemy import func
    
    user = User.query.get(user_id)
    if not user:
        return []
    
    conquistas_desbloqueadas = []
    
    # Conquista: Primeira aula concluída
    if not UserConquista.query.filter_by(user_id=user_id, conquista_id=1).first():
        primeira_aula = ProgressoAula.query.filter_by(user_id=user_id, concluida=True).first()
        if primeira_aula:
            desbloquear_conquista(user_id, 'primeira_aula')
            conquistas_desbloqueadas.append('primeira_aula')
    
    # Conquista: 10 aulas concluídas
    if not UserConquista.query.filter_by(user_id=user_id, conquista_id=2).first():
        aulas_concluidas = ProgressoAula.query.filter_by(user_id=user_id, concluida=True).count()
        if aulas_concluidas >= 10:
            desbloquear_conquista(user_id, 'dez_aulas')
            conquistas_desbloqueadas.append('dez_aulas')
    
    # Conquista: 7 dias consecutivos
    if not UserConquista.query.filter_by(user_id=user_id, conquista_id=3).first():
        sequencia = calcular_sequencia_estudo(user_id)
        if sequencia >= 7:
            desbloquear_conquista(user_id, 'sequencia_7')
            conquistas_desbloqueadas.append('sequencia_7')
    
    # Conquista: 100 moedas
    if not UserConquista.query.filter_by(user_id=user_id, conquista_id=4).first():
        if user.total_moedas >= 100:
            desbloquear_conquista(user_id, 'moedas_100')
            conquistas_desbloqueadas.append('moedas_100')
    
    # Conquista: 10 horas de estudo
    if not UserConquista.query.filter_by(user_id=user_id, conquista_id=5).first():
        tempo_total = db.session.query(func.sum(SessaoEstudo.tempo_ativo)).filter_by(
            user_id=user_id, ativa=False
        ).scalar() or 0
        
        if tempo_total >= 36000:  # 10 horas em segundos
            desbloquear_conquista(user_id, 'dez_horas')
            conquistas_desbloqueadas.append('dez_horas')
    
    return conquistas_desbloqueadas

def desbloquear_conquista(user_id, codigo_conquista):
    """Desbloqueia uma conquista específica para o usuário"""
    conquista = Conquista.query.filter_by(codigo=codigo_conquista).first()
    if not conquista:
        return False
    
    # Verificar se já foi conquistada
    ja_conquistada = UserConquista.query.filter_by(
        user_id=user_id,
        conquista_id=conquista.id
    ).first()
    
    if ja_conquistada:
        return False
    
    # Criar registro da conquista
    user_conquista = UserConquista(
        user_id=user_id,
        conquista_id=conquista.id
    )
    db.session.add(user_conquista)
    
    # Adicionar moedas de bônus se houver
    if conquista.moedas_bonus > 0:
        from app.models.user import User
        user = User.query.get(user_id)
        user.adicionar_moedas(
            conquista.moedas_bonus,
            'conquista',
            f'Conquista desbloqueada: {conquista.titulo}'
        )
    
    # Criar notificação
    criar_notificacao(
        user_id,
        f'🏆 Conquista Desbloqueada!',
        f'{conquista.icone} {conquista.titulo}\n{conquista.descricao}' + 
        (f'\n\n💰 Bônus: +{conquista.moedas_bonus} moedas!' if conquista.moedas_bonus > 0 else ''),
        'conquista',
        conquista.icone
    )
    
    db.session.commit()
    return True

def calcular_sequencia_estudo(user_id):
    """Calcula sequência de dias estudando"""
    from app.models.estudo import SessaoEstudo
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    hoje = datetime.now().date()
    sequencia = 0
    data_verificacao = hoje
    
    while sequencia < 365:
        sessoes_do_dia = SessaoEstudo.query.filter(
            SessaoEstudo.user_id == user_id,
            func.date(SessaoEstudo.inicio) == data_verificacao,
            SessaoEstudo.tempo_ativo >= 300  # 5 minutos
        ).first()
        
        if sessoes_do_dia:
            sequencia += 1
            data_verificacao -= timedelta(days=1)
        else:
            break
    
    return sequencia

def inicializar_conquistas():
    """Inicializa as conquistas padrão do sistema"""
    conquistas_padrao = [
        {
            'codigo': 'primeira_aula',
            'titulo': 'Primeiros Passos',
            'descricao': 'Concluiu sua primeira aula!',
            'icone': '🎓',
            'moedas_bonus': 20
        },
        {
            'codigo': 'dez_aulas',
            'titulo': 'Estudante Dedicado',
            'descricao': 'Concluiu 10 aulas!',
            'icone': '📚',
            'moedas_bonus': 50
        },
        {
            'codigo': 'sequencia_7',
            'titulo': 'Constância é Tudo',
            'descricao': 'Estudou por 7 dias consecutivos!',
            'icone': '🔥',
            'moedas_bonus': 100
        },
        {
            'codigo': 'moedas_100',
            'titulo': 'Primeiro Tesouro',
            'descricao': 'Acumulou 100 moedas!',
            'icone': '💰',
            'moedas_bonus': 25
        },
        {
            'codigo': 'dez_horas',
            'titulo': 'Maratonista dos Estudos',
            'descricao': 'Completou 10 horas de estudo!',
            'icone': '⏰',
            'moedas_bonus': 150
        },
        {
            'codigo': 'primeira_materia',
            'titulo': 'Especialista em Formação',
            'descricao': 'Concluiu todas as aulas de uma matéria!',
            'icone': '🎯',
            'moedas_bonus': 200
        },
        {
            'codigo': 'speed_runner',
            'titulo': 'Speed Runner',
            'descricao': 'Concluiu 5 aulas em um dia!',
            'icone': '⚡',
            'moedas_bonus': 75
        },
        {
            'codigo': 'night_owl',
            'titulo': 'Coruja Noturna',
            'descricao': 'Estudou após as 22h!',
            'icone': '🦉',
            'moedas_bonus': 30
        }
    ]
    
    for conquista_data in conquistas_padrao:
        conquista_existente = Conquista.query.filter_by(codigo=conquista_data['codigo']).first()
        if not conquista_existente:
            conquista = Conquista(**conquista_data)
            db.session.add(conquista)
    
    db.session.commit()

# Rotas para o sistema de notificações

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

notificacoes_bp = Blueprint('notificacoes', __name__, url_prefix='/api/notificacoes')

@notificacoes_bp.route('/')
@login_required
def listar_notificacoes():
    """Lista notificações do usuário"""
    limite = request.args.get('limite', 10, type=int)
    apenas_nao_lidas = request.args.get('nao_lidas', False, type=bool)
    
    query = Notificacao.query.filter_by(user_id=current_user.id)
    
    if apenas_nao_lidas:
        query = query.filter_by(lida=False)
    
    notificacoes = query.order_by(Notificacao.data_criacao.desc()).limit(limite).all()
    
    return jsonify({
        'notificacoes': [n.to_dict() for n in notificacoes],
        'total_nao_lidas': Notificacao.query.filter_by(user_id=current_user.id, lida=False).count()
    })

@notificacoes_bp.route('/<int:notificacao_id>/marcar_lida', methods=['POST'])
@login_required
def marcar_como_lida(notificacao_id):
    """Marca notificação como lida"""
    notificacao = Notificacao.query.filter_by(
        id=notificacao_id,
        user_id=current_user.id
    ).first()
    
    if not notificacao:
        return jsonify({'error': 'Notificação não encontrada'}), 404
    
    notificacao.lida = True
    notificacao.data_leitura = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True})

@notificacoes_bp.route('/marcar_todas_lidas', methods=['POST'])
@login_required
def marcar_todas_lidas():
    """Marca todas as notificações como lidas"""
    Notificacao.query.filter_by(
        user_id=current_user.id,
        lida=False
    ).update({
        'lida': True,
        'data_leitura': datetime.utcnow()
    })
    
    db.session.commit()
    
    return jsonify({'success': True})

@notificacoes_bp.route('/conquistas')
@login_required
def listar_conquistas():
    """Lista conquistas do usuário"""
    # Conquistas desbloqueadas
    conquistas_usuario = db.session.query(Conquista, UserConquista).join(
        UserConquista
    ).filter(UserConquista.user_id == current_user.id).all()
    
    # Todas as conquistas disponíveis
    todas_conquistas = Conquista.query.filter_by(ativa=True).all()
    
    conquistas_desbloqueadas = []
    conquistas_bloqueadas = []
    
    ids_desbloqueadas = [uc.conquista_id for _, uc in conquistas_usuario]
    
    for conquista in todas_conquistas:
        if conquista.id in ids_desbloqueadas:
            user_conquista = next(uc for c, uc in conquistas_usuario if c.id == conquista.id)
            conquistas_desbloqueadas.append({
                'id': conquista.id,
                'codigo': conquista.codigo,
                'titulo': conquista.titulo,
                'descricao': conquista.descricao,
                'icone': conquista.icone,
                'moedas_bonus': conquista.moedas_bonus,
                'data_conquista': user_conquista.data_conquista.isoformat(),
                'desbloqueada': True
            })
        else:
            conquistas_bloqueadas.append({
                'id': conquista.id,
                'codigo': conquista.codigo,
                'titulo': conquista.titulo,
                'descricao': conquista.descricao,
                'icone': '🔒',  # Ícone de bloqueado
                'moedas_bonus': conquista.moedas_bonus,
                'desbloqueada': False
            })
    
    return jsonify({
        'desbloqueadas': conquistas_desbloqueadas,
        'bloqueadas': conquistas_bloqueadas,
        'total_desbloqueadas': len(conquistas_desbloqueadas),
        'total_disponiveis': len(todas_conquistas)
    })