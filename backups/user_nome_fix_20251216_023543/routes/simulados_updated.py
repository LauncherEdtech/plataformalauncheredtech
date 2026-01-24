# app/routes/simulados_updated.py
"""
Atualização das rotas de simulados para integrar com o gerador de questões
SUBSTITUI o arquivo app/routes/simulados.py existente
VERSÃO CORRIGIDA - Resolve bug do desempenho por área
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app.models.simulado import Simulado, Questao, Alternativa
from app.models.user import User
from app import db
from datetime import datetime, timedelta
from flask import current_app
import json

# NOVA IMPORTAÇÃO - Integrador com banco de questões
from app.services.gerador_questoes import gerar_questoes_simulado

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
    
    # ✅ CORREÇÃO: Mapear áreas reais para áreas de exibição
    # Mapear disciplinas reais (que vêm do banco) para áreas do ENEM
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
    
    print(f"DEBUG: Encontradas {len(todas_questoes)} questões")
    for q in todas_questoes[:3]:
        print(f"DEBUG: Questão área='{q.area}' mapeada='{mapeamento_areas.get(q.area, q.area)}'")
    
    # Processar cada questão e mapear para a área correta
    for questao in todas_questoes:
        # Mapear a disciplina real para área de exibição
        area_display = mapeamento_areas.get(questao.area, questao.area)
        
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
    
    return render_template('simulados/index.html',
                          simulados_pendentes=simulados_pendentes,
                          simulados_concluidos=simulados_concluidos,
                          datas_grafico=datas_grafico,
                          notas_grafico=notas_grafico,
                          desempenho_areas=desempenho_areas)

@simulados_bp.route('/<int:simulado_id>')
@login_required
def iniciar_simulado(simulado_id):
    simulado = Simulado.query.get_or_404(simulado_id)
    
    # Verificar se o simulado pertence ao usuário
    if simulado.user_id != current_user.id:
        flash('Você não tem permissão para acessar este simulado.', 'danger')
        return redirect(url_for('simulados.index'))
    
    # Verificar se o simulado já foi realizado
    if simulado.status == 'Concluído':
        return redirect(url_for('simulados.resultado', simulado_id=simulado_id))
    
    # *** NOVA FUNCIONALIDADE ***
    # Verificar se o simulado tem questões, se não tiver, gerar automaticamente
    if simulado.questoes.count() == 0:
        print(f"🎯 Simulado {simulado_id} sem questões, gerando automaticamente...")
        
        sucesso = gerar_questoes_simulado(simulado_id)
        
        if not sucesso:
            flash('Não foi possível gerar as questões para este simulado. Tente novamente.', 'error')
            return redirect(url_for('simulados.index'))
        
        # Recarregar simulado para obter as questões
        db.session.refresh(simulado)
        
        flash(f'Simulado preparado com {simulado.questoes.count()} questões baseado em suas configurações!', 'success')
    
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
            
            # *** NOVA FUNCIONALIDADE ***
            # Atualizar estatísticas da questão base
            if questao.questao_base_id:
                from app.models.questao import QuestaoBase
                questao_base = QuestaoBase.query.get(questao.questao_base_id)
                if questao_base:
                    acertou = questao.verificar_resposta()
                    questao_base.incrementar_uso(acertou)
                
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
    
    # Validações melhoradas
    if not questao_id or not resposta or resposta not in ['A', 'B', 'C', 'D', 'E']:
        return jsonify({'success': False, 'error': 'Invalid data'}), 400
    
    # Validação de tempo (deve ser entre 1 segundo e 30 minutos)
    if tempo and (not isinstance(tempo, int) or tempo < 1 or tempo > 1800):
        return jsonify({'success': False, 'error': 'Invalid time'}), 400
    
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
    
    # *** NOVA FUNCIONALIDADE ***
    # Atualizar estatísticas da questão base
    if questao.questao_base_id:
        from app.models.questao import QuestaoBase
        questao_base = QuestaoBase.query.get(questao.questao_base_id)
        if questao_base:
            acertou = questao.verificar_resposta()
            questao_base.incrementar_uso(acertou)
    
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
        xp_ganho = round((simulado.nota_tri * 0.1) / 5) * 5
        current_user.xp_total += int(xp_ganho)
        
        flash(f'Você ganhou {int(xp_ganho)} XP por completar o simulado!', 'success')
    
    db.session.commit()
    
    flash('Simulado finalizado com sucesso!', 'success')
    return redirect(url_for('simulados.resultado', simulado_id=simulado_id))

@simulados_bp.route('/<int:simulado_id>/resultado')
@login_required
def resultado(simulado_id):
    simulado = Simulado.query.get_or_404(simulado_id)
    
    # Verificar permissão
    if simulado.user_id != current_user.id:
        flash('Você não tem permissão para acessar este simulado.', 'danger')
        return redirect(url_for('simulados.index'))
    
    # Verificar se o simulado foi concluído
    if simulado.status != 'Concluído':
        flash('Este simulado ainda não foi concluído.', 'warning')
        return redirect(url_for('simulados.index'))
    
    # ✅ CORREÇÃO: Usar mesmo mapeamento da página inicial
    areas = {}
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
    
    for questao in simulado.questoes:
        area_real = questao.area
        area_display = mapeamento_areas.get(area_real, area_real)
        
        if area_display not in areas:
            areas[area_display] = {'total': 0, 'acertos': 0}
        
        areas[area_display]['total'] += 1
        if questao.verificar_resposta():
            areas[area_display]['acertos'] += 1
    
    # Calcular percentuais
    for area in areas:
        if areas[area]['total'] > 0:
            areas[area]['percentual'] = (areas[area]['acertos'] / areas[area]['total']) * 100
        else:
            areas[area]['percentual'] = 0
    
    # Gerar dados para gráfico de tempo por questão
    tempos_questoes = []
    numeros_questoes = []
    
    for questao in simulado.questoes.order_by(Questao.numero):
        if questao.tempo_resposta:
            numeros_questoes.append(questao.numero)
            # Converter segundos para minutos para o gráfico
            tempos_questoes.append(round(questao.tempo_resposta / 60, 1))
    
    # Obter histórico de notas para comparação
    historico_notas = Simulado.query.filter(
        Simulado.user_id == current_user.id,
        Simulado.status == 'Concluído',
        Simulado.id != simulado_id
    ).order_by(Simulado.data_realizado.desc()).limit(3).all()
    
    # Calcular média do usuário para comparação
    media_usuario = db.session.query(db.func.avg(Simulado.nota_tri)).filter(
        Simulado.user_id == current_user.id,
        Simulado.status == 'Concluído'
    ).scalar() or 0
    
    # Obter pontos fortes e fracos
    pontos_fortes = []
    pontos_fracos = []
    
    # Ordenar áreas por desempenho
    areas_ordenadas = sorted(areas.items(), key=lambda x: x[1]['percentual'], reverse=True)
    
    # Top 2 áreas como pontos fortes
    for area, dados in areas_ordenadas[:2]:
        if dados['percentual'] >= 50:  # Só considerar como forte se >= 50%
            pontos_fortes.append(f"{area}: {dados['percentual']:.1f}%")
    
    # Bottom 2 áreas como pontos fracos
    for area, dados in reversed(areas_ordenadas[-2:]):
        if dados['percentual'] < 70:  # Só considerar como fraco se < 70%
            pontos_fracos.append(f"{area}: {dados['percentual']:.1f}%")
    
    return render_template('simulados/resultado.html',
                          simulado=simulado,
                          areas=areas,
                          tempos_questoes=json.dumps(tempos_questoes),
                          numeros_questoes=json.dumps(numeros_questoes),
                          historico_notas=historico_notas,
                          media_usuario=media_usuario,
                          pontos_fortes=pontos_fortes,
                          pontos_fracos=pontos_fracos)

# *** NOVA FUNCIONALIDADE ***
@simulados_bp.route('/<int:simulado_id>/regenerar-questoes')
@login_required
def regenerar_questoes(simulado_id):
    """Permite regenerar questões de um simulado pendente"""
    simulado = Simulado.query.get_or_404(simulado_id)
    
    # Verificar permissão
    if simulado.user_id != current_user.id:
        flash('Você não tem permissão para acessar este simulado.', 'danger')
        return redirect(url_for('simulados.index'))
    
    # Só permitir regenerar se estiver pendente
    if simulado.status != 'Pendente':
        flash('Só é possível regenerar questões de simulados pendentes.', 'warning')
        return redirect(url_for('simulados.index'))
    
    # Limpar questões existentes
    try:
        Questao.query.filter_by(simulado_id=simulado_id).delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash('Erro ao limpar questões anteriores.', 'error')
        return redirect(url_for('simulados.index'))
    
    # Gerar novas questões
    sucesso = gerar_questoes_simulado(simulado_id)
    
    if sucesso:
        db.session.refresh(simulado)
        flash(f'Questões regeneradas! Simulado agora tem {simulado.questoes.count()} questões.', 'success')
    else:
        flash('Erro ao regenerar questões. Tente novamente.', 'error')
    
    return redirect(url_for('simulados.index'))

# *** NOVA FUNCIONALIDADE ***
@simulados_bp.route('/estatisticas-questoes')
@login_required
def estatisticas_questoes():
    """Página com estatísticas das questões do banco"""
    from app.models.questao import QuestaoBase
    from sqlalchemy import func
    
    try:
        # Estatísticas gerais
        total_questoes = QuestaoBase.query.filter_by(ativa=True).count()
        
        # Por matéria
        por_materia = db.session.query(
            QuestaoBase.materia,
            func.count(QuestaoBase.id).label('total')
        ).filter(
            QuestaoBase.ativa == True
        ).group_by(QuestaoBase.materia).all()
        
        # Top questões mais usadas
        mais_usadas = QuestaoBase.query.filter(
            QuestaoBase.ativa == True,
            QuestaoBase.vezes_utilizada > 0
        ).order_by(QuestaoBase.vezes_utilizada.desc()).limit(10).all()
        
        # Questões com menor taxa de acerto
        menor_acerto = QuestaoBase.query.filter(
            QuestaoBase.ativa == True,
            QuestaoBase.vezes_utilizada >= 5
        ).all()
        
        # Calcular percentual e ordenar
        menor_acerto = sorted(
            [(q, q.percentual_acerto) for q in menor_acerto],
            key=lambda x: x[1]
        )[:10]
        
        return render_template('simulados/estatisticas_questoes.html',
                              total_questoes=total_questoes,
                              por_materia=por_materia,
                              mais_usadas=mais_usadas,
                              menor_acerto=menor_acerto)
    except Exception as e:
        flash(f'Erro ao carregar estatísticas: {str(e)}', 'error')
        return redirect(url_for('simulados.index'))
