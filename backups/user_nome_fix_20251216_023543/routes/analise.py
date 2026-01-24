from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models.simulado import Simulado, Questao
from app.models.user import User
from app import db
from datetime import datetime, timedelta
import json
import random

analise_bp = Blueprint('analise', __name__, url_prefix='/analise')

@analise_bp.route('/')
@login_required
def index():
    # Obter estatísticas básicas do usuário
    simulados_concluidos = Simulado.query.filter_by(
        user_id=current_user.id,
        status='Concluído'
    ).count()
    
    # Calcular total de questões respondidas
    total_questoes = 0
    total_acertos = 0
    
    simulados = Simulado.query.filter_by(
        user_id=current_user.id,
        status='Concluído'
    ).all()
    
    for simulado in simulados:
        for questao in simulado.questoes:
            if questao.resposta_usuario:  # Se a questão foi respondida
                total_questoes += 1
                if questao.resposta_usuario == questao.resposta_correta:
                    total_acertos += 1
    
    # Calcular percentual de acertos
    percentual_acertos = (total_acertos / total_questoes) * 100 if total_questoes > 0 else 0
    
    # Obter histórico de notas TRI para o gráfico
    historico_simulados = Simulado.query.filter_by(
        user_id=current_user.id,
        status='Concluído'
    ).order_by(Simulado.data_realizado).all()
    
    datas = []
    notas = []
    
    for sim in historico_simulados:
        if sim.data_realizado and sim.nota_tri:
            datas.append(sim.data_realizado.strftime('%d/%m'))
            notas.append(sim.nota_tri)
    
    # Calcular médias por área
    areas = ['Linguagens', 'Matemática', 'Humanas', 'Natureza']
    desempenho_areas = {}
    
    for area in areas:
        acertos_area = 0
        total_area = 0
        
        for simulado in simulados:
            for questao in simulado.questoes:
                if questao.area == area and questao.resposta_usuario:
                    total_area += 1
                    if questao.resposta_usuario == questao.resposta_correta:
                        acertos_area += 1
        
        percentual_area = (acertos_area / total_area) * 100 if total_area > 0 else 0
        desempenho_areas[area] = {
            'percentual': percentual_area,
            'acertos': acertos_area,
            'total': total_area
        }
    
    return render_template('analise/index.html',
                          simulados_concluidos=simulados_concluidos,
                          total_questoes=total_questoes,
                          total_acertos=total_acertos,
                          percentual_acertos=percentual_acertos,
                          datas=datas,
                          notas=notas,
                          desempenho_areas=desempenho_areas)

@analise_bp.route('/simulados')
@login_required
def simulados():
    # Obter todos os simulados concluídos
    simulados = Simulado.query.filter_by(
        user_id=current_user.id,
        status='Concluído'
    ).order_by(Simulado.data_realizado.desc()).all()
    
    return render_template('analise/simulados.html',
                          simulados=simulados)

@analise_bp.route('/areas')
@login_required
def areas():
    # Obter estatísticas por área
    simulados = Simulado.query.filter_by(
        user_id=current_user.id,
        status='Concluído'
    ).all()
    
    areas = ['Linguagens', 'Matemática', 'Humanas', 'Natureza']
    estatisticas_areas = {}
    
    for area in areas:
        # Inicializar estatísticas por área
        estatisticas_areas[area] = {
            'acertos': 0,
            'total': 0,
            'faceis_acertos': 0,
            'faceis_total': 0,
            'medias_acertos': 0,
            'medias_total': 0,
            'dificeis_acertos': 0,
            'dificeis_total': 0,
            'historico_percentual': []
        }
        
        # Processar cada simulado para esta área
        for simulado in simulados:
            acertos_simulado = 0
            total_simulado = 0
            
            for questao in simulado.questoes:
                if questao.area == area and questao.resposta_usuario:
                    # Estatísticas gerais
                    estatisticas_areas[area]['total'] += 1
                    if questao.resposta_usuario == questao.resposta_correta:
                        estatisticas_areas[area]['acertos'] += 1
                        acertos_simulado += 1
                    
                    total_simulado += 1
                    
                    # Estatísticas por dificuldade
                    if questao.dificuldade < 0.4:  # Fácil
                        estatisticas_areas[area]['faceis_total'] += 1
                        if questao.resposta_usuario == questao.resposta_correta:
                            estatisticas_areas[area]['faceis_acertos'] += 1
                    elif questao.dificuldade < 0.7:  # Média
                        estatisticas_areas[area]['medias_total'] += 1
                        if questao.resposta_usuario == questao.resposta_correta:
                            estatisticas_areas[area]['medias_acertos'] += 1
                    else:  # Difícil
                        estatisticas_areas[area]['dificeis_total'] += 1
                        if questao.resposta_usuario == questao.resposta_correta:
                            estatisticas_areas[area]['dificeis_acertos'] += 1
            
            # Adicionar histórico percentual para este simulado
            if total_simulado > 0:
                percentual = (acertos_simulado / total_simulado) * 100
                data = simulado.data_realizado.strftime('%d/%m') if simulado.data_realizado else 'Sem data'
                estatisticas_areas[area]['historico_percentual'].append({
                    'data': data,
                    'percentual': percentual
                })
    
    # Calcular percentuais
    for area in areas:
        # Percentual geral
        if estatisticas_areas[area]['total'] > 0:
            estatisticas_areas[area]['percentual'] = (estatisticas_areas[area]['acertos'] / estatisticas_areas[area]['total']) * 100
        else:
            estatisticas_areas[area]['percentual'] = 0
        
        # Percentual por dificuldade
        if estatisticas_areas[area]['faceis_total'] > 0:
            estatisticas_areas[area]['faceis_percentual'] = (estatisticas_areas[area]['faceis_acertos'] / estatisticas_areas[area]['faceis_total']) * 100
        else:
            estatisticas_areas[area]['faceis_percentual'] = 0
            
        if estatisticas_areas[area]['medias_total'] > 0:
            estatisticas_areas[area]['medias_percentual'] = (estatisticas_areas[area]['medias_acertos'] / estatisticas_areas[area]['medias_total']) * 100
        else:
            estatisticas_areas[area]['medias_percentual'] = 0
            
        if estatisticas_areas[area]['dificeis_total'] > 0:
            estatisticas_areas[area]['dificeis_percentual'] = (estatisticas_areas[area]['dificeis_acertos'] / estatisticas_areas[area]['dificeis_total']) * 100
        else:
            estatisticas_areas[area]['dificeis_percentual'] = 0
    
    return render_template('analise/areas.html',
                          areas=areas,
                          estatisticas_areas=estatisticas_areas)

