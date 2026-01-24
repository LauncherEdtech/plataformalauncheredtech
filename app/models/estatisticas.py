from datetime import datetime, timedelta
from app import db
from flask import current_app

class TempoEstudo(db.Model):
    """
    Modelo para armazenar registros de tempo de estudo.
    Rastreia quanto tempo um usuário passou estudando diferentes atividades.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    data_inicio = db.Column(db.DateTime, default=datetime.utcnow)
    data_fim = db.Column(db.DateTime, nullable=True)
    minutos = db.Column(db.Integer, default=0)  # Duração em minutos
    atividade = db.Column(db.String(50))  # Tipo de atividade: 'simulado', 'exercicio', 'redacao', etc.


    # Relação com o usuário
    usuario = db.relationship('User', backref=db.backref('tempos_estudo', lazy='dynamic'))
    
    def __repr__(self):
        return f'<TempoEstudo {self.id}: {self.user_id} - {self.minutos}min>'
    
    @staticmethod
    def calcular_tempo_hoje(user_id):
        """Calcula o tempo total de estudo do usuário no dia atual."""
        hoje = datetime.utcnow().date()
        registros = TempoEstudo.query.filter(
            TempoEstudo.user_id == user_id,
            db.func.date(TempoEstudo.data_inicio) == hoje
        ).all()
        
        return sum(r.minutos for r in registros)
    
    @staticmethod
    def calcular_tempo_semana(user_id):
        """Calcula o tempo total de estudo do usuário na semana atual."""
        hoje = datetime.utcnow().date()
        # Cálculo da data da segunda-feira dessa semana usando a função extract para PostgreSQL
        # O DOW em PostgreSQL vai de 0 (domingo) a 6 (sábado)
        # Subtraindo o DOW atual de hoje e somando 1 se não for domingo (DOW != 0)
        dias_a_subtrair = hoje.weekday()  # 0 para segunda, 6 para domingo no Python
        inicio_semana = hoje - timedelta(days=dias_a_subtrair)
        
        registros = TempoEstudo.query.filter(
            TempoEstudo.user_id == user_id,
            db.func.date(TempoEstudo.data_inicio) >= inicio_semana
        ).all()
        
        return sum(r.minutos for r in registros)
    
    @staticmethod
    def calcular_tempo_mes(user_id):
        """Calcula o tempo total de estudo do usuário no mês atual."""
        hoje = datetime.utcnow().date()
        inicio_mes = hoje.replace(day=1)  # Primeiro dia do mês
        
        registros = TempoEstudo.query.filter(
            TempoEstudo.user_id == user_id,
            db.func.date(TempoEstudo.data_inicio) >= inicio_mes
        ).all()
        
        return sum(r.minutos for r in registros)

class Exercicio(db.Model):
    """
    Modelo para catalogar exercícios.
    Armazena informações sobre exercícios disponíveis na plataforma.
    """
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    area = db.Column(db.String(50))  # 'Linguagens', 'Matemática', 'Humanas', 'Natureza'
    dificuldade = db.Column(db.Float, default=0.5)  # Valor entre 0 e 1
    enunciado = db.Column(db.Text)
    resposta_correta = db.Column(db.String(200))
    
    # Relacionamentos
    realizacoes = db.relationship('ExercicioRealizado', backref='exercicio', lazy='dynamic')
    
    def __repr__(self):
        return f'<Exercicio {self.id}: {self.titulo}>'

class ExercicioRealizado(db.Model):
    """
    Modelo para rastrear exercícios realizados pelos usuários.
    Armazena o histórico de exercícios feitos e os resultados.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exercicio_id = db.Column(db.Integer, db.ForeignKey('exercicio.id'), nullable=False)
    data_realizacao = db.Column(db.DateTime, default=datetime.utcnow)
    acertou = db.Column(db.Boolean, default=False)
    resposta_usuario = db.Column(db.String(200))
    tempo_resposta = db.Column(db.Integer)  # Tempo em segundos para responder
    
    # Relação com o usuário
    usuario = db.relationship('User', backref=db.backref('exercicios_realizados', lazy='dynamic'))
    
    def __repr__(self):
        return f'<ExercicioRealizado {self.id}: {self.user_id} - {self.exercicio_id}>'
    
    @staticmethod
    def calcular_progresso_por_area(user_id):
        """
        Calcula o progresso do usuário por área de conhecimento.
        Retorna um dicionário com as áreas e os percentuais de acerto.
        """
        # Obtém todos os exercícios realizados pelo usuário
        exercicios = ExercicioRealizado.query.filter_by(user_id=user_id).all()
        
        # Agrupa por área
        areas = {}
        for ex in exercicios:
            area = ex.exercicio.area
            if area not in areas:
                areas[area] = {'total': 0, 'acertos': 0}
            
            areas[area]['total'] += 1
            if ex.acertou:
                areas[area]['acertos'] += 1
        
        # Calcula os percentuais
        for area in areas:
            if areas[area]['total'] > 0:
                areas[area]['percentual'] = (areas[area]['acertos'] / areas[area]['total']) * 100
            else:
                areas[area]['percentual'] = 0
        
        return areas

class XpGanho(db.Model):
    """
    Modelo para registrar os pontos XP ganhos pelos usuários.
    Rastreia quando, quanto e como o usuário ganhou pontos XP.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    origem = db.Column(db.String(100))  # 'simulado', 'exercicio', 'redacao', 'helpzone', etc.
    
    # Relação com o usuário
    usuario = db.relationship('User', backref=db.backref('historico_xp', lazy='dynamic'))
    
    def __repr__(self):
        return f'<XpGanho {self.id}: {self.user_id} - {self.quantidade}XP>'
    
    @staticmethod
    def calcular_xp_periodo(user_id, dias=7):
        """
        Calcula o XP ganho pelo usuário nos últimos X dias.
        Retorna um dicionário com as datas e valores de XP.
        """
        from datetime import timedelta
        
        hoje = datetime.utcnow().date()
        data_inicial = hoje - timedelta(days=dias)
        
        # Criar um dicionário com todas as datas do período
        datas = {}
        for i in range(dias):
            data = (data_inicial + timedelta(days=i+1)).strftime('%d/%m')
            datas[data] = 0
        
        # Obter os registros de XP do período
        registros = XpGanho.query.filter(
            XpGanho.user_id == user_id,
            db.func.date(XpGanho.data) > data_inicial
        ).all()
        
        # Agrupar por data
        for reg in registros:
            data = reg.data.strftime('%d/%m')
            if data in datas:
                datas[data] += reg.quantidade
        
        # Formatar para retorno
        resultado = {
            'datas': list(datas.keys()),
            'valores': list(datas.values())
        }
        
        return resultado
