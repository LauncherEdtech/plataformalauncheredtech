# app/routes/cronograma.py
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date
from app import db
from app.models.estudo import (
    Cronograma, ItemCronograma, Materia, Modulo, Aula, ProgressoAula
)
import calendar

cronograma_bp = Blueprint('cronograma', __name__, url_prefix='/cronograma')

# ==========================================
# HELPERS
# ==========================================



def sincronizar_progresso_cronograma(cronograma):
    """
    Sincroniza o cronograma com o progresso real das aulas.
    Marca itens do cronograma como concluídos se a aula já foi assistida no sistema normal.
    """
    itens_atualizados = 0
    
    # Buscar todos os itens do cronograma que são aulas e ainda não foram marcados como concluídos
    itens_pendentes = cronograma.itens.filter(
        ItemCronograma.tipo_item == 'aula',
        ItemCronograma.aula_id.isnot(None),
        ItemCronograma.concluido == False
    ).all()
    
    for item in itens_pendentes:
        # Verificar se a aula já foi concluída no sistema normal
        progresso = ProgressoAula.query.filter_by(
            user_id=current_user.id,
            aula_id=item.aula_id
        ).first()
        
        if progresso and progresso.concluida:
            # Marcar o item do cronograma como concluído
            item.concluido = True
            item.data_conclusao = progresso.data_conclusao or datetime.utcnow()
            itens_atualizados += 1
    
    if itens_atualizados > 0:
        db.session.commit()
        print(f"✅ Sincronizado: {itens_atualizados} aulas marcadas como concluídas no cronograma")
    
    return itens_atualizados
    
    