@analise_bp.route('/desempenho-detalhado/<int:simulado_id>')
@login_required
def desempenho_detalhado(simulado_id):
    # Obter o simulado específico
    simulado = Simulado.query.get_or_404(simulado_id)
    
    # Verificar permissão
    if simulado.user_id != current_user.id:
        flash('Você não tem permissão para acessar este recurso.', 'danger')
        return redirect(url_for('analise.index'))
    
    # Verificar se o simulado foi concluído
    if simulado.status != 'Concluído':
        flash('Este simulado ainda não foi concluído.', 'warning')
        return redirect(url_for('analise.simulados'))
    
    # Obter estatísticas por área
    areas = {}
    for questao in simulado.questoes:
        area = questao.area
        if area not in areas:
            areas[area] = {
                'total': 0,
                'acertos': 0,
                'notas': []
            }
        
        areas[area]['total'] += 1
        if questao.resposta_usuario == questao.resposta_correta:
            areas[area]['acertos'] += 1
            areas[area]['notas'].append(1.0)  # Acerto completo
        elif not questao.resposta_usuario:
            areas[area]['notas'].append(0.0)  # Em branco
        else:
            areas[area]['notas'].append(0.0)  # Erro
    
    # Calcular percentuais
    for area in areas:
        if areas[area]['total'] > 0:
            areas[area]['percentual'] = (areas[area]['acertos'] / areas[area]['total']) * 100
        else:
            areas[area]['percentual'] = 0
    
    # Obter estatísticas por dificuldade
    dificuldades = {
        'Fácil': {'total': 0, 'acertos': 0, 'notas': []},
        'Média': {'total': 0, 'acertos': 0, 'notas': []},
        'Difícil': {'total': 0, 'acertos': 0, 'notas': []},
    }
    
    for questao in simulado.questoes:
        # Determinar categoria de dificuldade
        if questao.dificuldade < 0.4:
            categoria = 'Fácil'
        elif questao.dificuldade < 0.7:
            categoria = 'Média'
        else:
            categoria = 'Difícil'
        
        dificuldades[categoria]['total'] += 1
        if questao.resposta_usuario == questao.resposta_correta:
            dificuldades[categoria]['acertos'] += 1
            dificuldades[categoria]['notas'].append(1.0)  # Acerto completo
        elif not questao.resposta_usuario:
            dificuldades[categoria]['notas'].append(0.0)  # Em branco
        else:
            dificuldades[categoria]['notas'].append(0.0)  # Erro
    
    # Calcular percentuais por dificuldade
    for dif in dificuldades:
        if dificuldades[dif]['total'] > 0:
            dificuldades[dif]['percentual'] = (dificuldades[dif]['acertos'] / dificuldades[dif]['total']) * 100
        else:
            dificuldades[dif]['percentual'] = 0
    
    # Obter lista de questões com detalhes
    questoes_detalhes = []
    for i, questao in enumerate(simulado.questoes):
        # Determinar categoria de dificuldade
        if questao.dificuldade < 0.4:
            dificuldade = 'Fácil'
        elif questao.dificuldade < 0.7:
            dificuldade = 'Média'
        else:
            dificuldade = 'Difícil'
        
        acertou = questao.resposta_usuario == questao.resposta_correta
        
        questoes_detalhes.append({
            'numero': questao.numero,
            'area': questao.area,
            'dificuldade': dificuldade,
            'resposta_usuario': questao.resposta_usuario,
            'resposta_correta': questao.resposta_correta,
            'acertou': acertou
        })
    
    # Estatísticas gerais
    total_questoes = len(simulado.questoes.all())
    total_acertos = sum(1 for q in simulado.questoes if q.resposta_usuario == q.resposta_correta)
    total_percentual = (total_acertos / total_questoes) * 100 if total_questoes > 0 else 0
    
    # Tempo de realização formatado
    tempo_minutos = 0
    if simulado.tempo_realizado:
        partes = simulado.tempo_realizado.split('h')
        if len(partes) == 2:
            tempo_minutos = int(partes[0]) * 60 + int(partes[1])
    
    # Notas (para média)
    notas = []
    for questao in simulado.questoes:
        if questao.resposta_usuario == questao.resposta_correta:
            notas.append(1.0)
        else:
            notas.append(0.0)
    
    return render_template('analise/desempenho_detalhado.html',
                          simulado=simulado,
                          areas=areas,
                          dificuldades=dificuldades,
                          questoes_detalhes=questoes_detalhes,
                          total_questoes=total_questoes,
                          total_acertos=total_acertos,
                          total_percentual=total_percentual,
                          tempo_minutos=tempo_minutos,
                          notas=notas)  # Adicionamos a lista de notas para calcular a média