from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app.models.estatisticas import TempoEstudo, ExercicioRealizado, XpGanho
from app.models.simulado import Questao, Simulado
from app.models.redacao import Redacao
from app.models.user import User
from app import db
from datetime import datetime, timedelta
import json

progresso_bp = Blueprint('progresso', __name__, url_prefix='/progresso')

def formatar_tempo_melhorado(minutos):
    """
    Formata minutos em uma string legÃ­vel melhorada.
    
    Args:
        minutos (int): Tempo em minutos
    
    Returns:
        str: Tempo formatado (ex: "2h30" ou "45min")
    """
    if minutos == 0:
        return "0h0"
    
    horas = minutos // 60
    min_restantes = minutos % 60
    
    if horas > 0:
        if min_restantes > 0:
            return f"{horas}h{min_restantes:02d}"
        else:
            return f"{horas}h00"
    else:
        return f"{min_restantes}min"

def iniciar_sessao_estudo(user_id, atividade):
    """
    Marca o inÃ­cio de uma sessÃ£o de estudo.
    """
    try:
        from flask import current_app
        
        # Verificar se jÃ¡ existe uma sessÃ£o ativa
        sessao_ativa = TempoEstudo.query.filter_by(
            user_id=user_id,
            data_fim=None
        ).first()
        
        # Se existir uma sessÃ£o ativa, finalize-a automaticamente
        if sessao_ativa:
            current_app.logger.info(f"Finalizando sessÃ£o ativa {sessao_ativa.id} para user {user_id}")
            finalizar_sessao_estudo(sessao_ativa.id, adicionar_xp=False)
        
        # Criar nova sessÃ£o
        nova_sessao = TempoEstudo(
            user_id=user_id,
            data_inicio=datetime.utcnow(),
            atividade=atividade,
            minutos=0  # Inicializar com 0
        )
        
        db.session.add(nova_sessao)
        db.session.commit()
        
        current_app.logger.info(f"Nova sessÃ£o {nova_sessao.id} iniciada para user {user_id}, atividade: {atividade}")
        
        return nova_sessao
    
    except Exception as e:
        try:
            from flask import current_app
            current_app.logger.error(f"Erro ao iniciar sessÃ£o de estudo para user {user_id}: {e}")
        except:
            print(f"Erro ao iniciar sessÃ£o de estudo para user {user_id}: {e}")
        db.session.rollback()
        raise

def finalizar_sessao_estudo(sessao_id, adicionar_xp=True):
    """
    Finaliza uma sessÃ£o de estudo, calcula o tempo gasto e adiciona XP.
    """
    try:
        from flask import current_app
        
        sessao = TempoEstudo.query.get(sessao_id)
        
        if not sessao:
            current_app.logger.warning(f"SessÃ£o {sessao_id} nÃ£o encontrada")
            return {'erro': 'SessÃ£o nÃ£o encontrada'}
        
        if sessao.data_fim:
            current_app.logger.warning(f"SessÃ£o {sessao_id} jÃ¡ foi finalizada")
            return {'erro': 'SessÃ£o jÃ¡ finalizada'}
        
        agora = datetime.utcnow()
        sessao.data_fim = agora
        
        # Calcular duraÃ§Ã£o em minutos
        duracao = (agora - sessao.data_inicio).total_seconds() / 60
        duracao_minutos = max(1, int(duracao))  # MÃ­nimo de 1 minuto
        sessao.minutos = duracao_minutos
        
        # Salvar no banco
        db.session.commit()
        
        current_app.logger.info(f"SessÃ£o {sessao_id} finalizada: {duracao_minutos} minutos de {sessao.atividade}")
        
        resultado = {
            'minutos': duracao_minutos,
            'xp_ganho': 0
        }
        
        # Adicionar XP ao usuÃ¡rio (2 XP por minuto de estudo, limitado)
        if adicionar_xp and duracao_minutos > 0:
            # PrevenÃ§Ã£o de abuso: mÃ¡ximo 240 XP por sessÃ£o (2 horas)
            xp_a_adicionar = min(duracao_minutos * 2, 240)
            
            if xp_a_adicionar > 0:
                registrar_xp_ganho(sessao.user_id, xp_a_adicionar, f'Tempo de estudo: {sessao.atividade}')
                resultado['xp_ganho'] = xp_a_adicionar
                current_app.logger.info(f"XP concedido: {xp_a_adicionar} para user {sessao.user_id}")
        
        return resultado
    
    except Exception as e:
        try:
            from flask import current_app
            current_app.logger.error(f"Erro ao finalizar sessÃ£o {sessao_id}: {e}")
        except:
            print(f"Erro ao finalizar sessÃ£o {sessao_id}: {e}")
        db.session.rollback()
        return {'erro': f'Erro interno: {str(e)}'}

