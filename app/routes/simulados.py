from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app.models.simulado import Simulado, Questao, Alternativa
from app.decorators.freemium import requer_simulado_disponivel
from app.models.user import User
from app import db
from datetime import datetime, timedelta
from flask import current_app
import json
from app.services.xp_service import XpService
from app.services.gerador_questoes import (
    GeradorQuestoes, 
    gerar_questoes_materia_topico,
    obter_topicos_disponiveis
)


simulados_bp = Blueprint('simulados', __name__, url_prefix='/simulados')

@simulados_bp.route('/')
@login_required
def index():
    # Obter simulados pendentes
    simulados_pendentes = Simulado.query.filter_by(
        user_id=current_user.id,
        status='Pendente'
    ).all()
    
    # Obter simulados concluídos
    simulados_concluidos = Simulado.query.filter_by(
        user_id=current_user.id,
        status='Concluído'
    ).order_by(Simulado.data_realizado.desc()).all()
    
    # Obter estatísticas TRI (simulado para o gráfico)
    tri_ultimos_simulados = Simulado.query.filter_by(
        user_id=current_user.id,
        status='Concluído'
    ).order_by(Simulado.data_realizado.desc()).limit(3).all()
    
    # Formatar dados para o gráfico
    datas_grafico = []
    notas_grafico = []
    
    for sim in reversed(tri_ultimos_simulados):
        datas_grafico.append(sim.data_realizado.strftime('%d/%m'))
        notas_grafico.append(sim.nota_tri)
    
    # ✅ CORREÇÃO: Mapear disciplinas reais para áreas do ENEM
    mapeamento_areas = {
        'Português': 'Linguagens',
        'Literatura': 'Linguagens', 
        'Inglês': 'Linguagens',
        'Espanhol': 'Linguagens',
        'Artes': 'Linguagens',
        'Matemática': 'Matemática',
        'História': 'Humanas',
        'Geografia': 'Humanas',
        'Filosofia': 'Humanas',
        'Sociologia': 'Humanas',
        'Física': 'Natureza',
        'Química': 'Natureza',
        'Biologia': 'Natureza'
    }
    
    # Inicializar contadores para as 4 áreas principais
    desempenho_areas = {'Linguagens': 0, 'Matemática': 0, 'Humanas': 0, 'Natureza': 0}
    contadores = {
        'Linguagens': {'total': 0, 'acertos': 0}, 
        'Matemática': {'total': 0, 'acertos': 0}, 
        'Humanas': {'total': 0, 'acertos': 0}, 
        'Natureza': {'total': 0, 'acertos': 0}
    }
    
    # Buscar TODAS as questões de simulados concluídos
    todas_questoes = db.session.query(Questao).join(
        Simulado, Questao.simulado_id == Simulado.id
        ).filter(
            Simulado.user_id == current_user.id,
            Simulado.status == 'Concluído'
    ).all()
    
    print(f"DEBUG: Encontradas {len(todas_questoes)} questões")  # Log para debug
    
    # Processar cada questão e mapear para a área correta
    for questao in todas_questoes:
        # Mapear a disciplina real para área de exibição
        area_display = mapeamento_areas.get(questao.area, questao.area)
        
        print(f"DEBUG: Questão área='{questao.area}' mapeada='{area_display}'")  # Log para debug
        
        # Se a área mapeada existe nos contadores, contabilizar
        if area_display in contadores:
            contadores[area_display]['total'] += 1
            if questao.verificar_resposta():
                contadores[area_display]['acertos'] += 1
    
    # Calcular percentuais finais
    for area in contadores:
        if contadores[area]['total'] > 0:
            desempenho_areas[area] = round((contadores[area]['acertos'] / contadores[area]['total']) * 100)
        else:
            desempenho_areas[area] = 0
    
    print(f"DEBUG: Contadores finais: {contadores}")  # Log para debug
    print(f"DEBUG: Desempenho áreas: {desempenho_areas}")  # Log para debug
    
    return render_template('simulados/index.html',
                          simulados_pendentes=simulados_pendentes,
                          simulados_concluidos=simulados_concluidos,
                          datas_grafico=datas_grafico,
                          notas_grafico=notas_grafico,
                          desempenho_areas=desempenho_areas)


