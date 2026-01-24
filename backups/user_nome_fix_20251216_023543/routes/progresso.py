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
    Formata minutos em uma string legível melhorada.
    
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
    Marca o início de uma sessão de estudo.
    """
    try:
        from flask import current_app
        
        # Verificar se já existe uma sessão ativa
        sessao_ativa = TempoEstudo.query.filter_by(
            user_id=user_id,
            data_fim=None
        ).first()
        
        # Se existir uma sessão ativa, finalize-a automaticamente
        if sessao_ativa:
            current_app.logger.info(f"Finalizando sessão ativa {sessao_ativa.id} para user {user_id}")
            finalizar_sessao_estudo(sessao_ativa.id, adicionar_xp=False)
        
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
        try:
            from flask import current_app
            current_app.logger.error(f"Erro ao iniciar sessão de estudo para user {user_id}: {e}")
        except:
            print(f"Erro ao iniciar sessão de estudo para user {user_id}: {e}")
        db.session.rollback()
        raise

def finalizar_sessao_estudo(sessao_id, adicionar_xp=True):
    """
    Finaliza uma sessão de estudo, calcula o tempo gasto e adiciona XP.
    """
    try:
        from flask import current_app
        
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
                registrar_xp_ganho(sessao.user_id, xp_a_adicionar, f'Tempo de estudo: {sessao.atividade}')
                resultado['xp_ganho'] = xp_a_adicionar
                current_app.logger.info(f"XP concedido: {xp_a_adicionar} para user {sessao.user_id}")
        
        return resultado
    
    except Exception as e:
        try:
            from flask import current_app
            current_app.logger.error(f"Erro ao finalizar sessão {sessao_id}: {e}")
        except:
            print(f"Erro ao finalizar sessão {sessao_id}: {e}")
        db.session.rollback()
        return {'erro': f'Erro interno: {str(e)}'}

def registrar_xp_ganho(user_id, quantidade, origem):
    """
    Registra XP ganho por um usuário.
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
        
        # Adicionar ao usuário
        usuario = User.query.get(user_id)
        if usuario:
            usuario.xp_total += quantidade
            current_app.logger.info(f"XP adicionado: +{quantidade} para user {user_id} (origem: {origem}). Total: {usuario.xp_total}")
        else:
            current_app.logger.error(f"Usuário {user_id} não encontrado ao adicionar XP")
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
    Página principal de progresso do usuário.
    Exibe estatísticas reais de progresso ou estados vazios para novos usuários.
    """
    # Obter XP total
    xp_total = current_user.xp_total
    
    # Obter simulados concluídos
    simulados = Simulado.query.filter_by(
        user_id=current_user.id,
        status='Concluído'
    ).order_by(Simulado.data_realizado.desc()).limit(3).all()

    # Obter redações enviadas
    redacoes_enviadas = Redacao.query.filter_by(
        user_id=current_user.id
    ).count()
    
    # Verificar se o usuário tem simulados concluídos (forma mais simples de verificar atividade)
    tem_atividades = len(simulados) > 0 or redacoes_enviadas > 0
    
    # Obter estatísticas de tempo
    estatisticas_tempo = obter_estatisticas_tempo_real(current_user.id)
    
    # Formatar os tempos para exibição
    tempos_formatados = {
        'hoje': formatar_tempo_melhorado(estatisticas_tempo['hoje']),
        'semana': formatar_tempo_melhorado(estatisticas_tempo['semana']),
        'mes': formatar_tempo_melhorado(estatisticas_tempo['mes'])
    }
    
    # Obter progresso por área
    progresso_areas = calcular_progresso_areas_real(current_user.id)
    
    # Obter dados de evolução para gráficos
    progresso_semanal = obter_progresso_semanal_real(current_user.id)
    
    return render_template('progresso/index.html',
                          xp_total=xp_total,
                          simulados=simulados,
                          redacoes_enviadas=redacoes_enviadas,
                          progresso_areas=progresso_areas,
                          estatisticas_tempo=estatisticas_tempo,
                          tempos_formatados=tempos_formatados,
                          progresso_semanal=progresso_semanal,
                          tem_atividades=tem_atividades)

def obter_estatisticas_tempo_real(user_id):
    """
    Obtém estatísticas reais de tempo de estudo para o usuário.
    Versão melhorada com logs e consultas mais robustas.
    """
    tempo_hoje = 0
    tempo_semana = 0
    tempo_mes = 0
    
    try:
        # Verificar se a tabela existe
        inspecionar = db.inspect(db.engine)
        if 'tempo_estudo' not in inspecionar.get_table_names():
            print(f"Tabela tempo_estudo não existe, retornando zeros para user {user_id}")
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
            TempoEstudo.minutos.isnot(None)  # Apenas sessões finalizadas
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
        
        # Calcular tempo do mês (primeiro dia do mês até hoje)
        inicio_mes = hoje.replace(day=1)
        inicio_mes_dt = datetime.combine(inicio_mes, datetime.min.time())
        
        registros_mes = TempoEstudo.query.filter(
            TempoEstudo.user_id == user_id,
            TempoEstudo.data_inicio >= inicio_mes_dt,
            TempoEstudo.data_inicio <= fim_hoje,
            TempoEstudo.minutos.isnot(None)
        ).all()
        
        tempo_mes = sum(r.minutos for r in registros_mes if r.minutos)
        print(f"Tempo mês para user {user_id}: {tempo_mes} minutos ({len(registros_mes)} registros)")
        
        # Se não houver registros na tabela TempoEstudo, tentar estimar baseado em atividades
        if tempo_hoje == 0 and tempo_semana == 0 and tempo_mes == 0:
            print(f"Nenhum registro de tempo encontrado para user {user_id}, estimando baseado em atividades")
            tempo_estimado = estimar_tempo_baseado_atividades(user_id)
            tempo_hoje = tempo_estimado.get('hoje', 0)
            tempo_semana = tempo_estimado.get('semana', 0)
            tempo_mes = tempo_estimado.get('mes', 0)
        
    except Exception as e:
        print(f"Erro ao obter estatísticas de tempo para user {user_id}: {e}")
    
    return {
        'hoje': tempo_hoje,
        'semana': tempo_semana,
        'mes': tempo_mes
    }

def estimar_tempo_baseado_atividades(user_id):
    """
    Estima tempo de estudo baseado em atividades realizadas quando 
    não há registros diretos de tempo.
    """
    agora = datetime.utcnow()
    hoje = agora.date()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    inicio_mes = hoje.replace(day=1)
    
    tempo_hoje = 0
    tempo_semana = 0
    tempo_mes = 0
    
    try:
        # Simulados concluídos (estimar 120 minutos por simulado)
        simulados_hoje = Simulado.query.filter(
            Simulado.user_id == user_id,
            Simulado.status == 'Concluído',
            db.func.date(Simulado.data_realizado) == hoje
        ).count()
        tempo_hoje += simulados_hoje * 120
        
        simulados_semana = Simulado.query.filter(
            Simulado.user_id == user_id,
            Simulado.status == 'Concluído',
            db.func.date(Simulado.data_realizado) >= inicio_semana
        ).count()
        tempo_semana += simulados_semana * 120
        
        simulados_mes = Simulado.query.filter(
            Simulado.user_id == user_id,
            Simulado.status == 'Concluído',
            db.func.date(Simulado.data_realizado) >= inicio_mes
        ).count()
        tempo_mes += simulados_mes * 120
        
        # Redações enviadas (estimar 60 minutos por redação)
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
    Se não houver dados, retorna progresso zero para todas as áreas padrão.
    """
    # Áreas padrão do ENEM
    areas_padrao = ['Linguagens', 'Matemática', 'Ciências Humanas', 'Ciências da Natureza']
    
    # Inicializar o resultado com zeros para todas as áreas
    resultado = {}
    for area in areas_padrao:
        resultado[area] = {
            'total': 0,
            'acertos': 0,
            'percentual': 0,
            'exercicios_feitos': 0,
            'total_exercicios': 100  # Valor total fictício para referência
        }
    
    try:
        # Buscar dados reais a partir de simulados concluídos
        simulados = Simulado.query.filter_by(
            user_id=user_id,
            status='Concluído'
        ).all()
        
        # Para cada simulado, contabilizar as questões por área
        for simulado in simulados:
            questoes = Questao.query.filter_by(simulado_id=simulado.id).all()
            
            for questao in questoes:
                # Mapear a área da questão para uma das áreas padrão
                area_padrao = None
                
                if questao.area in areas_padrao:
                    area_padrao = questao.area
                elif 'Linguagens' in questao.area or 'Português' in questao.area:
                    area_padrao = 'Linguagens'
                elif 'Matemática' in questao.area:
                    area_padrao = 'Matemática'
                elif 'Humanas' in questao.area or 'História' in questao.area or 'Geografia' in questao.area:
                    area_padrao = 'Ciências Humanas'
                elif 'Natureza' in questao.area or 'Física' in questao.area or 'Química' in questao.area or 'Biologia' in questao.area:
                    area_padrao = 'Ciências da Natureza'
                else:
                    # Se não conseguir mapear, pular
                    continue
                
                # Contabilizar
                resultado[area_padrao]['total'] += 1
                resultado[area_padrao]['exercicios_feitos'] += 1
                
                if questao.resposta_usuario == questao.resposta_correta:
                    resultado[area_padrao]['acertos'] += 1
        
        # Calcular percentuais
        for area in resultado:
            if resultado[area]['total'] > 0:
                resultado[area]['percentual'] = (resultado[area]['acertos'] / resultado[area]['total']) * 100
    
    except Exception as e:
        # Em caso de erro, retornar zeros para todas as áreas
        print(f"Erro ao calcular progresso por área: {e}")
    
    return resultado