def registrar_xp_ganho(user_id, quantidade, origem):
    """
    Registra XP ganho por um usuÃ¡rio.
    """
    try:
        from flask import current_app
        
        # Criar registro de XP
        xp_ganho = XpGanho(
            user_id=user_id,
            quantidade=quantidade,
            origem=origem,
            data=datetime.utcnow()
        )
        
        # Adicionar ao usuÃ¡rio
        usuario = User.query.get(user_id)
        if usuario:
            usuario.xp_total += quantidade
            current_app.logger.info(f"XP adicionado: +{quantidade} para user {user_id} (origem: {origem}). Total: {usuario.xp_total}")
        else:
            current_app.logger.error(f"UsuÃ¡rio {user_id} nÃ£o encontrado ao adicionar XP")
            return None
        
        # Salvar no banco
        db.session.add(xp_ganho)
        db.session.commit()
        
        return xp_ganho
    
    except Exception as e:
        try:
            from flask import current_app
            current_app.logger.error(f"Erro ao registrar XP para user {user_id}: {e}")
        except:
            print(f"Erro ao registrar XP para user {user_id}: {e}")
        db.session.rollback()
        return None

@progresso_bp.route('/')
@login_required
def index():
    """
    PÃ¡gina principal de progresso do usuÃ¡rio.
    Exibe estatÃ­sticas reais de progresso ou estados vazios para novos usuÃ¡rios.
    """
    # Obter XP total
    xp_total = current_user.xp_total
    
    # Obter simulados concluÃ­dos
    # Total para o card de summary
    total_simulados = Simulado.query.filter_by(
        user_id=current_user.id
        #status='ConcluÃ­do'
    ).count()
    
    # Os 3 mais recentes para a tabela
    simulados_recentes = Simulado.query.filter_by(
        user_id=current_user.id,
        status='ConcluÃ­do'
    ).order_by(Simulado.data_realizado.desc()).limit(3).all()

    # Obter redaÃ§Ãµes enviadas
    redacoes_enviadas = Redacao.query.filter_by(
        user_id=current_user.id
    ).count()
    
    # Verificar se o usuÃ¡rio tem simulados concluÃ­dos (forma mais simples de verificar atividade)
    tem_atividades = total_simulados > 0 or redacoes_enviadas > 0

    # Obter estatÃ­sticas de tempo
    estatisticas_tempo = obter_estatisticas_tempo_real(current_user.id)
    
    # Formatar os tempos para exibiÃ§Ã£o
    tempos_formatados = {
        'hoje': formatar_tempo_melhorado(estatisticas_tempo['hoje']),
        'semana': formatar_tempo_melhorado(estatisticas_tempo['semana']),
        'mes': formatar_tempo_melhorado(estatisticas_tempo['mes'])
    }
    
    # Obter progresso por área
    progresso_areas = calcular_progresso_areas_real(current_user.id)
    
    # Obter dados de evolução para gráficos
    progresso_semanal = obter_progresso_semanal_real(current_user.id)
    dados_simulados = obter_dados_simulados_7_dias(current_user.id)
    dados_redacoes = obter_dados_redacoes_7_dias(current_user.id)
    dados_horas = obter_dados_horas_7_dias(current_user.id)
    
    return render_template('progresso/index.html',
                          xp_total=xp_total,
                          total_simulados=total_simulados,
                          simulados_recentes=simulados_recentes,
                          redacoes_enviadas=redacoes_enviadas,
                          progresso_areas=progresso_areas,
                          estatisticas_tempo=estatisticas_tempo,
                          tempos_formatados=tempos_formatados,
                          grafico_xp=progresso_semanal,
                          grafico_simulados=dados_simulados,
                          grafico_redacoes=dados_redacoes,
                          grafico_tempo=dados_horas,
                          tem_atividades=tem_atividades)