@simulados_bp.route('/<int:simulado_id>')
@login_required
@requer_simulado_disponivel

def iniciar_simulado(simulado_id):
    simulado = Simulado.query.get_or_404(simulado_id)
    
    # Verificar se o simulado pertence ao usuário
    if simulado.user_id != current_user.id:
        flash('Você não tem permissão para acessar este simulado.', 'danger')
        return redirect(url_for('simulados.index'))
    
    # Verificar se o simulado já foi realizado
    if simulado.status == 'Concluído':
        return redirect(url_for('simulados.resultado', simulado_id=simulado_id))

    # ✨ CONSUMIR SIMULADO GRATUITO (quando marcar como iniciado)
    if not simulado.data_realizado:
        simulado.data_realizado = datetime.utcnow()
        current_user.consumir_simulado_gratuito()
        db.session.commit()

    # Marcar horário de início se for a primeira vez
    if not simulado.data_realizado:
        simulado.data_realizado = datetime.utcnow()
        db.session.commit()
    
    # Obter a primeira questão do simulado
    primeira_questao = Questao.query.filter_by(simulado_id=simulado_id).order_by(Questao.numero).first()
    
    if not primeira_questao:
        flash('Este simulado não possui questões.', 'warning')
        return redirect(url_for('simulados.index'))
    
    return redirect(url_for('simulados.questao', simulado_id=simulado_id, questao_numero=primeira_questao.numero))

@simulados_bp.route('/<int:simulado_id>/questao/<int:questao_numero>', methods=['GET', 'POST'])
@login_required
def questao(simulado_id, questao_numero):
    simulado = Simulado.query.get_or_404(simulado_id)
    questao = Questao.query.filter_by(simulado_id=simulado_id, numero=questao_numero).first_or_404()
    
    # Verificar permissão
    if simulado.user_id != current_user.id:
        flash('Você não tem permissão para acessar este simulado.', 'danger')
        return redirect(url_for('simulados.index'))
    
    # Registrar o tempo quando o usuário acessa a questão (para cálculo de tempo)
    timestamp_acesso = int(datetime.utcnow().timestamp())
    
    # Processar resposta
    if request.method == 'POST':
        resposta = request.form.get('resposta')
        timestamp_resposta = request.form.get('timestamp', 0)
        
        if resposta in ['A', 'B', 'C', 'D', 'E']:
            # Salvar resposta
            questao.resposta_usuario = resposta
            
            # Calcular tempo de resposta
            if timestamp_resposta and timestamp_acesso:
                try:
                    tempo = int(timestamp_resposta) - timestamp_acesso
                    if tempo > 0:
                        questao.tempo_resposta = tempo
                except (ValueError, TypeError):
                    pass
                
            db.session.commit()
            
            # Verificar se há próxima questão
            proxima_questao = Questao.query.filter(
                Questao.simulado_id == simulado_id,
                Questao.numero > questao_numero
            ).order_by(Questao.numero).first()
            
            if proxima_questao:
                return redirect(url_for('simulados.questao', 
                                    simulado_id=simulado_id, 
                                    questao_numero=proxima_questao.numero))
            else:
                # Finalizar simulado
                return redirect(url_for('simulados.finalizar', simulado_id=simulado_id))
    
    # Obter todas as questões para a navegação
    todas_questoes = Questao.query.filter_by(simulado_id=simulado_id).order_by(Questao.numero).all()
    
    # Calcular progresso
    total_questoes = len(todas_questoes)
    progresso = (questao_numero / total_questoes) * 100
    
    return render_template('simulados/questao.html',
                          simulado=simulado,
                          questao=questao,
                          todas_questoes=todas_questoes,
                          progresso=progresso,
                          timestamp_acesso=timestamp_acesso)

