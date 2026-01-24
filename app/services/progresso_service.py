from datetime import datetime, timedelta
from app import db
from flask_login import current_user
from app.models.estatisticas import TempoEstudo, ExercicioRealizado, XpGanho
from app.models.user import User
from app.services.xp_service import XpService

class ProgressoService:
    """
    Serviço para gerenciar o registro e cálculo de progresso dos usuários.
    Fornece métodos para iniciar/finalizar sessões de estudo e registrar XP.
    """
    # Adicione estas melhorias ao progresso_service.py

@staticmethod
def iniciar_sessao_estudo(user_id, atividade):
    """
    Marca o início de uma sessão de estudo.
    Versão melhorada com logs e verificação de erro.
    
    Args:
        user_id (int): ID do usuário
        atividade (str): Tipo de atividade ('simulado', 'exercicio', 'redacao', etc.)
        
    Returns:
        TempoEstudo: Objeto de tempo de estudo criado
    """
    from flask import current_app
    
    try:
        # Verificar se já existe uma sessão ativa
        sessao_ativa = TempoEstudo.query.filter_by(
            user_id=user_id,
            data_fim=None
        ).first()
        
        # Se existir uma sessão ativa, finalize-a automaticamente
        if sessao_ativa:
            current_app.logger.info(f"Finalizando sessão ativa {sessao_ativa.id} para user {user_id}")
            ProgressoService.finalizar_sessao_estudo(sessao_ativa.id, adicionar_xp=False)
        
        # Criar nova sessão
        nova_sessao = TempoEstudo(
            user_id=user_id,
            data_inicio=datetime.utcnow(),
            atividade=atividade,
            minutos=0  # Inicializar com 0
        )
        
        db.session.add(nova_sessao)
        db.session.commit()
        
        current_app.logger.info(f"Nova sessão {nova_sessao.id} iniciada para user {user_id}, atividade: {atividade}")
        
        return nova_sessao
    
    except Exception as e:
        current_app.logger.error(f"Erro ao iniciar sessão de estudo para user {user_id}: {e}")
        db.session.rollback()
        raise

@staticmethod
def finalizar_sessao_estudo(sessao_id, adicionar_xp=True):
    """
    Finaliza uma sessão de estudo, calcula o tempo gasto e adiciona XP.
    Versão melhorada com logs e verificação de erro.
    
    Args:
        sessao_id (int): ID da sessão de tempo de estudo
        adicionar_xp (bool): Se deve adicionar XP ao usuário
        
    Returns:
        dict: Informações sobre a sessão finalizada (minutos, xp_ganho)
    """
    from flask import current_app
    
    try:
        sessao = TempoEstudo.query.get(sessao_id)
        
        if not sessao:
            current_app.logger.warning(f"Sessão {sessao_id} não encontrada")
            return {'erro': 'Sessão não encontrada'}
        
        if sessao.data_fim:
            current_app.logger.warning(f"Sessão {sessao_id} já foi finalizada")
            return {'erro': 'Sessão já finalizada'}
        
        agora = datetime.utcnow()
        sessao.data_fim = agora
        
        # Calcular duração em minutos
        duracao = (agora - sessao.data_inicio).total_seconds() / 60
        duracao_minutos = max(1, int(duracao))  # Mínimo de 1 minuto
        sessao.minutos = duracao_minutos
        
        # Salvar no banco
        db.session.commit()
        
        current_app.logger.info(f"Sessão {sessao_id} finalizada: {duracao_minutos} minutos de {sessao.atividade}")
        
        resultado = {
            'minutos': duracao_minutos,
            'xp_ganho': 0
        }
        
        # Adicionar XP ao usuário (2 XP por minuto de estudo, limitado)
        if adicionar_xp and duracao_minutos > 0:
            # Prevenção de abuso: máximo 240 XP por sessão (2 horas)
            xp_a_adicionar = min(duracao_minutos * 2, 240)
            
            if xp_a_adicionar > 0:
                ProgressoService.registrar_xp_ganho(
                    sessao.user_id, 
                    xp_a_adicionar, 
                    f'Tempo de estudo: {sessao.atividade}'
                )
                resultado['xp_ganho'] = xp_a_adicionar
                current_app.logger.info(f"XP concedido: {xp_a_adicionar} para user {sessao.user_id}")
        
        return resultado
    
    except Exception as e:
        current_app.logger.error(f"Erro ao finalizar sessão {sessao_id}: {e}")
        db.session.rollback()
        return {'erro': f'Erro interno: {str(e)}'}