def distribuir_aulas_no_cronograma(cronograma, materias_selecionadas, config_extras=None):
    """
    Distribui aulas no cronograma do usuário de forma sequencial, respeitando:
    - dias de estudo selecionados
    - horas por dia
    - priorização por dificuldade (opcional)
    Também adiciona simulados e redações, se configurado.
    """
    if config_extras is None:
        config_extras = {}
    
    # 1) Coletar todas as aulas das matérias selecionadas (por NOME da matéria)
    aulas_para_distribuir = []
    
    # Buscar todas as matérias com os nomes selecionados
    materias_obj = Materia.query.filter(Materia.id.in_(materias_selecionadas)).all()
    
    for materia in materias_obj:
        modulos = materia.modulos.filter_by(ativo=True).order_by(Modulo.ordem).all()
        for modulo in modulos:
            aulas = modulo.aulas.filter_by(ativa=True).order_by(Aula.ordem).all()
            for aula in aulas:
                progresso = ProgressoAula.query.filter_by(
                    user_id=current_user.id,
                    aula_id=aula.id
                ).first()
                if not progresso or not progresso.concluida:
                    aulas_para_distribuir.append({
                        "aula": aula,
                        "materia": materia.nome,
                        "modulo": modulo.titulo,
                        "dificuldade": getattr(modulo, "dificuldade", "medio"),
                        "duracao": aula.duracao_estimada or 30,
                        "ordem_global": len(aulas_para_distribuir),
                    })

    if not aulas_para_distribuir:
        return False, "Nenhuma aula disponível para incluir no cronograma."

    # 2) Ordenar por dificuldade, se configurado
    if getattr(cronograma, "priorizar_dificuldade", False):
        ordem = {"facil": 1, "medio": 2, "dificil": 3}
        aulas_para_distribuir.sort(
            key=lambda x: (ordem.get(x["dificuldade"], 2), x["ordem_global"])
        )

    # 3) ✅ CORRIGIDO: Mapeamento dos dias (Python weekday: 0=Monday)
    dias_mapeamento = {
        "seg": 0,  # Segunda-feira
        "ter": 1,  # Terça-feira
        "qua": 2,  # Quarta-feira
        "qui": 3,  # Quinta-feira
        "sex": 4,  # Sexta-feira
        "sab": 5,  # Sábado
        "dom": 6   # Domingo
    }
    
    dias_disponiveis = cronograma.dias_estudo or ["seg", "ter", "qua", "qui", "sex"]
    dias_validos = [d for d in dias_disponiveis if d in dias_mapeamento]
    dias_numeros = sorted([dias_mapeamento[d] for d in dias_validos])
    
    print(f"📅 Dias selecionados pelo usuário: {dias_validos}")
    print(f"📅 Dias em números (weekday): {dias_numeros}")

    horas_por_dia_dict = cronograma.horas_por_dia or {}
    data_atual = cronograma.data_inicio
    indice_aula = 0

    # 4) Distribuir aulas dia a dia
    max_iteracoes = 500
    iteracao = 0
    
    while indice_aula < len(aulas_para_distribuir) and iteracao < max_iteracoes:
        iteracao += 1
        dia_semana = data_atual.weekday()  # 0=Monday, 1=Tuesday, etc.
        
        # ✅ Só processar se é dia de estudo
        if dia_semana not in dias_numeros:
            data_atual += timedelta(days=1)
            if cronograma.data_fim_prevista and data_atual > cronograma.data_fim_prevista:
                break
            continue

        # Nome do dia para buscar horas
        nome_dia = [k for k, v in dias_mapeamento.items() if v == dia_semana][0]
        minutos_disponiveis_hoje = int(float(horas_por_dia_dict.get(nome_dia, 2))) * 60
        minutos_usados = 0
        ordem_no_dia = 1

        print(f"📆 Distribuindo aulas para {data_atual} ({nome_dia}) - {minutos_disponiveis_hoje} minutos disponíveis")

        # Preencher o dia
        while indice_aula < len(aulas_para_distribuir) and minutos_usados < minutos_disponiveis_hoje:
            info = aulas_para_distribuir[indice_aula]
            dur = int(info["duracao"])

            if minutos_usados + dur > minutos_disponiveis_hoje and ordem_no_dia > 1:
                break

            item = ItemCronograma(
                cronograma_id=cronograma.id,
                aula_id=info["aula"].id,
                data_prevista=data_atual,
                ordem_no_dia=ordem_no_dia,
                tempo_previsto=dur,
                tipo_item="aula",
            )
            db.session.add(item)

            minutos_usados += dur
            ordem_no_dia += 1
            indice_aula += 1

        # Próximo dia
        data_atual += timedelta(days=1)
        if cronograma.data_fim_prevista and data_atual > cronograma.data_fim_prevista:
            break

    # 5) ✅ CORRIGIDO: Adicionar simulados e redações (SEM limitar a "hoje")
    data_inicio_extras = cronograma.data_inicio
    data_fim_extras = cronograma.data_fim_prevista or (cronograma.data_inicio + timedelta(days=90))
    
    print(f"📝 Janela para simulados/redações: {data_inicio_extras} até {data_fim_extras}")
    
    # ✅ Incluir simulados com dia e frequência customizáveis
    if getattr(cronograma, "incluir_simulados", False):
        dia_simulado = config_extras.get('dia_simulados', 'sab')
        frequencia_simulados = config_extras.get('frequencia_simulados', 2)
        
        # Converter dia para número
        numero_dia_simulado = dias_mapeamento.get(dia_simulado, 5)  # default: sábado
        
        # Encontrar o primeiro dia adequado
        dias_ate_simulado = (numero_dia_simulado - data_inicio_extras.weekday()) % 7
        if dias_ate_simulado == 0:
            dias_ate_simulado = 7
        
        proxima_data_simulado = data_inicio_extras + timedelta(days=dias_ate_simulado)
        
        simulados_adicionados = 0
        while proxima_data_simulado <= data_fim_extras:
            db.session.add(ItemCronograma(
                cronograma_id=cronograma.id,
                aula_id=None,
                data_prevista=proxima_data_simulado,
                ordem_no_dia=1,
                tempo_previsto=180,  # 3 horas
                tipo_item="simulado",
                observacoes="📝 Simulado completo - Avaliar seu progresso",
            ))
            simulados_adicionados += 1
            print(f"📝 Simulado adicionado em {proxima_data_simulado}")
            proxima_data_simulado += timedelta(weeks=frequencia_simulados)
        
        print(f"✅ Total de simulados adicionados: {simulados_adicionados}")
    
    # ✅ Incluir redações com dia e frequência customizáveis
    if getattr(cronograma, "incluir_redacoes", False):
        dia_redacao = config_extras.get('dia_redacoes', 'dom')
        frequencia_redacoes = config_extras.get('frequencia_redacoes', 1)
        
        # Converter dia para número
        numero_dia_redacao = dias_mapeamento.get(dia_redacao, 6)  # default: domingo
        
        # Encontrar o primeiro dia adequado
        dias_ate_redacao = (numero_dia_redacao - data_inicio_extras.weekday()) % 7
        if dias_ate_redacao == 0:
            dias_ate_redacao = 7
        
        proxima_data_redacao = data_inicio_extras + timedelta(days=dias_ate_redacao)
        
        redacoes_adicionadas = 0
        while proxima_data_redacao <= data_fim_extras:
            db.session.add(ItemCronograma(
                cronograma_id=cronograma.id,
                aula_id=None,
                data_prevista=proxima_data_redacao,
                ordem_no_dia=2,
                tempo_previsto=60,  # 1 hora
                tipo_item="redacao",
                observacoes="✍️ Redação - Praticar escrita dissertativa",
            ))
            redacoes_adicionadas += 1
            print(f"✍️ Redação adicionada em {proxima_data_redacao}")
            proxima_data_redacao += timedelta(weeks=frequencia_redacoes)
        
        print(f"✅ Total de redações adicionadas: {redacoes_adicionadas}")

    db.session.commit()
    
    # Mensagem de sucesso
    msg_parts = [f"{indice_aula} aulas distribuídas"]
    if getattr(cronograma, "incluir_simulados", False):
        msg_parts.append("simulados")
    if getattr(cronograma, "incluir_redacoes", False):
        msg_parts.append("redações")
    
    return True, f"{', '.join(msg_parts)} no seu cronograma!"