@simulados_bp.route('/<int:simulado_id>/salvar-resposta', methods=['POST'])
@login_required
def salvar_resposta_ajax(simulado_id):
    """Endpoint para salvar resposta via AJAX sem redirecionar"""
    if not request.is_json:
        return jsonify({'success': False, 'error': 'Request must be JSON'}), 400
        
    data = request.get_json()
    questao_id = data.get('questao_id')
    resposta = data.get('resposta')
    tempo = data.get('tempo')
    
    # Validações
    if not questao_id or not resposta or resposta not in ['A', 'B', 'C', 'D', 'E']:
        return jsonify({'success': False, 'error': 'Invalid data'}), 400
    
    # Buscar questão
    questao = Questao.query.get(questao_id)
    if not questao or questao.simulado_id != simulado_id:
        return jsonify({'success': False, 'error': 'Question not found'}), 404
    
    # Verificar permissão
    simulado = Simulado.query.get(simulado_id)
    if simulado.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    
    # Salvar resposta
    questao.resposta_usuario = resposta
    if tempo and isinstance(tempo, int) and tempo > 0:
        questao.tempo_resposta = tempo
    
    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@simulados_bp.route('/<int:simulado_id>/finalizar')
@login_required
def finalizar(simulado_id):
    simulado = Simulado.query.get_or_404(simulado_id)
    
    # Verificar permissão
    if simulado.user_id != current_user.id:
        flash('Você não tem permissão para acessar este simulado.', 'danger')
        return redirect(url_for('simulados.index'))
    
    # Calcular tempo de realização
    if simulado.data_realizado:
        tempo_realizado = datetime.utcnow() - simulado.data_realizado
        horas = tempo_realizado.seconds // 3600
        minutos = (tempo_realizado.seconds % 3600) // 60
        simulado.tempo_realizado = f"{horas:02d}h{minutos:02d}"
    
    # Marcar como concluído
    simulado.status = 'Concluído'
    
    # Calcular nota TRI com o novo algoritmo mais sofisticado
    simulado.nota_tri = simulado.calcular_nota_tri()
    
    # Calcular estatísticas adicionais
    simulado.calcular_estatisticas()
    
    # Adicionar XP ao usuário com base na nota
    if simulado.nota_tri > 0:
        # Fórmula para calcular XP: 10% da nota TRI arredondado para múltiplo de 5
       
    # Fórmula para calcular XP: 10% da nota TRI arredondado para múltiplo de 5
        xp_ganho = round((simulado.nota_tri * 0.1) / 5) * 5
        resultado = XpService.conceder_xp(
           current_user, 
           int(xp_ganho), 
           'simulado', 
           f'Simulado finalizado - Nota: {simulado.nota_tri:.1f}'
        )

        if resultado:
           flash(f'Você ganhou {int(xp_ganho)} XP e {resultado["diamantes_ganhos"]} Launcher Coins !', 'success')
        else:
           flash(f'Você ganhou {int(xp_ganho)} XP por completar o simulado!', 'success')
 
    db.session.commit()
    
    flash('Simulado finalizado com sucesso!', 'success')
    return redirect(url_for('simulados.resultado', simulado_id=simulado_id))


#timer
@simulados_bp.route('/<int:simulado_id>/reset-timer', methods=['POST'])
@login_required
def reset_timer(simulado_id):
    """Reset timer para simulados com problema"""
    simulado = Simulado.query.get_or_404(simulado_id)
    
    if simulado.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    if simulado.status == 'Concluído':
        return jsonify({'success': False, 'error': 'Simulado já finalizado'}), 400
    
    # Reset timer
    simulado.data_realizado = datetime.now()
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Timer resetado'})



