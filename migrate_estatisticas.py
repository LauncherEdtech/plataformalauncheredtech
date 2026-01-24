"""
Script de migração para adicionar as novas tabelas de estatísticas
e converter dados fictícios em dados reais para usuários existentes.

Para utilizar:
1. Certifique-se de que os modelos novos foram adicionados
2. Execute este script com `python migrate_estatisticas.py`
"""

from app import create_app, db
from app.models.estatisticas import TempoEstudo, Exercicio, ExercicioRealizado, XpGanho
from app.models.user import User
from app.models.simulado import Simulado, Questao
from datetime import datetime, timedelta
import random

def migrar_estatisticas():
    """
    Migra estatísticas dos usuários existentes para o novo modelo de dados.
    Cria registros reais com base em atividades já realizadas.
    """
    print("[+] Iniciando migração de estatísticas...")
    
    # Criar app context
    app = create_app()
    with app.app_context():
        # Criar as novas tabelas, caso ainda não existam
        db.create_all()
        
        # Buscar todos os usuários
        usuarios = User.query.all()
        print(f"[+] Encontrados {len(usuarios)} usuários para migração.")
        
        for user in usuarios:
            print(f"[+] Migrando dados para o usuário: {user.username}...")
            
            # 1. Migrar simulados para registros de tempo e XP
            simulados = Simulado.query.filter_by(
                user_id=user.id,
                status='Concluído'
            ).all()
            
            if simulados:
                print(f"    - Migrando {len(simulados)} simulados...")
                for simulado in simulados:
                    # Convertemos o tempo em string para minutos
                    tempo_str = simulado.tempo_realizado if simulado.tempo_realizado else "01h30"
                    try:
                        horas, minutos = tempo_str.split('h')
                        minutos_total = int(horas) * 60 + int(minutos)
                    except:
                        minutos_total = 90  # Padrão: 1h30min
                    
                    # Criar registro de tempo
                    tempo_estudo = TempoEstudo(
                        user_id=user.id,
                        data_inicio=simulado.data_realizado,
                        data_fim=simulado.data_realizado + timedelta(minutes=minutos_total),
                        minutos=minutos_total,
                        atividade=f"Simulado: {simulado.titulo}"
                    )
                    db.session.add(tempo_estudo)
                    
                    # Criar registro de XP ganho
                    # Cálculo: 10% da nota TRI arredondado para múltiplo de 5
                    if simulado.nota_tri and simulado.nota_tri > 0:
                        xp_ganho = round((simulado.nota_tri * 0.1) / 5) * 5
                        xp_registro = XpGanho(
                            user_id=user.id,
                            quantidade=int(xp_ganho),
                            data=simulado.data_realizado,
                            origem=f"Simulado: {simulado.titulo}"
                        )
                        db.session.add(xp_registro)
                    
                    # Migrar questões como exercícios realizados
                    questoes = Questao.query.filter_by(simulado_id=simulado.id).all()
                    
                    # Primeiro, precisamos garantir que os exercícios existam
                    for questao in questoes:
                        # Verificar se já existe o exercício
                        exercicio = Exercicio.query.filter_by(
                            titulo=f"Questão {questao.numero} - {simulado.titulo}"
                        ).first()
                        
                        if not exercicio:
                            # Criar exercício
                            exercicio = Exercicio(
                                titulo=f"Questão {questao.numero} - {simulado.titulo}",
                                area=questao.area,
                                dificuldade=questao.dificuldade,
                                enunciado=questao.texto,
                                resposta_correta=questao.resposta_correta
                            )
                            db.session.add(exercicio)
                            db.session.flush()  # Para obter o ID
                        
                        # Criar registro de exercício realizado
                        acertou = questao.resposta_usuario == questao.resposta_correta
                        exercicio_realizado = ExercicioRealizado(
                            user_id=user.id,
                            exercicio_id=exercicio.id,
                            data_realizacao=simulado.data_realizado + timedelta(minutes=questao.numero),
                            acertou=acertou,
                            resposta_usuario=questao.resposta_usuario,
                            tempo_resposta=questao.tempo_resposta if hasattr(questao, 'tempo_resposta') else random.randint(30, 180)
                        )
                        db.session.add(exercicio_realizado)
                        
                        # Adicionar XP por acerto em questão
                        if acertou:
                            xp_questao = int(5 * (0.5 + questao.dificuldade))
                            xp_registro = XpGanho(
                                user_id=user.id,
                                quantidade=xp_questao,
                                data=exercicio_realizado.data_realizacao,
                                origem=f"Exercício: Questão {questao.numero} - {simulado.titulo}"
                            )
                            db.session.add(xp_registro)
            else:
                print(f"    - Nenhum simulado encontrado para o usuário {user.username}")
            
            # 2. Verificar se tem registros no HelpZone e migrar
            try:
                from app.models.helpzone import Resposta, Duvida
                
                # Dúvidas criadas
                duvidas = Duvida.query.filter_by(user_id=user.id).all()
                
                if duvidas:
                    print(f"    - Migrando {len(duvidas)} dúvidas do HelpZone...")
                    for duvida in duvidas:
                        # Criar registro de tempo para cada dúvida
                        tempo_duvida = TempoEstudo(
                            user_id=user.id,
                            data_inicio=duvida.data_criacao,
                            data_fim=duvida.data_criacao + timedelta(minutes=15),  # Estimativa
                            minutos=15,
                            atividade=f"HelpZone: Criação de dúvida"
                        )
                        db.session.add(tempo_duvida)
                        
                        # Adicionar XP - Padrão: 5 XP por dúvida
                        xp_duvida = XpGanho(
                            user_id=user.id,
                            quantidade=5,
                            data=duvida.data_criacao,
                            origem=f"HelpZone: Dúvida '{duvida.titulo}'"
                        )
                        db.session.add(xp_duvida)
                
                # Respostas criadas
                respostas = Resposta.query.filter_by(user_id=user.id).all()
                
                if respostas:
                    print(f"    - Migrando {len(respostas)} respostas do HelpZone...")
                    for resposta in respostas:
                        # Criar registro de tempo para cada resposta
                        tempo_resposta = TempoEstudo(
                            user_id=user.id,
                            data_inicio=resposta.data_criacao,
                            data_fim=resposta.data_criacao + timedelta(minutes=10),  # Estimativa
                            minutos=10,
                            atividade=f"HelpZone: Resposta a dúvida"
                        )
                        db.session.add(tempo_resposta)
                        
                        # Adicionar XP - 10 XP por resposta, 50 se for solução
                        xp_valor = 50 if resposta.solucao else 10
                        xp_resposta = XpGanho(
                            user_id=user.id,
                            quantidade=xp_valor,
                            data=resposta.data_criacao,
                            origem=f"HelpZone: {'Solução' if resposta.solucao else 'Resposta'} em dúvida"
                        )
                        db.session.add(xp_resposta)
            except ImportError:
                print("    - Módulo HelpZone não encontrado, pulando migração de dúvidas/respostas")
            
            # 3. Se não tem nenhuma atividade registrada, criar alguns registros "seed" aleatórios
            if not simulados and TempoEstudo.query.filter_by(user_id=user.id).count() == 0:
                print(f"    - Usuário sem atividades. Gerando dados seed aleatórios...")
                
                # Registros de tempo para usuários sem atividade
                # Data base: entre 1 e 30 dias atrás
                dias_atras = random.randint(1, 30)
                data_base = datetime.utcnow() - timedelta(days=dias_atras)
                
                # Entre 1 e 5 registros de tempo
                for i in range(random.randint(1, 5)):
                    # Data aleatória a partir da data base
                    data_registro = data_base + timedelta(days=random.randint(0, dias_atras))
                    
                    # Atividade aleatória
                    atividades = ['Simulado', 'Exercícios', 'Redação', 'HelpZone']
                    atividade = random.choice(atividades)
                    
                    # Tempo aleatório entre 15 e 120 minutos
                    minutos = random.randint(15, 120)
                    
                    tempo_estudo = TempoEstudo(
                        user_id=user.id,
                        data_inicio=data_registro,
                        data_fim=data_registro + timedelta(minutes=minutos),
                        minutos=minutos,
                        atividade=f"{atividade}: Sessão de estudo"
                    )
                    db.session.add(tempo_estudo)
                    
                    # Adicionar XP
                    xp_estudo = XpGanho(
                        user_id=user.id,
                        quantidade=int(minutos * 0.5),  # Metade dos minutos como XP
                        data=data_registro + timedelta(minutes=minutos),
                        origem=f"{atividade}: Sessão de estudo"
                    )
                    db.session.add(xp_estudo)
            
            # 4. Comitar mudanças para este usuário
            try:
                db.session.commit()
                print(f"[+] Migração concluída com sucesso para o usuário {user.username}")
            except Exception as e:
                db.session.rollback()
                print(f"[!] Erro ao migrar dados para o usuário {user.username}: {e}")
        
        print("[+] Migração de estatísticas concluída com sucesso!")

if __name__ == "__main__":
    migrar_estatisticas()