# ==========================================
# ROTAS
# ==========================================

@cronograma_bp.route('/')
@login_required
def index():
    """Dashboard do cronograma"""
    cronograma_ativo = Cronograma.query.filter_by(
        user_id=current_user.id,
        ativo=True
    ).first()
    
    if not cronograma_ativo:
        return redirect(url_for('cronograma.intro'))
    
    # ✅ NOVO: Sincronizar progresso antes de exibir
    sincronizar_progresso_cronograma(cronograma_ativo)
    
    hoje = datetime.now().date()
    
    aulas_hoje = cronograma_ativo.aulas_hoje
    proxima_aula = cronograma_ativo.proxima_aula
    aulas_semana = cronograma_ativo.get_aulas_semana()
    
    progresso = cronograma_ativo.progresso_geral
    atrasados = cronograma_ativo.itens_atrasados
    
    hoje_obj = datetime.now()
    cal = calendar.monthcalendar(hoje_obj.year, hoje_obj.month)
    
    itens_mes = cronograma_ativo.itens.filter(
        db.extract('month', ItemCronograma.data_prevista) == hoje_obj.month,
        db.extract('year', ItemCronograma.data_prevista) == hoje_obj.year
    ).all()
    
    dias_com_aulas = {}
    for item in itens_mes:
        dia = item.data_prevista.day
        if dia not in dias_com_aulas:
            dias_com_aulas[dia] = {'total': 0, 'concluidas': 0}
        dias_com_aulas[dia]['total'] += 1
        if item.concluido:
            dias_com_aulas[dia]['concluidas'] += 1
    
    return render_template('cronograma/dashboard.html',
                         cronograma=cronograma_ativo,
                         aulas_hoje=aulas_hoje,
                         proxima_aula=proxima_aula,
                         aulas_semana=aulas_semana,
                         progresso=progresso,
                         atrasados=atrasados,
                         calendario=cal,
                         dias_com_aulas=dias_com_aulas,
                         mes_atual=hoje_obj.strftime('%B %Y'),
                         datetime=datetime,
                         today=date.today())




@cronograma_bp.route('/intro')
@login_required
def intro():
    """Página de introdução/boas-vindas"""
    tem_cronograma = Cronograma.query.filter_by(
        user_id=current_user.id,
        ativo=True
    ).first()
    
    if tem_cronograma:
        return redirect(url_for('cronograma.index'))
    
    materias = Materia.query.filter_by(ativa=True).order_by(Materia.nome).all()
    
    return render_template('cronograma/intro.html', materias=materias)