@simulados_bp.route('/<int:simulado_id>/resultado')
@login_required
def resultado(simulado_id):
    """Mostra resultado do simulado - COM EXPLICAÇÕES COMPLETAS"""
    simulado = Simulado.query.get_or_404(simulado_id)
    
    # Verificar permissão
    if simulado.user_id != current_user.id:
        flash('Você não tem permissão para acessar este simulado.', 'danger')
        return redirect(url_for('simulados.index'))
    
    # Verificar se simulado foi finalizado
    if simulado.status != 'Concluído':
        flash('Este simulado ainda não foi finalizado.', 'warning')
        return redirect(url_for('simulados.index'))
    
    # Obter todas as questões do simulado
    questoes = Questao.query.filter_by(simulado_id=simulado_id).order_by(Questao.numero).all()
    
    # Calcular estatísticas
    total_questoes = len(questoes)
    acertos = 0
    
    for questao in questoes:
        if questao.resposta_usuario == questao.resposta_correta:
            acertos += 1
    
    # Calcular percentual
    percentual = (acertos / total_questoes * 100) if total_questoes > 0 else 0
    
    # ✅ BUSCAR EXPLICAÇÕES DIRETAMENTE DO BANCO questoes_base
    explicacoes = {}
    
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='34.63.141.69',
            user='postgres',
            password='22092021Dd$',
            database='plataforma'
        )
        
        cursor = conn.cursor()
        
        # Para cada questão do simulado, buscar explicação pelo texto
        for questao in questoes:
            # Buscar explicação usando o texto da questão
            cursor.execute("""
                SELECT explicacao, materia, topico
                FROM questoes_base 
                WHERE ativa = true 
                AND texto = %s
                LIMIT 1
            """, (questao.texto,))
            
            resultado_busca = cursor.fetchone()
            
            if resultado_busca and resultado_busca[0]:
                explicacoes[questao.id] = {
                    'explicacao': resultado_busca[0],
                    'materia': resultado_busca[1], 
                    'topico': resultado_busca[2]
                }
        
        cursor.close()
        conn.close()
        
        print(f"✅ {len(explicacoes)} explicações carregadas do banco")
        
    except Exception as e:
        print(f"⚠️ Erro ao buscar explicações: {e}")
        # Continuar sem explicações se houver erro
        pass
    
    # Renderizar template com todas as variáveis necessárias
    return render_template('simulados/resultado.html',
                         simulado=simulado,
                         questoes=questoes,
                         total_questoes=total_questoes,
                         acertos=acertos,
                         percentual=percentual,
                         explicacoes=explicacoes)




# ==================== NOVAS ROTAS PARA MATÉRIAS INDIVIDUAIS ====================
# Adicionar estas rotas ao arquivo app/routes/simulados.py existente


# ✨ ROTA 1: Seleção de Modo (ENEM vs Individual)
@simulados_bp.route('/selecionar-modo')
@login_required
def selecionar_modo():
    """Tela para escolher entre Modalidades ENEM ou Matérias Individuais"""
    return render_template('simulados/selecionar_modo.html')


# ✨ ROTA 2: Seleção de Matéria Individual
@simulados_bp.route('/selecionar-materia')
@login_required
def selecionar_materia():
    """Mostra lista de matérias individuais disponíveis"""
    
    gerador = GeradorQuestoes()
    
    # Buscar disponibilidade de cada matéria
    disponibilidade = gerador.obter_questoes_disponiveis()
    
    # Mapeamento de ícones e áreas por matéria
    materias_config = {
        # Linguagens
        'Português': {'icone': 'bi-chat-text', 'area': 'Linguagens'},
        'Literatura': {'icone': 'bi-book', 'area': 'Linguagens'},
        'Inglês': {'icone': 'bi-translate', 'area': 'Linguagens'},
        'Espanhol': {'icone': 'bi-globe', 'area': 'Linguagens'},
        'Artes': {'icone': 'bi-palette', 'area': 'Linguagens'},
        
        # Matemática
        'Matemática': {'icone': 'bi-calculator', 'area': 'Matemática'},
        
        # Humanas
        'História': {'icone': 'bi-clock-history', 'area': 'Humanas'},
        'Geografia': {'icone': 'bi-globe-americas', 'area': 'Humanas'},
        'Filosofia': {'icone': 'bi-lightbulb', 'area': 'Humanas'},
        'Sociologia': {'icone': 'bi-people', 'area': 'Humanas'},
        
        # Natureza
        'Física': {'icone': 'bi-lightning', 'area': 'Natureza'},
        'Química': {'icone': 'bi-flask', 'area': 'Natureza'},
        'Biologia': {'icone': 'bi-heart-pulse', 'area': 'Natureza'}
    }
    
    # Construir lista de matérias com estatísticas
    materias_disponiveis = []
    
    for materia in GeradorQuestoes.MATERIAS_INDIVIDUAIS:
        if materia in disponibilidade and disponibilidade[materia] > 0:
            # Buscar estatísticas da matéria
            stats = gerador.obter_estatisticas_materia(materia)
            
            config = materias_config.get(materia, {
                'icone': 'bi-book',
                'area': 'Geral'
            })
            
            materias_disponiveis.append({
                'nome': materia,
                'icone': config['icone'],
                'area': config['area'],
                'total_questoes': stats['total_questoes'],
                'topicos_count': stats['topicos_disponiveis']
            })
    
    # Ordenar por área e depois por nome
    materias_disponiveis.sort(key=lambda x: (x['area'], x['nome']))
    
    return render_template('simulados/selecionar_materia.html',
                         materias_disponiveis=materias_disponiveis)