def obter_estatisticas_tempo_real(user_id):
    """
    ObtÃ©m estatÃ­sticas reais de tempo de estudo para o usuÃ¡rio.
    VersÃ£o melhorada com logs e consultas mais robustas.
    """
    tempo_hoje = 0
    tempo_semana = 0
    tempo_mes = 0
    
    try:
        # Verificar se a tabela existe
        inspecionar = db.inspect(db.engine)
        if 'tempo_estudo' not in inspecionar.get_table_names():
            print(f"Tabela tempo_estudo nÃ£o existe, retornando zeros para user {user_id}")
            return {'hoje': tempo_hoje, 'semana': tempo_semana, 'mes': tempo_mes}
        
        # Data atual
        agora = datetime.utcnow()
        hoje = agora.date()
        
        # Calcular tempo hoje
        inicio_hoje = datetime.combine(hoje, datetime.min.time())
        fim_hoje = datetime.combine(hoje, datetime.max.time())
        
        registros_hoje = TempoEstudo.query.filter(
            TempoEstudo.user_id == user_id,
            TempoEstudo.data_inicio >= inicio_hoje,
            TempoEstudo.data_inicio <= fim_hoje,
            TempoEstudo.minutos.isnot(None)  # Apenas sessÃµes finalizadas
        ).all()
        
        tempo_hoje = sum(r.minutos for r in registros_hoje if r.minutos)
        print(f"Tempo hoje para user {user_id}: {tempo_hoje} minutos ({len(registros_hoje)} registros)")
        
        # Calcular tempo da semana (segunda-feira a hoje)
        dias_desde_segunda = hoje.weekday()  # 0 = segunda, 6 = domingo
        inicio_semana = hoje - timedelta(days=dias_desde_segunda)
        inicio_semana_dt = datetime.combine(inicio_semana, datetime.min.time())
        
        registros_semana = TempoEstudo.query.filter(
            TempoEstudo.user_id == user_id,
            TempoEstudo.data_inicio >= inicio_semana_dt,
            TempoEstudo.data_inicio <= fim_hoje,
            TempoEstudo.minutos.isnot(None)
        ).all()
        
        tempo_semana = sum(r.minutos for r in registros_semana if r.minutos)
        print(f"Tempo semana para user {user_id}: {tempo_semana} minutos ({len(registros_semana)} registros)")
        
        # Calcular tempo do mÃªs (primeiro dia do mÃªs atÃ© hoje)
        inicio_mes = hoje.replace(day=1)
        inicio_mes_dt = datetime.combine(inicio_mes, datetime.min.time())
        
        registros_mes = TempoEstudo.query.filter(
            TempoEstudo.user_id == user_id,
            TempoEstudo.data_inicio >= inicio_mes_dt,
            TempoEstudo.data_inicio <= fim_hoje,
            TempoEstudo.minutos.isnot(None)
        ).all()
        
        tempo_mes = sum(r.minutos for r in registros_mes if r.minutos)
        print(f"Tempo mÃªs para user {user_id}: {tempo_mes} minutos ({len(registros_mes)} registros)")
        
        # Se nÃ£o houver registros na tabela TempoEstudo, tentar estimar baseado em atividades
        if tempo_hoje == 0 and tempo_semana == 0 and tempo_mes == 0:
            print(f"Nenhum registro de tempo encontrado para user {user_id}, estimando baseado em atividades")
            tempo_estimado = estimar_tempo_baseado_atividades(user_id)
            tempo_hoje = tempo_estimado.get('hoje', 0)
            tempo_semana = tempo_estimado.get('semana', 0)
            tempo_mes = tempo_estimado.get('mes', 0)
        
    except Exception as e:
        print(f"Erro ao obter estatÃ­sticas de tempo para user {user_id}: {e}")
    
    return {
        'hoje': tempo_hoje,
        'semana': tempo_semana,
        'mes': tempo_mes
    }

def estimar_tempo_baseado_atividades(user_id):
    """
    Estima tempo de estudo baseado em atividades realizadas quando 
    nÃ£o hÃ¡ registros diretos de tempo.
    """
    agora = datetime.utcnow()
    hoje = agora.date()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    inicio_mes = hoje.replace(day=1)
    
    tempo_hoje = 0
    tempo_semana = 0
    tempo_mes = 0
    
    try:
        # Simulados concluÃ­dos (estimar 120 minutos por simulado)
        simulados_hoje = Simulado.query.filter(
            Simulado.user_id == user_id,
            Simulado.status == 'ConcluÃ­do',
            db.func.date(Simulado.data_realizado) == hoje
        ).count()
        tempo_hoje += simulados_hoje * 120
        
        simulados_semana = Simulado.query.filter(
            Simulado.user_id == user_id,
            Simulado.status == 'ConcluÃ­do',
            db.func.date(Simulado.data_realizado) >= inicio_semana
        ).count()
        tempo_semana += simulados_semana * 120
        
        simulados_mes = Simulado.query.filter(
            Simulado.user_id == user_id,
            Simulado.status == 'ConcluÃ­do',
            db.func.date(Simulado.data_realizado) >= inicio_mes
        ).count()
        tempo_mes += simulados_mes * 120
        
        # RedaÃ§Ãµes enviadas (estimar 60 minutos por redaÃ§Ã£o)
        redacoes_hoje = Redacao.query.filter(
            Redacao.user_id == user_id,
            db.func.date(Redacao.data_envio) == hoje
        ).count()
        tempo_hoje += redacoes_hoje * 60
        
        redacoes_semana = Redacao.query.filter(
            Redacao.user_id == user_id,
            db.func.date(Redacao.data_envio) >= inicio_semana
        ).count()
        tempo_semana += redacoes_semana * 60
        
        redacoes_mes = Redacao.query.filter(
            Redacao.user_id == user_id,
            db.func.date(Redacao.data_envio) >= inicio_mes
        ).count()
        tempo_mes += redacoes_mes * 60
        
    except Exception as e:
        print(f"Erro ao estimar tempo baseado em atividades: {e}")
    
    return {
        'hoje': tempo_hoje,
        'semana': tempo_semana,
        'mes': tempo_mes
    }

