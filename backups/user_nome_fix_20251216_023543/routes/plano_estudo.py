from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app.models.simulado import Simulado, Questao
from app.models.user import User
from app import db
from datetime import datetime, timedelta
import json
import random

# Criar o blueprint
plano_estudo_bp = Blueprint('plano_estudo', __name__, url_prefix='/plano-estudo')

@plano_estudo_bp.route('/')
@login_required
def index():
    """
    Rota temporária - versão básica do plano de estudos
    """
    # Verificar se existem simulados concluídos
    simulados_concluidos = Simulado.query.filter_by(
        user_id=current_user.id,
        status='Concluído'
    ).count()
    
    if simulados_concluidos == 0:
        # Se não existem simulados, exibir mensagem informativa
        return render_template('plano_estudo/sem_dados.html')
    
    # Obter estatísticas básicas por área
    areas_stats = {}
    
    # Buscar todas as questões respondidas agrupadas por área
    questoes = Questao.query.join(Simulado).filter(
        Simulado.user_id == current_user.id,
        Simulado.status == 'Concluído'
    ).all()
    
    # Agrupar por área
    for q in questoes:
        if q.area not in areas_stats:
            areas_stats[q.area] = {'total': 0, 'acertos': 0}
        
        areas_stats[q.area]['total'] += 1
        if q.verificar_resposta():
            areas_stats[q.area]['acertos'] += 1
    
    # Calcular percentuais
    for area in areas_stats:
        if areas_stats[area]['total'] > 0:
            areas_stats[area]['percentual'] = (areas_stats[area]['acertos'] / areas_stats[area]['total']) * 100
        else:
            areas_stats[area]['percentual'] = 0
    
    # Identificar áreas prioritárias (abaixo de 70%)
    areas_prioritarias = []
    for area, stats in areas_stats.items():
        if stats['percentual'] < 70:  # Priorizar áreas com menos de 70% de acerto
            areas_prioritarias.append({
                'area': area,
                'percentual': stats['percentual'],
                'prioridade': max(1, int(6 - (stats['percentual'] / 20)))  # Escala de 1 a 5
            })
    
    # Ordenar por prioridade (mais alta primeiro)
    areas_prioritarias.sort(key=lambda x: x['prioridade'], reverse=True)
    
    # Simular um plano de estudos básico
    plano_semanal = {
        'Segunda': [{'area': 'Matemática', 'horas': 2, 'conteudos': ['Funções', 'Geometria']}],
        'Terça': [{'area': 'Linguagens', 'horas': 2, 'conteudos': ['Interpretação', 'Gramática']}],
        'Quarta': [{'area': 'Ciências da Natureza', 'horas': 2, 'conteudos': ['Física Mecânica', 'Química Orgânica']}],
        'Quinta': [{'area': 'Ciências Humanas', 'horas': 2, 'conteudos': ['História do Brasil', 'Geografia']}],
        'Sexta': [{'area': 'Redação', 'horas': 2, 'conteudos': ['Estrutura Dissertativa', 'Repertório']}],
        'Sábado': [{'area': 'Revisão Geral', 'horas': 4, 'conteudos': ['Revisão Semanal', 'Exercícios']}],
        'Domingo': []  # Dia de descanso
    }
    
    return render_template('plano_estudo/index_temp.html',
                          areas_stats=areas_stats,
                          areas_prioritarias=areas_prioritarias,
                          plano_semanal=plano_semanal)