# ✨ ROTA 3: Seleção de Tópico dentro da Matéria
@simulados_bp.route('/selecionar-topico/<materia>')
@login_required
def selecionar_topico(materia):
    """Mostra tópicos disponíveis para uma matéria específica"""
    
    # Buscar tópicos da matéria
    topicos = obter_topicos_disponiveis(materia)
    
    if not topicos:
        flash(f'Nenhum tópico encontrado para {materia}.', 'warning')
        return redirect(url_for('simulados.selecionar_materia'))
    
    return render_template('simulados/selecionar_topico.html',
                         materia=materia,
                         topicos=topicos)


# ✨ ROTA 4: Gerar Simulado por Matéria + Tópico
@simulados_bp.route('/gerar-individual')
@login_required
@requer_simulado_disponivel
def gerar_individual():
    """Gera simulado baseado em matéria + tópico específicos"""
    
    # Obter parâmetros
    materia = request.args.get('materia')
    topico = request.args.get('topico')
    quantidade = request.args.get('quantidade', 10, type=int)
    
    # Validar parâmetros
    if not materia or not topico:
        flash('Parâmetros inválidos para geração do simulado.', 'danger')
        return redirect(url_for('simulados.selecionar_modo'))
    
    # Validar quantidade
    if quantidade < 5 or quantidade > 50:
        flash('A quantidade de questões deve estar entre 5 e 50.', 'warning')
        return redirect(url_for('simulados.selecionar_topico', materia=materia))
    
    try:
        # Gerar questões usando o novo método
        questoes_geradas = gerar_questoes_materia_topico(materia, topico, quantidade)
        
        if not questoes_geradas:
            flash(f'Não foi possível gerar questões para {materia} - {topico}.', 'danger')
            return redirect(url_for('simulados.selecionar_topico', materia=materia))
        
        # ✅ BUSCAR PRÓXIMO NÚMERO
        ultimo_simulado = Simulado.query.filter_by(user_id=current_user.id).order_by(Simulado.id.desc()).first()
        if ultimo_simulado and ultimo_simulado.numero is not None:
            proximo_numero = ultimo_simulado.numero + 1
        else:
            total_simulados = Simulado.query.filter_by(user_id=current_user.id).count()
            proximo_numero = total_simulados + 1
        
        # Criar simulado no banco
        simulado = Simulado(
            user_id=current_user.id,
            numero=proximo_numero,  # ✅ ADICIONADO
            titulo=f"{materia} - {topico}",
            tipo='individual',
            areas=materia,
            duracao_minutos=quantidade * 2,
            status='Pendente',
            data_criacao=datetime.utcnow()
        )
        
        db.session.add(simulado)
        db.session.flush()
        
        # Adicionar questões ao simulado
        for i, questao_data in enumerate(questoes_geradas, start=1):
            questao = Questao(
                simulado_id=simulado.id,
                numero=i,
                texto=questao_data['texto'],
                area=questao_data['materia'],
                dificuldade=questao_data['dificuldade'],
                resposta_correta=questao_data['resposta_correta']
            )
            
            db.session.add(questao)
            db.session.flush()
            
            # Adicionar alternativas
            alternativas_letras = ['A', 'B', 'C', 'D', 'E']
            for letra in alternativas_letras:
                alternativa = Alternativa(
                    questao_id=questao.id,
                    letra=letra,
                    texto=questao_data[f'opcao_{letra.lower()}']
                )
                db.session.add(alternativa)
        
        db.session.commit()
        
        flash(f'Simulado de {materia} - {topico} criado com sucesso!', 'success')
        return redirect(url_for('simulados.iniciar_simulado', simulado_id=simulado.id))
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Erro ao criar simulado individual: {e}')
        flash('Erro ao criar simulado. Tente novamente.', 'danger')
        return redirect(url_for('simulados.selecionar_topico', materia=materia))