@staticmethod
def registrar_xp_ganho(user_id, quantidade, origem):
    """
    Registra XP ganho por um usuário.
    Versão melhorada com logs e verificação de erro.
    
    Args:
        user_id (int): ID do usuário
        quantidade (int): Quantidade de XP ganho
        origem (str): Origem do XP ('simulado', 'exercicio', etc.)
    
    Returns:
        XpGanho: Objeto de XP ganho criado
    """
    from flask import current_app
    
    try:
        # Criar registro de XP
        xp_ganho = XpGanho(
            user_id=user_id,
            quantidade=quantidade,
            origem=origem,
            data=datetime.utcnow()
        )
        
        # Adicionar ao usuário
        usuario = User.query.get(user_id)

        if usuario:
           from app.services.xp_service import XpService
           resultado = XpService.conceder_xp(usuario, quantidade, origem, f'XP via ProgressoService: {origem}')
            
           if resultado:
              current_app.logger.info(f"XP adicionado: +{quantidade} para user {user_id} (origem: {origem}). Total: {resultado['xp_total']}")
           else:
              current_app.logger.error(f"Falha ao adicionar XP para user {user_id}")
        else:
            current_app.logger.error(f"Usuário {user_id} não encontrado ao adicionar XP")
            return None




        
        # Salvar no banco
        db.session.add(xp_ganho)
        db.session.commit()
        
        return xp_ganho
    
    except Exception as e:
        current_app.logger.error(f"Erro ao registrar XP para user {user_id}: {e}")
        db.session.rollback()
        return None

@staticmethod
def registrar_tempo_atividade(user_id, atividade, minutos):
    """
    Registra tempo gasto em uma atividade específica diretamente.
    Útil para quando não há cronômetro, mas sabemos o tempo gasto.
    
    Args:
        user_id (int): ID do usuário
        atividade (str): Tipo de atividade
        minutos (int): Tempo gasto em minutos
        
    Returns:
        TempoEstudo: Objeto criado
    """
    from flask import current_app
    
    try:
        tempo_estudo = TempoEstudo(
            user_id=user_id,
            data_inicio=datetime.utcnow() - timedelta(minutes=minutos),
            data_fim=datetime.utcnow(),
            atividade=atividade,
            minutos=minutos
        )
        
        db.session.add(tempo_estudo)
        db.session.commit()
        
        current_app.logger.info(f"Tempo registrado diretamente: {minutos}min de {atividade} para user {user_id}")
        
        # Adicionar XP proporcional
        xp_ganho = min(minutos * 2, 240)  # 2 XP por minuto, máximo 240
        if xp_ganho > 0:
            ProgressoService.registrar_xp_ganho(user_id, xp_ganho, f'Tempo de estudo: {atividade}')
        
        return tempo_estudo
    
    except Exception as e:
        current_app.logger.error(f"Erro ao registrar tempo direto para user {user_id}: {e}")
        db.session.rollback()
        return None

    
    @staticmethod
    def registrar_exercicio_realizado(user_id, exercicio_id, acertou, resposta, tempo_resposta=None):
        """
        Registra um exercício realizado por um usuário.
        
        Args:
            user_id (int): ID do usuário
            exercicio_id (int): ID do exercício
            acertou (bool): Se o usuário acertou o exercício
            resposta (str): Resposta dada pelo usuário
            tempo_resposta (int, optional): Tempo em segundos para responder
            
        Returns:
            ExercicioRealizado: Objeto de exercício realizado criado
        """
        # Criar registro
        exercicio_realizado = ExercicioRealizado(
            user_id=user_id,
            exercicio_id=exercicio_id,
            acertou=acertou,
            resposta_usuario=resposta,
            tempo_resposta=tempo_resposta
        )
        
        # Adicionar XP se acertou (valor baseado na dificuldade)
        from app.models.estatisticas import Exercicio
        
        exercicio = Exercicio.query.get(exercicio_id)
        if exercicio and acertou:
            # XP base: 5 pontos por acerto, multiplicado pela dificuldade (0.5 a 1.5)
            multiplicador = 0.5 + exercicio.dificuldade
            xp_a_adicionar = int(5 * multiplicador)
            
            ProgressoService.registrar_xp_ganho(
                user_id,
                xp_a_adicionar,
                f'Exercício: {exercicio.titulo}'
            )
        
        # Salvar no banco
        db.session.add(exercicio_realizado)
        db.session.commit()
        
        return exercicio_realizado
    
    @staticmethod
    def tem_atividades(user_id):
        """
        Verifica se o usuário já realizou alguma atividade na plataforma.
        
        Args:
            user_id (int): ID do usuário
            
        Returns:
            bool: True se o usuário já realizou atividades, False caso contrário
        """
        # Verificar se tem tempo de estudo registrado
        if TempoEstudo.query.filter_by(user_id=user_id).count() > 0:
            return True
        
        # Verificar se tem exercícios realizados
        if ExercicioRealizado.query.filter_by(user_id=user_id).count() > 0:
            return True
        
        # Verificar se tem XP ganho
        if XpGanho.query.filter_by(user_id=user_id).count() > 0:
            return True
        
        # Verificar se tem simulados realizados
        from app.models.simulado import Simulado
        if Simulado.query.filter_by(user_id=user_id, status='Concluído').count() > 0:
            return True
        
        # Sem atividades
        return False