def obter_progresso_semanal_real(user_id):
    """
    Obtém dados reais de progresso semanal (XP ganho por dia).
    Versão melhorada que contabiliza todo tipo de XP ganho.
    """
    # Preparar estrutura de dados para os últimos 7 dias
    data_atual = datetime.utcnow().date()
    datas = []
    valores = []
    
    # Gerar as datas dos últimos 7 dias (de 6 dias atrás até hoje)
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
            print(f"Tabela xp_ganho não existe, retornando zeros para user {user_id}")
            return resultado
        
        # Para cada dia dos últimos 7 dias, consultar o XP ganho
        for i in range(7):
            dia = data_atual - timedelta(days=6-i)
            
            # Definir início e fim do dia
            inicio_dia = datetime.combine(dia, datetime.min.time())
            fim_dia = datetime.combine(dia, datetime.max.time())
            
            # Consultar soma de XP para este dia específico
            xp_dia = db.session.query(
                db.func.coalesce(db.func.sum(XpGanho.quantidade), 0)
            ).filter(
                XpGanho.user_id == user_id,
                XpGanho.data >= inicio_dia,
                XpGanho.data <= fim_dia
            ).scalar()
            
            # Atualizar o valor (xp_dia já é um int devido ao coalesce)
            valores[i] = int(xp_dia) if xp_dia else 0
            
            print(f"XP para user {user_id} em {dia.strftime('%d/%m')}: {valores[i]}")
        
        resultado['valores'] = valores
        
        # Se não há XP registrado na tabela, tentar estimar baseado em atividades
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
    Estima XP ganho baseado em atividades quando não há registros diretos.
    """
    valores = [0] * 7  # 7 dias de zeros
    
    try:
        data_atual = datetime.utcnow().date()
        
        # Para cada dia, verificar atividades
        for i in range(7):
            dia = data_atual - timedelta(days=6-i)
            xp_dia = 0
            
            # Simulados concluídos neste dia (50-80 XP por simulado)
            simulados = Simulado.query.filter(
                Simulado.user_id == user_id,
                Simulado.status == 'Concluído',
                db.func.date(Simulado.data_realizado) == dia
            ).all()
            
            for simulado in simulados:
                # XP baseado na nota TRI (10% da nota)
                if simulado.nota_tri:
                    xp_simulado = round((simulado.nota_tri * 0.1) / 5) * 5
                    xp_dia += int(xp_simulado)
                else:
                    xp_dia += 50  # XP padrão se não há nota
            
            # Redações enviadas neste dia (50 XP por redação + moedas)
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

@progresso_bp.route('/registrar-tempo', methods=['POST'])
@login_required
def registrar_tempo():
    """
    Rota melhorada para iniciar ou finalizar uma sessão de estudo.
    Agora com implementação direta sem ProgressoService.
    """
    data = request.json
    acao = data.get('acao')
    
    if acao == 'iniciar':
        atividade = data.get('atividade', 'geral')
        
        try:
            # Verificar se já existe uma sessão ativa
            sessao_existente = TempoEstudo.query.filter_by(
                user_id=current_user.id,
                data_fim=None
            ).first()
            
            # Se existe uma sessão ativa da mesma atividade, retornar ela
            if sessao_existente and sessao_existente.atividade == atividade:
                tempo_decorrido = (datetime.utcnow() - sessao_existente.data_inicio).total_seconds() / 60
                return jsonify({
                    'sucesso': True,
                    'sessao_id': sessao_existente.id,
                    'mensagem': f'Sessão de {atividade} já estava ativa',
                    'minutos_decorridos': int(tempo_decorrido)
                })
            
            # Se existe sessão de atividade diferente, finalizar a anterior
            if sessao_existente:
                finalizar_sessao_estudo(sessao_existente.id, adicionar_xp=True)
            
            # Criar nova sessão
            sessao = iniciar_sessao_estudo(current_user.id, atividade)
            return jsonify({
                'sucesso': True,
                'sessao_id': sessao.id,
                'mensagem': f'Sessão de {atividade} iniciada!'
            })
            
        except Exception as e:
            print(f"Erro ao iniciar sessão: {e}")
            return jsonify({
                'sucesso': False,
                'mensagem': f'Erro interno: {str(e)}'
            })
    
    elif acao == 'finalizar':
        sessao_id = data.get('sessao_id')
        if not sessao_id:
            return jsonify({
                'sucesso': False,
                'mensagem': 'ID da sessão não fornecido'
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
                'mensagem': f'Sessão finalizada! {resultado["minutos"]} minutos, +{resultado["xp_ganho"]} XP'
            })
            
        except Exception as e:
            print(f"Erro ao finalizar sessão: {e}")
            return jsonify({
                'sucesso': False,
                'mensagem': f'Erro interno: {str(e)}'
            })
    
    return jsonify({
        'sucesso': False,
        'mensagem': 'Ação inválida'
    })

@progresso_bp.route('/ping-sessao', methods=['POST'])
@login_required
def ping_sessao():
    """Recebe pings periódicos para manter a sessão ativa."""
    data = request.json
    sessao_id = data.get('sessao_id')
    
    if not sessao_id:
        return jsonify({'sucesso': False, 'erro': 'ID da sessão não fornecido'})
    
    try:
        # Buscar a sessão
        sessao = TempoEstudo.query.get(sessao_id)
        
        if not sessao or sessao.user_id != current_user.id:
            return jsonify({'sucesso': False, 'erro': 'Sessão não encontrada'})
        
        return jsonify({'sucesso': True})
        
    except Exception as e:
        print(f"Erro no ping da sessão {sessao_id}: {e}")
        return jsonify({'sucesso': False, 'erro': str(e)})

@progresso_bp.route('/finalizar-sessao', methods=['POST'])
@login_required  
def finalizar_sessao_beacon():
    """Finaliza uma sessão via sendBeacon."""
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
        
        return jsonify({'sucesso': False, 'erro': 'ID da sessão não fornecido'})
        
    except Exception as e:
        print(f"Erro ao finalizar sessão via beacon: {e}")
        return jsonify({'sucesso': False, 'erro': str(e)})

@progresso_bp.route('/atividades')
@login_required
def atividades():
    """Página de histórico de atividades do usuário."""
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
    """Retorna o tempo atual de estudo do usuário no dia."""
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
        # Migrar simulados concluídos
        simulados = Simulado.query.filter_by(
            user_id=current_user.id,
            status='Concluído'
        ).all()
        
        for simulado in simulados:
            # Verificar se já existe registro de tempo para este período
            data_simulado = simulado.data_realizado.date() if simulado.data_realizado else None
            if data_simulado:
                existe_tempo = TempoEstudo.query.filter(
                    TempoEstudo.user_id == current_user.id,
                    db.func.date(TempoEstudo.data_inicio) == data_simulado,
                    TempoEstudo.atividade == 'Simulado'
                ).first()
                
                if not existe_tempo:
                    # Calcular minutos do simulado
                    minutos = 120  # Padrão
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
        
        # Migrar redações
        redacoes = Redacao.query.filter_by(user_id=current_user.id).all()
        
        for redacao in redacoes:
            data_redacao = redacao.data_envio.date()
            existe_tempo = TempoEstudo.query.filter(
                TempoEstudo.user_id == current_user.id,
                db.func.date(TempoEstudo.data_inicio) == data_redacao,
                TempoEstudo.atividade == 'Redação'
            ).first()
            
            if not existe_tempo:
                # Criar registro retroativo
                tempo_estudo = TempoEstudo(
                    user_id=current_user.id,
                    data_inicio=redacao.data_envio - timedelta(minutes=60),
                    data_fim=redacao.data_envio,
                    atividade='Redação',
                    minutos=60
                )
                db.session.add(tempo_estudo)
        
        db.session.commit()
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'Dados migrados com sucesso! {len(simulados)} simulados e {len(redacoes)} redações processados.'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro na migração: {str(e)}'
        })