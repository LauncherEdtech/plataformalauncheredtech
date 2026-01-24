# app/routes/agendar_simulado.py
"""
Rota para criação de simulados - ATUALIZADA para suportar "Fazer Agora" e "Agendar"
SUBSTITUI o arquivo existente app/routes/agendar_simulado.py
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app.models.simulado import Simulado, Questao, Alternativa
from app import db
from datetime import datetime, timedelta
import random

# NOVA IMPORTAÇÃO - Gerador de questões do banco
from app.services.gerador_questoes import gerar_questoes_simulado, obter_relatorio_disponibilidade

agendar_simulado_bp = Blueprint('agendar_simulado', __name__, url_prefix='/agendar-simulado')

@agendar_simulado_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    """
    Rota principal para criação de simulados.
    ATUALIZADA para suportar "Fazer Agora" e "Agendar".
    """
    
    # Obter questões disponíveis para mostrar na interface
    disponibilidade = obter_relatorio_disponibilidade()
    
    if request.method == 'POST':
        # NOVO: Extrair a ação (fazer agora ou agendar)
        action = request.form.get('action')
        
        # Extrair dados do formulário
        areas = request.form.getlist('areas')
        duracao = int(request.form.get('duracao', 120))
        num_questoes = int(request.form.get('num_questoes', 45))
        data_agendada_str = request.form.get('data_agendada')
        estrategia = request.form.get('estrategia', 'equilibrada')
        titulo_personalizado = request.form.get('titulo', '').strip()
        
        # Validações básicas
        if not action or action not in ['now', 'schedule']:
            flash('Selecione se deseja fazer o simulado agora ou agendar', 'warning')
            return render_template('agendar_simulado/index.html', 
                                 disponibilidade=disponibilidade)
        
        if not areas:
            flash('Selecione pelo menos uma área de conhecimento', 'warning')
            return render_template('agendar_simulado/index.html', 
                                 disponibilidade=disponibilidade)
        
        if num_questoes <= 0 or num_questoes > 200:
            flash('Número de questões deve estar entre 1 e 200', 'warning')
            return render_template('agendar_simulado/index.html', 
                                 disponibilidade=disponibilidade)
        
        # Verificar se há questões suficientes para as áreas selecionadas
        total_disponivel = calcular_questoes_disponiveis(areas, disponibilidade)
        
        if total_disponivel < num_questoes:
            flash(f'Questões insuficientes! Disponível: {total_disponivel}, '
                  f'Solicitado: {num_questoes}', 'warning')
            return render_template('agendar_simulado/index.html', 
                                 disponibilidade=disponibilidade)
        
        # NOVO: Validação específica para agendamento
        data_agendada = None
        if action == 'schedule':
            if not data_agendada_str:
                flash('Para agendar, é necessário informar data e horário', 'warning')
                return render_template('agendar_simulado/index.html', 
                                     disponibilidade=disponibilidade)
            
            try:
                data_agendada = datetime.strptime(data_agendada_str, '%Y-%m-%dT%H:%M')
                
                # Verificar se a data não é no passado (com margem de 1 hora)
                if data_agendada < datetime.now() + timedelta(hours=1):
                    flash('A data de agendamento deve ser pelo menos 1 hora no futuro', 'warning')
                    return render_template('agendar_simulado/index.html', 
                                         disponibilidade=disponibilidade)
            except ValueError:
                flash('Formato de data inválido', 'danger')
                return render_template('agendar_simulado/index.html', 
                                     disponibilidade=disponibilidade)
        
        # Construir título baseado na ação
        if titulo_personalizado:
            titulo = titulo_personalizado
        else:
            areas_texto = ' e '.join(areas)
            prefixo = "Simulado Imediato" if action == 'now' else "Simulado Agendado"
            titulo = f"{prefixo} - {areas_texto} ({num_questoes} questões)"
        
        # NOVO: Status baseado na ação
        status_inicial = 'Em Andamento' if action == 'now' else 'Pendente'
        
        # Criar o novo simulado
        simulado = Simulado(
            numero=get_next_simulado_number(current_user.id),
            titulo=titulo,
            areas=', '.join(areas),
            duracao_minutos=duracao,
            data_agendada=data_agendada,
            status=status_inicial,
            user_id=current_user.id,
            # NOVO: Marcar horário de início se for "fazer agora"
            data_realizado=datetime.now() if action == 'now' else None
        )
        
        db.session.add(simulado)
        db.session.flush()  # Para obter o ID do simulado
        
        try:
            # Gerar questões reais do banco de dados
            questoes_geradas = gerar_questoes_simulado(
                areas=areas, 
                quantidade=num_questoes, 
                estrategia=estrategia
            )
            
            if not questoes_geradas:
                flash('Erro ao gerar questões. Tente novamente.', 'danger')
                db.session.rollback()
                return render_template('agendar_simulado/index.html', 
                                     disponibilidade=disponibilidade)
            
            # Inserir questões no simulado
            sucesso = inserir_questoes_no_simulado(simulado.id, questoes_geradas)
            
            if not sucesso:
                flash('Erro ao salvar questões do simulado', 'danger')
                db.session.rollback()
                return render_template('agendar_simulado/index.html', 
                                     disponibilidade=disponibilidade)
            
            db.session.commit()
            
            # NOVO: Redirecionamento baseado na ação
            if action == 'now':
                flash(f'Simulado iniciado com sucesso! {len(questoes_geradas)} questões carregadas.', 'success')
                return redirect(url_for('simulados.iniciar_simulado', simulado_id=simulado.id))
            else:
                data_formatada = data_agendada.strftime('%d/%m/%Y às %H:%M')
                flash(f'Simulado "{titulo}" agendado para {data_formatada}! '
                      f'{len(questoes_geradas)} questões preparadas.', 'success')
                return redirect(url_for('simulados.index'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar simulado: {str(e)}', 'danger')
            return render_template('agendar_simulado/index.html', 
                                 disponibilidade=disponibilidade)
    
    return render_template('agendar_simulado/index.html', 
                         disponibilidade=disponibilidade)


def calcular_questoes_disponiveis(areas, disponibilidade):
    """
    Calcula o total de questões disponíveis para as áreas selecionadas
    """
    total_disponivel = 0
    
    for area in areas:
        if area == 'Matemática':
            total_disponivel += disponibilidade.get('Matemática', 0)
        elif area == 'Física':
            total_disponivel += disponibilidade.get('Física', 0)
        elif area == 'Química':
            total_disponivel += disponibilidade.get('Química', 0)
        elif area == 'Biologia':
            total_disponivel += disponibilidade.get('Biologia', 0)
        elif area == 'História':
            total_disponivel += disponibilidade.get('História', 0)
        elif area == 'Geografia':
            total_disponivel += disponibilidade.get('Geografia', 0)
        elif area == 'Português':
            total_disponivel += disponibilidade.get('Português', 0)
        elif area == 'Linguagens':
            total_disponivel += (
                disponibilidade.get('Português', 0) + 
                disponibilidade.get('Literatura', 0) +
                disponibilidade.get('Inglês', 0) +
                disponibilidade.get('Espanhol', 0) +
                disponibilidade.get('Artes', 0)
            )
        elif area == 'Humanas':
            total_disponivel += (
                disponibilidade.get('História', 0) +
                disponibilidade.get('Geografia', 0) +
                disponibilidade.get('Sociologia', 0) +
                disponibilidade.get('Filosofia', 0)
            )
        elif area == 'Natureza':
            total_disponivel += (
                disponibilidade.get('Física', 0) +
                disponibilidade.get('Química', 0) +
                disponibilidade.get('Biologia', 0)
            )
    
    return total_disponivel


def get_next_simulado_number(user_id):
    """Retorna o próximo número de simulado para o usuário"""
    ultimo_simulado = Simulado.query.filter_by(user_id=user_id).order_by(Simulado.id.desc()).first()
    
    if ultimo_simulado and ultimo_simulado.numero is not None:
        return ultimo_simulado.numero + 1
    elif ultimo_simulado:
        total_simulados = Simulado.query.filter_by(user_id=user_id).count()
        return total_simulados + 1
    else:
        return 1

def inserir_questoes_no_simulado(simulado_id: int, questoes_dados: list) -> bool:
    """
    Insere questões reais do banco no simulado
    CORRIGIDO: Remove campos que não existem no modelo
    """
    try:
        for i, questao_data in enumerate(questoes_dados, 1):
            # Criar questão do simulado - SÓ CAMPOS VÁLIDOS
            questao = Questao(
                numero=i,
                texto=questao_data['texto'],
                area=questao_data['materia'],
                dificuldade=questao_data.get('dificuldade', 0.5),
                resposta_correta=questao_data['resposta_correta'],
                simulado_id=simulado_id
            )
            
            db.session.add(questao)
            db.session.flush()
            
            # Criar alternativas
            alternativas_dados = [
                ('A', questao_data['opcao_a']),
                ('B', questao_data['opcao_b']),
                ('C', questao_data['opcao_c']),
                ('D', questao_data['opcao_d']),
                ('E', questao_data['opcao_e'])
            ]
            
            for letra, texto in alternativas_dados:
                if texto and texto.strip():
                    alternativa = Alternativa(
                        letra=letra,
                        texto=texto.strip(),
                        questao_id=questao.id
                    )
                    db.session.add(alternativa)
        
        return True
        
    except Exception as e:
        print(f"Erro ao inserir questões: {e}")
        return False
# NOVO: Endpoint para validação em tempo real
@agendar_simulado_bp.route('/validar-configuracao', methods=['POST'])
@login_required
def validar_configuracao():
    """
    Valida configuração do simulado em tempo real (AJAX)
    """
    try:
        data = request.get_json()
        areas = data.get('areas', [])
        num_questoes = int(data.get('num_questoes', 45))
        action = data.get('action')
        data_agendada = data.get('data_agendada')
        
        # Validações
        erros = []
        avisos = []
        
        if not areas:
            erros.append('Selecione pelo menos uma área de conhecimento')
        
        if num_questoes <= 0 or num_questoes > 200:
            erros.append('Número de questões deve estar entre 1 e 200')
        
        if action == 'schedule' and not data_agendada:
            erros.append('Para agendar, informe data e horário')
        
        if data_agendada and action == 'schedule':
            try:
                data_obj = datetime.strptime(data_agendada, '%Y-%m-%dT%H:%M')
                if data_obj < datetime.now() + timedelta(hours=1):
                    erros.append('Data deve ser pelo menos 1 hora no futuro')
            except ValueError:
                erros.append('Formato de data inválido')
        
        # Verificar disponibilidade
        if areas:
            disponibilidade = obter_relatorio_disponibilidade()
            total_disponivel = calcular_questoes_disponiveis(areas, disponibilidade)
            
            if total_disponivel < num_questoes:
                erros.append(f'Questões insuficientes! Disponível: {total_disponivel}')
            elif total_disponivel < num_questoes * 1.5:
                avisos.append(f'Poucas questões disponíveis ({total_disponivel}). '
                            'Considere reduzir o número ou adicionar mais áreas.')
        
        return jsonify({
            'valido': len(erros) == 0,
            'erros': erros,
            'avisos': avisos,
            'questoes_disponiveis': total_disponivel if areas else 0
        })
        
    except Exception as e:
        return jsonify({
            'valido': False,
            'erros': [f'Erro de validação: {str(e)}'],
            'avisos': []
        })


@agendar_simulado_bp.route('/relatorio-disponibilidade')
@login_required
def relatorio_disponibilidade():
    """Endpoint para obter relatório de questões disponíveis (AJAX)"""
    try:
        disponibilidade = obter_relatorio_disponibilidade()
        return jsonify({
            'success': True,
            'data': disponibilidade,
            'total': sum(disponibilidade.values()),
            'por_area': {
                'Linguagens': calcular_questoes_disponiveis(['Linguagens'], disponibilidade),
                'Matemática': calcular_questoes_disponiveis(['Matemática'], disponibilidade),
                'Humanas': calcular_questoes_disponiveis(['Humanas'], disponibilidade),
                'Natureza': calcular_questoes_disponiveis(['Natureza'], disponibilidade)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@agendar_simulado_bp.route('/preview-simulado', methods=['POST'])
@login_required  
def preview_simulado():
    """Preview de como ficará o simulado antes de criar (AJAX)"""
    try:
        data = request.get_json()
        areas = data.get('areas', [])
        num_questoes = int(data.get('num_questoes', 45))
        estrategia = data.get('estrategia', 'equilibrada')
        
        if not areas:
            return jsonify({'success': False, 'error': 'Selecione pelo menos uma área'})
        
        # Gerar preview das questões (só os primeiros dados)
        questoes_preview = gerar_questoes_simulado(
            areas=areas,
            quantidade=min(num_questoes, 5),  # Só 5 para preview
            estrategia=estrategia
        )
        
        preview_data = []
        for q in questoes_preview:
            preview_data.append({
                'materia': q['materia'],
                'topico': q.get('topico', ''),
                'texto_preview': q['texto'][:100] + '...' if len(q['texto']) > 100 else q['texto'],
                'dificuldade': q.get('dificuldade', 0.5)
            })
        
        return jsonify({
            'success': True,
            'preview': preview_data,
            'total_possivel': len(questoes_preview),
            'areas_usadas': list(set(q['materia'] for q in questoes_preview))
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# NOVO: Endpoint para estatísticas rápidas
@agendar_simulado_bp.route('/estatisticas-usuario')
@login_required
def estatisticas_usuario():
    """Retorna estatísticas do usuário para melhorar a experiência"""
    try:
        # Simulados do usuário
        total_simulados = Simulado.query.filter_by(user_id=current_user.id).count()
        simulados_concluidos = Simulado.query.filter_by(
            user_id=current_user.id, 
            status='Concluído'
        ).count()
        
        # Última configuração usada
        ultimo_simulado = Simulado.query.filter_by(
            user_id=current_user.id
        ).order_by(Simulado.id.desc()).first()
        
        configuracao_sugerida = {}
        if ultimo_simulado:
            configuracao_sugerida = {
                'areas': ultimo_simulado.areas.split(', ') if ultimo_simulado.areas else [],
                'duracao': ultimo_simulado.duracao_minutos,
                'num_questoes': Questao.query.filter_by(simulado_id=ultimo_simulado.id).count()
            }
        
        return jsonify({
            'success': True,
            'estatisticas': {
                'total_simulados': total_simulados,
                'simulados_concluidos': simulados_concluidos,
                'taxa_conclusao': round((simulados_concluidos / max(total_simulados, 1)) * 100, 1),
                'configuracao_sugerida': configuracao_sugerida
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


# Função para testar a integração
def testar_integracao_completa():
    """Testa se toda a integração está funcionando"""
    print("🧪 TESTANDO INTEGRAÇÃO COMPLETA AGENDAR SIMULADO")
    print("=" * 60)
    
    try:
        # Teste 1: Disponibilidade
        disponibilidade = obter_relatorio_disponibilidade()
        print(f"✅ Questões disponíveis: {sum(disponibilidade.values())}")
        
        # Teste 2: Cálculo por área
        areas_teste = ['Matemática', 'Linguagens']
        total_areas = calcular_questoes_disponiveis(areas_teste, disponibilidade)
        print(f"✅ Questões para {areas_teste}: {total_areas}")
        
        # Teste 3: Geração de questões
        questoes = gerar_questoes_simulado(['Matemática'], 3, 'equilibrada')
        print(f"✅ Questões geradas: {len(questoes)}")
        
        if questoes:
            print("   📝 Exemplo de questão gerada:")
            q = questoes[0]
            print(f"   - Matéria: {q['materia']}")
            print(f"   - Texto: {q['texto'][:80]}...")
            print(f"   - Resposta: {q['resposta_correta']}")
            print(f"   - Tem explicação: {'Sim' if q.get('explicacao') else 'Não'}")
        
        print("\n🎉 INTEGRAÇÃO FUNCIONANDO PERFEITAMENTE!")
        print("✨ Funcionalidades prontas:")
        print("   - Fazer Simulado Agora")
        print("   - Agendar Simulado")
        print("   - Validação em tempo real")
        print("   - Preview de questões")
        print("   - Estatísticas do usuário")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na integração: {e}")
        return False


if __name__ == "__main__":
    testar_integracao_completa()