@cronograma_bp.route('/wizard')
@login_required
def wizard():
    """Wizard de criação de cronograma com matérias agrupadas por nome"""
    # Buscar todas as matérias ativas
    materias_todas = Materia.query.filter_by(ativa=True).order_by(Materia.nome).all()
    
    # ✅ NOVO: Agrupar matérias por nome (independente da seção)
    materias_agrupadas = {}
    for materia in materias_todas:
        nome = materia.nome
        if nome not in materias_agrupadas:
            materias_agrupadas[nome] = {
                'nome': nome,
                'icone': materia.icone or '📖',
                'ids': [],
                'secoes': []
            }
        materias_agrupadas[nome]['ids'].append(materia.id)
        
        # ✅ CORRIGIDO: Verificar se tem seção e usar o atributo correto
        if materia.secao:
            # Tentar diferentes atributos possíveis
            secao_nome = getattr(materia.secao, 'titulo', None) or \
                        getattr(materia.secao, 'nome', None) or \
                        f"Seção {materia.secao.id}"
            materias_agrupadas[nome]['secoes'].append(secao_nome)
    
    # Converter para lista
    materias_unicas = list(materias_agrupadas.values())
    
    return render_template(
        'cronograma/wizard.html',
        materias=materias_unicas,
        datetime=datetime,
        today=datetime.now().date()
    )

@cronograma_bp.route('/criar', methods=['POST'])
@login_required
def criar():
    """Processar criação do cronograma"""
    try:
        data = request.get_json()
        
        print("📥 Dados recebidos do frontend:")
        print(f"  - Dias de estudo: {data.get('dias_estudo')}")
        print(f"  - Horas por dia: {data.get('horas_por_dia')}")
        print(f"  - Incluir simulados: {data.get('incluir_simulados')}")
        print(f"  - Incluir redações: {data.get('incluir_redacoes')}")
        
        # Desativar cronogramas anteriores
        Cronograma.query.filter_by(user_id=current_user.id, ativo=True).update({'ativo': False})
        
        objetivo = data.get('objetivo', 'Estudar para o ENEM')
        data_inicio = datetime.strptime(data.get('data_inicio'), '%Y-%m-%d').date()
        
        data_prova_str = data.get('data_prova')
        data_prova = datetime.strptime(data_prova_str, '%Y-%m-%d').date() if data_prova_str else None
        
        if data_prova:
            data_fim = data_prova - timedelta(days=7)
        else:
            data_fim = data_inicio + timedelta(days=90)
        
        dias_estudo = data.get('dias_estudo', [])
        horas_por_dia = data.get('horas_por_dia', {})
        
        total_horas = sum([float(h) for h in horas_por_dia.values()])


        # Criar cronograma
        cronograma = Cronograma(
            user_id=current_user.id,
            objetivo=objetivo,
            data_inicio=data_inicio,
            data_fim_prevista=data_fim,
            data_prova=data_prova,
            horas_disponiveis_semana=int(total_horas),
            dias_estudo=dias_estudo,
            horas_por_dia=horas_por_dia,
            periodo_preferencia=data.get('periodo', 'flexivel'),
            nivel_atual=data.get('nivel', 'intermediario'),
            priorizar_dificuldade=data.get('priorizar_dificuldade', True),
            incluir_revisoes=data.get('incluir_revisoes', True),
            incluir_simulados=data.get('incluir_simulados', True),
            incluir_redacoes=data.get('incluir_redacoes', True),
            ativo=True
        )
        
        db.session.add(cronograma)
        db.session.flush()
        
        # ✅ Configurações extras para simulados e redações
        config_extras = {
            'dia_simulados': data.get('dia_simulados', 'sab'),
            'frequencia_simulados': int(data.get('frequencia_simulados', 2)),
            'dia_redacoes': data.get('dia_redacoes', 'dom'),
            'frequencia_redacoes': int(data.get('frequencia_redacoes', 1)),
        }
        
        print(f"⚙️ Configurações extras: {config_extras}")
        
        # Distribuir aulas
        materias_selecionadas = data.get('materias', [])
        sucesso, mensagem = distribuir_aulas_no_cronograma(cronograma, materias_selecionadas, config_extras)
        
        if not sucesso:
            db.session.rollback()
            return jsonify({'success': False, 'error': mensagem}), 400
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': mensagem,
            'cronograma_id': cronograma.id
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao criar cronograma: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@cronograma_bp.route('/api/marcar_concluido/<int:item_id>', methods=['POST'])
@login_required
def marcar_concluido(item_id):
    """Marcar um item do cronograma como concluído"""
    item = ItemCronograma.query.get_or_404(item_id)
    
    if item.cronograma.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Acesso negado'}), 403
    
    item.marcar_concluido()
    
    if item.aula_id:
        progresso = ProgressoAula.query.filter_by(
            user_id=current_user.id,
            aula_id=item.aula_id
        ).first()
        
        if progresso:
            progresso.concluida = True
            progresso.data_conclusao = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Aula marcada como concluída!',
        'progresso_geral': item.cronograma.progresso_geral
    })