def calcular_progresso_areas_real(user_id):
    """
    Calcula o progresso real do usuário por área de conhecimento.
    Versão melhorada com logs de diagnóstico.
    """
    # Áreas padrão do ENEM
    areas_padrao = ['Linguagens', 'Matemática', 'Humanas', 'Natureza']
    
    # Mapeamento completo de disciplinas para áreas
    mapeamento_areas = {
        'Português': 'Linguagens',
        'Literatura': 'Linguagens', 
        'Inglês': 'Linguagens',
        'Espanhol': 'Linguagens',
        'Artes': 'Linguagens',
        'Linguagens': 'Linguagens',
        'Redação': 'Linguagens',
        'Língua Portuguesa': 'Linguagens',
        
        'Matemática': 'Matemática',
        'Mat': 'Matemática',
        
        'História': 'Humanas',
        'Geografia': 'Humanas',
        'Filosofia': 'Humanas',
        'Sociologia': 'Humanas',
        'Ciências Humanas': 'Humanas',
        'Humanas': 'Humanas',
        
        'Física': 'Natureza',
        'Química': 'Natureza',
        'Biologia': 'Natureza',
        'Ciências da Natureza': 'Natureza',
        'Natureza': 'Natureza'
    }
    
    # Inicializar o resultado com zeros para todas as áreas
    resultado = {}
    for area in areas_padrao:
        resultado[area] = {
            'total': 0,
            'acertos': 0,
            'percentual': 0
        }


    try:
        # Buscar dados reais a partir de simulados concluídos
        simulados = Simulado.query.filter_by(
            user_id=user_id,
            status='Concluído'
        ).all()
        
        print(f"\n=== DIAGNÓSTICO PROGRESSO POR ÁREA (User {user_id}) ===")
        print(f"Total de simulados concluídos: {len(simulados)}")
        
        # Para cada simulado, contabilizar as questões por área
        questoes_sem_mapeamento = []
        
        for simulado in simulados:
            questoes = Questao.query.filter_by(simulado_id=simulado.id).all()
            print(f"\nSimulado {simulado.id}: {len(questoes)} questões")
            
            for questao in questoes:
                # Log da área da questão
                area_original = questao.area if questao.area else "(sem área)"
                
                # Mapear a área da questão usando o dicionário
                area_display = mapeamento_areas.get(questao.area, None)
                
                if not area_display:
                    # Tentar mapeamento parcial (se contiver o texto)
                    for disciplina, area in mapeamento_areas.items():
                        if disciplina in (questao.area or ""):
                            area_display = area
                            break
                
                # Se conseguiu mapear, contabilizar
                if area_display and area_display in resultado:
                    resultado[area_display]['total'] += 1
                    
                    # Verificar acerto
                    acertou = questao.resposta_usuario == questao.resposta_correta
                    if acertou:
                        resultado[area_display]['acertos'] += 1
                else:
                    # Registrar questões sem mapeamento
                    if area_original not in questoes_sem_mapeamento:
                        questoes_sem_mapeamento.append(area_original)
        
        # Log de questões sem mapeamento
        if questoes_sem_mapeamento:
            print(f"\n⚠️ Áreas sem mapeamento encontradas: {questoes_sem_mapeamento}")
        
        # Calcular percentuais
        for area in resultado:
            if resultado[area]['total'] > 0:
                resultado[area]['percentual'] = (resultado[area]['acertos'] / resultado[area]['total']) * 100
                print(f"{area}: {resultado[area]['acertos']}/{resultado[area]['total']} = {resultado[area]['percentual']:.1f}%")
            else:
                print(f"{area}: Nenhuma questão")
        
        print("=== FIM DIAGNÓSTICO ===\n")
    
    except Exception as e:
        # Em caso de erro, retornar zeros para todas as áreas
        print(f"❌ Erro ao calcular progresso por área: {e}")
        import traceback
        traceback.print_exc()
    
    return resultado