@cronograma_bp.route('/calendario')
@login_required
def calendario():
    """Visualização em calendário"""
    cronograma = Cronograma.query.filter_by(
        user_id=current_user.id,
        ativo=True
    ).first()

    if not cronograma:
        return redirect(url_for('cronograma.intro'))
    
    # ✅ NOVO: Sincronizar progresso antes de exibir
    sincronizar_progresso_cronograma(cronograma)

    mes = int(request.args.get('mes', datetime.now().month))
    ano = int(request.args.get('ano', datetime.now().year))

    cal = calendar.monthcalendar(ano, mes)

    itens_mes = cronograma.itens.filter(
        db.extract('month', ItemCronograma.data_prevista) == mes,
        db.extract('year', ItemCronograma.data_prevista) == ano
    ).all()

    itens_por_dia = {}
    itens_por_dia_json = {}

    for item in itens_mes:
        dia = item.data_prevista.day
        
        itens_por_dia.setdefault(dia, []).append(item)
        
        item_dict = {
            "id": item.id,
            "tipo_item": item.tipo_item,
            "concluido": bool(item.concluido),
            "tempo_previsto": int(item.tempo_previsto) if item.tempo_previsto else 0,
            "ordem_no_dia": int(item.ordem_no_dia) if item.ordem_no_dia else 1,
            "observacoes": item.observacoes or "",
            "aula": None
        }
        
        if item.aula:
            item_dict["aula"] = {
                "id": item.aula.id,
                "titulo": item.aula.titulo,
                "modulo": {
                    "materia": {
                        "nome": item.aula.modulo.materia.nome
                    }
                } if item.aula.modulo and item.aula.modulo.materia else None
            }
        
        itens_por_dia_json.setdefault(dia, []).append(item_dict)
    
    meses = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]
    mes_nome = meses[mes - 1]
    
    hoje = datetime.now()
    
    return render_template('cronograma/calendario.html',
                         cronograma=cronograma,
                         calendario=cal,
                         itens_por_dia=itens_por_dia,
                         itens_por_dia_json=itens_por_dia_json,
                         mes=mes,
                         ano=ano,
                         mes_nome=mes_nome,
                         hoje_dia=hoje.day,
                         hoje_mes=hoje.month,
                         hoje_ano=hoje.year)


@cronograma_bp.route('/ajustar')
@login_required
def ajustar():
    """Página para ajustar o cronograma"""
    cronograma = Cronograma.query.filter_by(
        user_id=current_user.id,
        ativo=True
    ).first()
    
    if not cronograma:
        return redirect(url_for('cronograma.intro'))
    
    return render_template('cronograma/ajustar.html', cronograma=cronograma)


@cronograma_bp.route('/excluir', methods=['POST'])
@login_required
def excluir():
    """Excluir cronograma atual"""
    cronograma = Cronograma.query.filter_by(
        user_id=current_user.id,
        ativo=True
    ).first()
    
    if cronograma:
        db.session.delete(cronograma)
        db.session.commit()
        flash('Cronograma excluído com sucesso!', 'success')
    
    return redirect(url_for('cronograma.intro'))