def obter_progresso_semanal_real(user_id):
    """
    ObtÃ©m dados reais de progresso semanal (XP ganho por dia).
    VersÃ£o melhorada que contabiliza todo tipo de XP ganho.
    """
    # Preparar estrutura de dados para os Ãºltimos 7 dias
    data_atual = datetime.utcnow().date()
    datas = []
    valores = []
    
    # Gerar as datas dos Ãºltimos 7 dias (de 6 dias atrÃ¡s atÃ© hoje)
    for i in range(6, -1, -1):
        data = data_atual - timedelta(days=i)
        datas.append(data.strftime('%d/%m'))
        valores.append(0)  # Inicializar com zero
    
    resultado = {
        'datas': datas,
        'valores': valores
    }
    
    try:
        # Verificar se a tabela XpGanho existe
        inspecionar = db.inspect(db.engine)
        if 'xp_ganho' not in inspecionar.get_table_names():
            print(f"Tabela xp_ganho nÃ£o existe, retornando zeros para user {user_id}")
            return resultado
        
        # Para cada dia dos Ãºltimos 7 dias, consultar o XP ganho
        for i in range(7):
            dia = data_atual - timedelta(days=6-i)
            
            # Definir inÃ­cio e fim do dia
            inicio_dia = datetime.combine(dia, datetime.min.time())
            fim_dia = datetime.combine(dia, datetime.max.time())
            
            # Consultar soma de XP para este dia especÃ­fico
            xp_dia = db.session.query(
                db.func.coalesce(db.func.sum(XpGanho.quantidade), 0)
            ).filter(
                XpGanho.user_id == user_id,
                XpGanho.data >= inicio_dia,
                XpGanho.data <= fim_dia
            ).scalar()
            
            # Atualizar o valor (xp_dia jÃ¡ Ã© um int devido ao coalesce)
            valores[i] = int(xp_dia) if xp_dia else 0
            
            print(f"XP para user {user_id} em {dia.strftime('%d/%m')}: {valores[i]}")
        
        resultado['valores'] = valores
        
        # Se nÃ£o hÃ¡ XP registrado na tabela, tentar estimar baseado em atividades
        total_xp = sum(valores)
        if total_xp == 0:
            print(f"Nenhum XP encontrado na tabela, estimando para user {user_id}")
            xp_estimado = estimar_xp_baseado_atividades(user_id, datas)
            resultado['valores'] = xp_estimado
        
    except Exception as e:
        print(f"Erro ao obter progresso semanal para user {user_id}: {e}")
    
    return resultado

def estimar_xp_baseado_atividades(user_id, datas):
    """
    Estima XP ganho baseado em atividades quando nÃ£o hÃ¡ registros diretos.
    """
    valores = [0] * 7  # 7 dias de zeros
    
    try:
        data_atual = datetime.utcnow().date()
        
        # Para cada dia, verificar atividades
        for i in range(7):
            dia = data_atual - timedelta(days=6-i)
            xp_dia = 0
            
            # Simulados concluÃ­dos neste dia (50-80 XP por simulado)
            simulados = Simulado.query.filter(
                Simulado.user_id == user_id,
                Simulado.status == 'ConcluÃ­do',
                db.func.date(Simulado.data_realizado) == dia
            ).all()
            
            for simulado in simulados:
                # XP baseado na nota TRI (10% da nota)
                if simulado.nota_tri:
                    xp_simulado = round((simulado.nota_tri * 0.1) / 5) * 5
                    xp_dia += int(xp_simulado)
                else:
                    xp_dia += 50  # XP padrÃ£o se nÃ£o hÃ¡ nota
            
            # RedaÃ§Ãµes enviadas neste dia (50 XP por redaÃ§Ã£o + moedas)
            redacoes = Redacao.query.filter(
                Redacao.user_id == user_id,
                db.func.date(Redacao.data_envio) == dia
            ).all()
            
            for redacao in redacoes:
                xp_dia += 50  # XP base por envio
                # XP adicional baseado na nota (se avaliada)
                if redacao.nota_final:
                    moedas = (redacao.nota_final // 100) * 10
                    xp_dia += moedas
            
            valores[i] = xp_dia
            
    except Exception as e:
        print(f"Erro ao estimar XP baseado em atividades: {e}")
    
    return valores


def obter_dados_simulados_7_dias(user_id):
    """
    Obtém dados de simulados dos últimos 7 dias.
    Retorna média, última e melhor nota por dia.
    """
    data_atual = datetime.utcnow().date()
    datas = []
    medias = []
    ultimas = []
    melhores = []
    
    # Gerar as datas dos últimos 7 dias
    for i in range(6, -1, -1):
        data = data_atual - timedelta(days=i)
        datas.append(data.strftime('%d/%m'))
        medias.append(0)
        ultimas.append(0)
        melhores.append(0)
    
    resultado = {
        'datas': datas,
        'media': medias,
        'ultima': ultimas,
        'melhor': melhores
    }
    
    try:
        # Para cada dia dos últimos 7 dias
        for i in range(7):
            dia = data_atual - timedelta(days=6-i)
            
            # Buscar simulados concluídos neste dia
            simulados_dia = Simulado.query.filter(
                Simulado.user_id == user_id,
                Simulado.status == 'Concluído',
                db.func.date(Simulado.data_realizado) == dia,
                Simulado.nota_tri.isnot(None)
            ).all()
            
            if simulados_dia:
                notas = [s.nota_tri for s in simulados_dia if s.nota_tri]
                
                if notas:
                    # Média das notas
                    medias[i] = round(sum(notas) / len(notas), 1)
                    
                    # Última nota (último simulado do dia)
                    ultimas[i] = round(notas[-1], 1)
                    
                    # Melhor nota
                    melhores[i] = round(max(notas), 1)
        
        resultado['media'] = medias
        resultado['ultima'] = ultimas
        resultado['melhor'] = melhores
        
    except Exception as e:
        print(f"Erro ao obter dados de simulados para user {user_id}: {e}")
    
    return resultado

def obter_dados_redacoes_7_dias(user_id):
    """
    Obtém dados de redações dos últimos 7 dias.
    Retorna média, última e melhor nota por dia.
    """
    data_atual = datetime.utcnow().date()
    datas = []
    medias = []
    ultimas = []
    melhores = []
    
    # Gerar as datas dos últimos 7 dias
    for i in range(6, -1, -1):
        data = data_atual - timedelta(days=i)
        datas.append(data.strftime('%d/%m'))
        medias.append(0)
        ultimas.append(0)
        melhores.append(0)
    
    resultado = {
        'datas': datas,
        'media': medias,
        'ultima': ultimas,
        'melhor': melhores
    }
    
    try:
        # Para cada dia dos últimos 7 dias
        for i in range(7):
            dia = data_atual - timedelta(days=6-i)
            
            # Buscar redações enviadas neste dia com nota
            redacoes_dia = Redacao.query.filter(
                Redacao.user_id == user_id,
                db.func.date(Redacao.data_envio) == dia,
                Redacao.nota_final.isnot(None)
            ).all()
            
            if redacoes_dia:
                notas = [r.nota_final for r in redacoes_dia if r.nota_final]
                
                if notas:
                    # Média das notas
                    medias[i] = round(sum(notas) / len(notas), 1)
                    
                    # Última nota (última redação do dia)
                    ultimas[i] = round(notas[-1], 1)
                    
                    # Melhor nota
                    melhores[i] = round(max(notas), 1)
        
        resultado['media'] = medias
        resultado['ultima'] = ultimas
        resultado['melhor'] = melhores
        
    except Exception as e:
        print(f"Erro ao obter dados de redações para user {user_id}: {e}")
    
    return resultado

def obter_dados_horas_7_dias(user_id):
    """
    Obtém dados de horas de estudo dos últimos 7 dias em minutos.
    """
    data_atual = datetime.utcnow().date()
    datas = []
    minutos = []
    
    # Gerar as datas dos últimos 7 dias
    for i in range(6, -1, -1):
        data = data_atual - timedelta(days=i)
        datas.append(data.strftime('%d/%m'))
        minutos.append(0)
    
    resultado = {
        'datas': datas,
        'minutos': minutos
    }
    
    try:
        # Verificar se a tabela existe
        inspecionar = db.inspect(db.engine)
        if 'tempo_estudo' not in inspecionar.get_table_names():
            print(f"Tabela tempo_estudo não existe, retornando zeros para user {user_id}")
            return resultado
        
        # Para cada dia dos últimos 7 dias
        for i in range(7):
            dia = data_atual - timedelta(days=6-i)
            
            # Definir início e fim do dia
            inicio_dia = datetime.combine(dia, datetime.min.time())
            fim_dia = datetime.combine(dia, datetime.max.time())
            
            # Buscar tempo de estudo deste dia
            registros_dia = TempoEstudo.query.filter(
                TempoEstudo.user_id == user_id,
                TempoEstudo.data_inicio >= inicio_dia,
                TempoEstudo.data_inicio <= fim_dia,
                TempoEstudo.minutos.isnot(None)
            ).all()
            
            # Somar os minutos
            if registros_dia:
                minutos[i] = sum(r.minutos for r in registros_dia if r.minutos)
        
        resultado['minutos'] = minutos
        
    except Exception as e:
        print(f"Erro ao obter dados de horas para user {user_id}: {e}")
    
    return resultado

@progresso_bp.route('/registrar-tempo', methods=['POST'])
@login_required
def registrar_tempo():
    """
    Rota melhorada para iniciar ou finalizar uma sessÃ£o de estudo.
    Agora com implementaÃ§Ã£o direta sem ProgressoService.
    """
    data = request.json
    acao = data.get('acao')
    
    if acao == 'iniciar':
        atividade = data.get('atividade', 'geral')
        
        try:
            # Verificar se jÃ¡ existe uma sessÃ£o ativa
            sessao_existente = TempoEstudo.query.filter_by(
                user_id=current_user.id,
                data_fim=None
            ).first()
            
            # Se existe uma sessÃ£o ativa da mesma atividade, retornar ela
            if sessao_existente and sessao_existente.atividade == atividade:
                tempo_decorrido = (datetime.utcnow() - sessao_existente.data_inicio).total_seconds() / 60
                return jsonify({
                    'sucesso': True,
                    'sessao_id': sessao_existente.id,
                    'mensagem': f'SessÃ£o de {atividade} jÃ¡ estava ativa',
                    'minutos_decorridos': int(tempo_decorrido)
                })
            
            # Se existe sessÃ£o de atividade diferente, finalizar a anterior
            if sessao_existente:
                finalizar_sessao_estudo(sessao_existente.id, adicionar_xp=True)
            
            # Criar nova sessÃ£o
            sessao = iniciar_sessao_estudo(current_user.id, atividade)
            return jsonify({
                'sucesso': True,
                'sessao_id': sessao.id,
                'mensagem': f'SessÃ£o de {atividade} iniciada!'
            })
            
        except Exception as e:
            print(f"Erro ao iniciar sessÃ£o: {e}")
            return jsonify({
                'sucesso': False,
                'mensagem': f'Erro interno: {str(e)}'
            })
    
    elif acao == 'finalizar':
        sessao_id = data.get('sessao_id')
        if not sessao_id:
            return jsonify({
                'sucesso': False,
                'mensagem': 'ID da sessÃ£o nÃ£o fornecido'
            })
        
        try:
            resultado = finalizar_sessao_estudo(sessao_id)
            if 'erro' in resultado:
                return jsonify({
                    'sucesso': False,
                    'mensagem': resultado['erro']
                })


            return jsonify({
                'sucesso': True,
                'minutos': resultado['minutos'],
                'xp_ganho': resultado['xp_ganho'],
                'mensagem': f'SessÃ£o finalizada! {resultado["minutos"]} minutos, +{resultado["xp_ganho"]} XP'
            })
            
        except Exception as e:
            print(f"Erro ao finalizar sessÃ£o: {e}")
            return jsonify({
                'sucesso': False,
                'mensagem': f'Erro interno: {str(e)}'
            })
    
    return jsonify({
        'sucesso': False,
        'mensagem': 'AÃ§Ã£o invÃ¡lida'
    })

@progresso_bp.route('/ping-sessao', methods=['POST'])
@login_required
def ping_sessao():
    """Recebe pings periÃ³dicos para manter a sessÃ£o ativa."""
    data = request.json
    sessao_id = data.get('sessao_id')
    
    if not sessao_id:
        return jsonify({'sucesso': False, 'erro': 'ID da sessÃ£o nÃ£o fornecido'})
    
    try:
        # Buscar a sessÃ£o
        sessao = TempoEstudo.query.get(sessao_id)
        
        if not sessao or sessao.user_id != current_user.id:
            return jsonify({'sucesso': False, 'erro': 'SessÃ£o nÃ£o encontrada'})
        
        return jsonify({'sucesso': True})
        
    except Exception as e:
        print(f"Erro no ping da sessÃ£o {sessao_id}: {e}")
        return jsonify({'sucesso': False, 'erro': str(e)})

@progresso_bp.route('/finalizar-sessao', methods=['POST'])
@login_required  
def finalizar_sessao_beacon():
    """Finaliza uma sessÃ£o via sendBeacon."""
    try:
        if request.is_json:
            data = request.json
        else:
            import json
            data = json.loads(request.data.decode('utf-8'))
        
        sessao_id = data.get('sessao_id')
        
        if sessao_id:
            resultado = finalizar_sessao_estudo(sessao_id)
            return jsonify({'sucesso': True, 'resultado': resultado})
        
        return jsonify({'sucesso': False, 'erro': 'ID da sessÃ£o nÃ£o fornecido'})
        
    except Exception as e:
        print(f"Erro ao finalizar sessÃ£o via beacon: {e}")
        return jsonify({'sucesso': False, 'erro': str(e)})

@progresso_bp.route('/atividades')
@login_required
def atividades():
    """PÃ¡gina de histÃ³rico de atividades do usuÃ¡rio."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Obter registros de XP (que servem como atividades)
    xp_registros = XpGanho.query.filter_by(user_id=current_user.id)\
                          .order_by(XpGanho.data.desc())\
                          .paginate(page=page, per_page=per_page)
    
    return render_template('progresso/atividades.html',
                          registros=xp_registros,
                          tem_atividades=xp_registros.total > 0)

@progresso_bp.route('/tempo-atual')
@login_required
def tempo_atual():
    """Retorna o tempo atual de estudo do usuÃ¡rio no dia."""
    tempo_hoje = obter_estatisticas_tempo_real(current_user.id)['hoje']
    
    return jsonify({
        'tempo_hoje': tempo_hoje,
        'formatado': formatar_tempo_melhorado(tempo_hoje)
    })

@progresso_bp.route('/migrar-dados-tempo', methods=['POST'])
@login_required
def migrar_dados_tempo():
    """Migra dados existentes para gerar registros de tempo de estudo."""
    try:
        # Migrar simulados concluÃ­dos
        simulados = Simulado.query.filter_by(
            user_id=current_user.id,
            status='ConcluÃ­do'
        ).all()
        
        for simulado in simulados:
            # Verificar se jÃ¡ existe registro de tempo para este perÃ­odo
            data_simulado = simulado.data_realizado.date() if simulado.data_realizado else None
            if data_simulado:
                existe_tempo = TempoEstudo.query.filter(
                    TempoEstudo.user_id == current_user.id,
                    db.func.date(TempoEstudo.data_inicio) == data_simulado,
                    TempoEstudo.atividade == 'Simulado'
                ).first()
                
                if not existe_tempo:
                    # Calcular minutos do simulado
                    minutos = 120  # PadrÃ£o
                    if simulado.tempo_realizado:
                        try:
                            tempo_str = simulado.tempo_realizado
                            if 'h' in tempo_str:
                                partes = tempo_str.split('h')
                                horas = int(partes[0])
                                mins = int(partes[1]) if partes[1] else 0
                                minutos = (horas * 60) + mins
                        except:
                            pass
                    
                    # Criar registro retroativo
                    tempo_estudo = TempoEstudo(
                        user_id=current_user.id,
                        data_inicio=simulado.data_realizado - timedelta(minutes=minutos),
                        data_fim=simulado.data_realizado,
                        atividade='Simulado',
                        minutos=minutos
                    )
                    db.session.add(tempo_estudo)
        
        # Migrar redaÃ§Ãµes
        redacoes = Redacao.query.filter_by(user_id=current_user.id).all()
        
        for redacao in redacoes:
            data_redacao = redacao.data_envio.date()
            existe_tempo = TempoEstudo.query.filter(
                TempoEstudo.user_id == current_user.id,
                db.func.date(TempoEstudo.data_inicio) == data_redacao,
                TempoEstudo.atividade == 'RedaÃ§Ã£o'
            ).first()
            
            if not existe_tempo:
                # Criar registro retroativo
                tempo_estudo = TempoEstudo(
                    user_id=current_user.id,
                    data_inicio=redacao.data_envio - timedelta(minutes=60),
                    data_fim=redacao.data_envio,
                    atividade='RedaÃ§Ã£o',
                    minutos=60
                )
                db.session.add(tempo_estudo)
        
        db.session.commit()
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'Dados migrados com sucesso! {len(simulados)} simulados e {len(redacoes)} redaÃ§Ãµes processados.'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro na migraÃ§Ã£o: {str(e)}'
        })
