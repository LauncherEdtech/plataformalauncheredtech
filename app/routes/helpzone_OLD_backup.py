# app/routes/helpzone.py

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app.models.helpzone import Duvida, Resposta, DuvidaVoto, RespostaVoto, Notificacao, Badge, UserBadge
from app.models.user import User
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func

helpzone_bp = Blueprint('helpzone', __name__, url_prefix='/helpzone')

# Adicionar contexto global para todos os templates do Help Zone
@helpzone_bp.context_processor
def inject_models():
    """
    Disponibiliza modelos e utilitários para todos os templates do Help Zone.
    Isso evita ter que passar os modelos explicitamente em cada rota.
    """
    return {
        'User': User,
        'Duvida': Duvida, 
        'Resposta': Resposta,
        'DuvidaVoto': DuvidaVoto,
        'RespostaVoto': RespostaVoto,
        'Badge': Badge,
        'UserBadge': UserBadge,
        'Notificacao': Notificacao,
        'now': datetime.utcnow()  # Para calcular "há X tempo" nos templates
    }

@helpzone_bp.route('/')
def index():
    # Obter parâmetros de filtragem e ordenação
    palavrachave = request.args.get('q', '')
    area = request.args.get('area', '')
    ordenar = request.args.get('ordenar', 'recentes')
    status = request.args.get('status', '')  # Nova opção: 'pendente' ou 'resolvido'
    periodo = request.args.get('periodo', '')  # Nova opção: 'hoje', 'semana', 'mes'
    
    # Consulta base
    query = Duvida.query
    
    # Aplicar filtros
    if palavrachave:
        query = query.filter(Duvida.titulo.ilike(f'%{palavrachave}%') | 
                          Duvida.conteudo.ilike(f'%{palavrachave}%'))
    
    if area:
        query = query.filter(Duvida.area == area)
    
    if status:
        if status == 'pendente':
            query = query.filter(Duvida.resolvida == False)
        elif status == 'resolvido':
            query = query.filter(Duvida.resolvida == True)
    
    if periodo:
        hoje = datetime.utcnow().date()
        if periodo == 'hoje':
            query = query.filter(db.func.date(Duvida.data_criacao) == hoje)
        elif periodo == 'semana':
            uma_semana_atras = hoje - timedelta(days=7)
            query = query.filter(db.func.date(Duvida.data_criacao) >= uma_semana_atras)
        elif periodo == 'mes':
            um_mes_atras = hoje - timedelta(days=30)
            query = query.filter(db.func.date(Duvida.data_criacao) >= um_mes_atras)
    
    # Aplicar ordenação
    if ordenar == 'recentes':
        query = query.order_by(Duvida.data_criacao.desc())
    elif ordenar == 'populares':
        # Esta é uma solução simples; em produção, seria mais eficiente
        # usando um subquery com contagem de votos ou um campo calculado
        duvidas = query.all()
        duvidas.sort(key=lambda d: d.total_votos(), reverse=True)
        
        # Obter top ajudantes da semana (simplificado)
        top_ajudantes = User.query.order_by(User.xp_total.desc()).limit(3).all()
        
        # Obter dados para o gráfico de atividade (últimos 7 dias)
        data_atual = datetime.utcnow().date()
        labels = []
        duvidas_por_dia = []
        respostas_por_dia = []
        
        for i in range(6, -1, -1):
            data = data_atual - timedelta(days=i)
            labels.append(data.strftime('%d/%m'))
            
            # Contar dúvidas nesse dia
            count_duvidas = Duvida.query.filter(
                db.func.date(Duvida.data_criacao) == data
            ).count()
            duvidas_por_dia.append(count_duvidas)
            
            # Contar respostas nesse dia
            count_respostas = Resposta.query.filter(
                db.func.date(Resposta.data_criacao) == data
            ).count()
            respostas_por_dia.append(count_respostas)
        
        return render_template('helpzone/index.html',
                              duvidas=duvidas,
                              palavrachave=palavrachave,
                              area=area,
                              ordenar=ordenar,
                              status=status,
                              periodo=periodo,
                              areas_disponiveis=['matematica', 'portugues', 'quimica', 'fisica', 'biologia', 'historia', 'geografia', 'redacao'],
                              top_ajudantes=top_ajudantes,
                              chart_data={
                                  'labels': labels,
                                  'duvidas': duvidas_por_dia,
                                  'respostas': respostas_por_dia
                              })
    
    # Executar consulta
    duvidas = query.all()
    
    # Obter top ajudantes da semana (simplificado)
    top_ajudantes = User.query.order_by(User.xp_total.desc()).limit(3).all()
    
    # Obter dados para o gráfico de atividade (últimos 7 dias)
    data_atual = datetime.utcnow().date()
    labels = []
    duvidas_por_dia = []
    respostas_por_dia = []
    
    for i in range(6, -1, -1):
        data = data_atual - timedelta(days=i)
        labels.append(data.strftime('%d/%m'))
        
        # Contar dúvidas nesse dia
        count_duvidas = Duvida.query.filter(
            db.func.date(Duvida.data_criacao) == data
        ).count()
        duvidas_por_dia.append(count_duvidas)
        
        # Contar respostas nesse dia
        count_respostas = Resposta.query.filter(
            db.func.date(Resposta.data_criacao) == data
        ).count()
        respostas_por_dia.append(count_respostas)
    
    return render_template('helpzone/index.html',
                          duvidas=duvidas,
                          palavrachave=palavrachave,
                          area=area,
                          ordenar=ordenar,
                          status=status,
                          periodo=periodo,
                          areas_disponiveis=['matematica', 'portugues', 'quimica', 'fisica', 'biologia', 'historia', 'geografia', 'redacao'],
                          top_ajudantes=top_ajudantes,
                          chart_data={
                              'labels': labels,
                              'duvidas': duvidas_por_dia,
                              'respostas': respostas_por_dia
                          })

@helpzone_bp.route('/duvida/nova', methods=['GET', 'POST'])
@login_required
def nova_duvida():
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        conteudo = request.form.get('conteudo')
        area = request.form.get('area')
        
        if not titulo or not conteudo or not area:
            flash('Preencha todos os campos obrigatórios', 'warning')
            return render_template('helpzone/nova_duvida.html',
                                  areas_disponiveis=['matematica', 'portugues', 'quimica', 'fisica', 'biologia', 'historia', 'geografia', 'redacao'])
        
        duvida = Duvida(
            titulo=titulo,
            conteudo=conteudo,
            area=area,
            user_id=current_user.id
        )
        
        db.session.add(duvida)
        db.session.commit()
        
        flash('Sua dúvida foi publicada com sucesso!', 'success')
        return redirect(url_for('helpzone.duvida', duvida_id=duvida.id))
    
    return render_template('helpzone/nova_duvida.html',
                          areas_disponiveis=['matematica', 'portugues', 'quimica', 'fisica', 'biologia', 'historia', 'geografia', 'redacao'])

@helpzone_bp.route('/duvida/<int:duvida_id>')
def duvida(duvida_id):
    duvida = Duvida.query.get_or_404(duvida_id)
    respostas = Resposta.query.filter_by(duvida_id=duvida_id).order_by(Resposta.solucao.desc(), Resposta.data_criacao).all()
    
    # Verificar se o usuário atual tem mesma dúvida
    tem_mesma_duvida = False
    voto_duvida = None
    
    if current_user.is_authenticated:
        voto_duvida = DuvidaVoto.query.filter_by(duvida_id=duvida_id, user_id=current_user.id).first()
    
    # Obter informações de voto para cada resposta
    votos_respostas = {}
    if current_user.is_authenticated:
        for resposta in respostas:
            voto = RespostaVoto.query.filter_by(resposta_id=resposta.id, user_id=current_user.id).first()
            votos_respostas[resposta.id] = voto.valor if voto else 0
    
    return render_template('helpzone/duvida.html',
                          duvida=duvida,
                          respostas=respostas,
                          tem_mesma_duvida=tem_mesma_duvida,
                          voto_duvida=voto_duvida.valor if voto_duvida else 0,
                          votos_respostas=votos_respostas)

@helpzone_bp.route('/duvida/<int:duvida_id>/responder', methods=['POST'])
@login_required
def responder(duvida_id):
    duvida = Duvida.query.get_or_404(duvida_id)
    conteudo = request.form.get('conteudo')
    
    if not conteudo:
        flash('O conteúdo da resposta não pode estar vazio', 'warning')
        return redirect(url_for('helpzone.duvida', duvida_id=duvida_id))
    
    # Criar e adicionar a resposta
    resposta = Resposta(
        conteudo=conteudo,
        duvida_id=duvida_id,
        user_id=current_user.id
    )
    
    db.session.add(resposta)
    
    # Adicionar XP ao usuário por responder
    current_user.xp_total += 10
    
    # Primeira tentativa: tentar salvar tudo incluindo notificação
    try:
        # Criar notificação para o autor da dúvida
        if duvida.user_id != current_user.id:  # Não notificar se o próprio usuário responder
            notificacao = Notificacao(
                user_id=duvida.user_id,
                conteudo=f"{current_user.username} respondeu sua dúvida: '{duvida.titulo}'",
                link=url_for('helpzone.duvida', duvida_id=duvida_id)
            )
            db.session.add(notificacao)
        
        db.session.commit()
        flash('Sua resposta foi publicada com sucesso!', 'success')
        
        # Verificar se o usuário ganhou novas badges
        try:
            new_badges = check_and_award_badges(current_user.id)
            if new_badges:
                badge_names = ", ".join([badge.nome for badge in new_badges])
                flash(f'Parabéns! Você ganhou {len(new_badges)} nova(s) badge(s): {badge_names}', 'success')
        except Exception as e:
            # Ignorar erros de badges
            print(f"Erro ao verificar badges: {e}")
    
    except Exception as e:
        # Em caso de erro, reverte e tenta salvar apenas a resposta e o XP
        db.session.rollback()
        print(f"Erro ao responder (com notificação): {e}")
        
        # Segunda tentativa: salvar apenas os elementos essenciais
        db.session.add(resposta)
        current_user.xp_total += 10
        
        try:
            db.session.commit()
            flash('Sua resposta foi publicada com sucesso!', 'success')
        except Exception as e:
            # Se ainda houver erro, notificar o usuário
            db.session.rollback()
            print(f"Erro persistente ao responder: {e}")
            flash('Ocorreu um erro ao publicar sua resposta. Por favor, tente novamente.', 'danger')
    
    return redirect(url_for('helpzone.duvida', duvida_id=duvida_id))

@helpzone_bp.route('/duvida/<int:duvida_id>/mesma-duvida', methods=['GET', 'POST'])
@login_required
def mesma_duvida(duvida_id):
    # Implementar lógica para marcar que o usuário tem a mesma dúvida
    # Isso pode ser implementado como um tipo especial de voto
    flash('Marcado como "Tenho a mesma dúvida"', 'success')
    return redirect(url_for('helpzone.duvida', duvida_id=duvida_id))

@helpzone_bp.route('/resposta/<int:resposta_id>/solucao', methods=['POST'])
@login_required
def marcar_solucao(resposta_id):
    resposta = Resposta.query.get_or_404(resposta_id)
    duvida = Duvida.query.get_or_404(resposta.duvida_id)
    
    # Verificar permissão (apenas o autor da dúvida pode marcar como solução)
    if duvida.user_id != current_user.id:
        flash('Você não tem permissão para realizar esta ação', 'danger')
        return redirect(url_for('helpzone.duvida', duvida_id=duvida.id))
    
    # Desmarcar todas as respostas como solução
    for r in duvida.respostas:
        r.solucao = False
    
    # Marcar esta resposta como solução
    resposta.solucao = True
    
    # Marcar a dúvida como resolvida
    duvida.resolvida = True
    
    # Adicionar XP ao autor da resposta
    resposta_autor = User.query.get(resposta.user_id)
    if resposta_autor:
        resposta_autor.xp_total += 50
    
    # Tentativa de salvar com notificação
    try:
        # Criar notificação para o autor da resposta
        if resposta_autor and resposta_autor.id != current_user.id:
            notificacao = Notificacao(
                user_id=resposta_autor.id,
                conteudo=f"Sua resposta foi marcada como solução por {current_user.username}!",
                link=url_for('helpzone.duvida', duvida_id=duvida.id)
            )
            db.session.add(notificacao)
        
        db.session.commit()
        flash('Resposta marcada como solução!', 'success')
        
        # Verificar se o autor da resposta ganhou novas badges
        try:
            if resposta_autor:
                new_badges = check_and_award_badges(resposta_autor.id)
                if new_badges and resposta_autor.id == current_user.id:
                    badge_names = ", ".join([badge.nome for badge in new_badges])
                    flash(f'Parabéns! Você ganhou {len(new_badges)} nova(s) badge(s): {badge_names}', 'success')
        except Exception as e:
            # Ignorar erros relacionados a badges
            print(f"Erro ao verificar badges: {e}")
            
    except Exception as e:
        # Em caso de erro, reverte e tenta salvar apenas as alterações essenciais
        db.session.rollback()
        print(f"Erro ao marcar como solução (com notificação): {e}")
        
        # Segunda tentativa: salvar apenas as mudanças essenciais
        for r in duvida.respostas:
            r.solucao = False
        resposta.solucao = True
        duvida.resolvida = True
        if resposta_autor:
            resposta_autor.xp_total += 50
            
        try:
            db.session.commit()
            flash('Resposta marcada como solução!', 'success')
        except Exception as e:
            # Se ainda houver erro, notificar o usuário
            db.session.rollback()
            print(f"Erro persistente ao marcar como solução: {e}")
            flash('Ocorreu um erro ao marcar a resposta como solução. Por favor, tente novamente.', 'danger')
    
    return redirect(url_for('helpzone.duvida', duvida_id=duvida.id))

@helpzone_bp.route('/duvida/<int:duvida_id>/voto', methods=['POST'])
@login_required
def votar_duvida(duvida_id):
    duvida = Duvida.query.get_or_404(duvida_id)
    valor = int(request.form.get('valor', 0))
    
    if valor not in [-1, 0, 1]:
        flash('Valor de voto inválido', 'danger')
        return redirect(url_for('helpzone.duvida', duvida_id=duvida_id))
    
    # Verificar se o usuário já votou nesta dúvida
    voto = DuvidaVoto.query.filter_by(duvida_id=duvida_id, user_id=current_user.id).first()
    
    if voto:
        if valor == 0:
            # Remover voto
            db.session.delete(voto)
        else:
            # Atualizar voto
            voto.valor = valor
    else:
        # Criar novo voto
        voto = DuvidaVoto(
            valor=valor,
            duvida_id=duvida_id,
            user_id=current_user.id
        )
        db.session.add(voto)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao votar em dúvida: {e}")
        flash('Ocorreu um erro ao registrar seu voto. Por favor, tente novamente.', 'danger')
    
    return redirect(url_for('helpzone.duvida', duvida_id=duvida_id))

@helpzone_bp.route('/resposta/<int:resposta_id>/voto', methods=['POST'])
@login_required
def votar_resposta(resposta_id):
    resposta = Resposta.query.get_or_404(resposta_id)
    valor = int(request.form.get('valor', 0))
    
    if valor not in [-1, 0, 1]:
        flash('Valor de voto inválido', 'danger')
        return redirect(url_for('helpzone.duvida', duvida_id=resposta.duvida_id))
    
    # Verificar se o usuário já votou nesta resposta
    voto = RespostaVoto.query.filter_by(resposta_id=resposta_id, user_id=current_user.id).first()
    
    if voto:
        if valor == 0:
            # Remover voto
            db.session.delete(voto)
        else:
            # Atualizar voto
            voto.valor = valor
    else:
        # Criar novo voto
        voto = RespostaVoto(
            valor=valor,
            resposta_id=resposta_id,
            user_id=current_user.id
        )
        db.session.add(voto)
    
    # Tentativa de salvar voto e notificação
    try:
        # Se foi um voto positivo, criar notificação
        if valor > 0 and resposta.user_id != current_user.id:
            # Criar notificação para o autor da resposta
            notificacao = Notificacao(
                user_id=resposta.user_id,
                conteudo=f"{current_user.username} gostou da sua resposta.",
                link=url_for('helpzone.duvida', duvida_id=resposta.duvida_id)
            )
            db.session.add(notificacao)
        
        db.session.commit()
        
        # Verificar badges para o autor da resposta se foi um voto positivo
        try:
            if valor > 0 and resposta.user_id != current_user.id:
                check_and_award_badges(resposta.user_id)
        except Exception as e:
            # Ignorar erros relacionados a badges
            print(f"Erro ao verificar badges: {e}")
            
    except Exception as e:
        # Em caso de erro, reverte e tenta salvar apenas o voto
        db.session.rollback()
        print(f"Erro ao votar em resposta (com notificação): {e}")
        
        # Segunda tentativa: salvar apenas o voto
        if voto:
            if valor == 0:
                db.session.delete(voto)
            else:
                if hasattr(voto, 'id') and voto.id:  # Se já está no banco de dados
                    voto.valor = valor
                else:  # Se é um novo voto
                    db.session.add(voto)
        
        try:
            db.session.commit()
        except Exception as e:
            # Se ainda houver erro, notificar o usuário
            db.session.rollback()
            print(f"Erro persistente ao votar em resposta: {e}")
            flash('Ocorreu um erro ao registrar seu voto. Por favor, tente novamente.', 'danger')
    
    return redirect(url_for('helpzone.duvida', duvida_id=resposta.duvida_id))

@helpzone_bp.route('/user/<int:user_id>')
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    
    # Get user's questions
    questions = Duvida.query.filter_by(user_id=user_id).order_by(Duvida.data_criacao.desc()).all()
    
    # Get user's answers
    answers = Resposta.query.filter_by(user_id=user_id).order_by(Resposta.data_criacao.desc()).all()
    
    # Get user's accepted solutions (answers marked as solutions)
    accepted_solutions = Resposta.query.filter_by(user_id=user_id, solucao=True).count()
    
    # Get total upvotes received on questions and answers
    question_votes = db.session.query(func.sum(DuvidaVoto.valor)).filter(
        DuvidaVoto.duvida_id.in_([q.id for q in questions]) if questions else False
    ).scalar() or 0
    
    answer_votes = db.session.query(func.sum(RespostaVoto.valor)).filter(
        RespostaVoto.resposta_id.in_([a.id for a in answers]) if answers else False
    ).scalar() or 0
    
    total_votes = question_votes + answer_votes
    
    # Calculate Help Zone reputation
    reputation = (total_votes * 5) + (accepted_solutions * 20) + (len(answers) * 2)
    
    # Get top areas (tags the user has most answers in)
    question_areas = {}
    for question in questions:
        if question.area in question_areas:
            question_areas[question.area] += 1
        else:
            question_areas[question.area] = 1
    
    top_areas = sorted(question_areas.items(), key=lambda x: x[1], reverse=True)[:3]
    
    return render_template('helpzone/user_profile.html',
                          user=user,
                          questions=questions,
                          answers=answers,
                          accepted_solutions=accepted_solutions,
                          total_votes=total_votes,
                          reputation=reputation,
                          top_areas=top_areas)

@helpzone_bp.route('/ranking')
def ranking():
    """
    Página de ranking dos melhores ajudantes do Help Zone.
    O cálculo da reputação é baseado em:
    - Número de respostas dadas
    - Respostas marcadas como solução
    - Votos positivos recebidos
    """
    try:
        # Consultar todos usuários que têm atividade no Help Zone
        # (que têm pelo menos uma resposta)
        users_with_answers = db.session.query(User.id).join(Resposta, User.id == Resposta.user_id).distinct().subquery()
        
        # Buscar dados em paralelo para cada métrica do ranking
        active_users = User.query.filter(User.id.in_(users_with_answers)).all()
        
        # Preparar dados de ranking
        ranking_data = []
        for user in active_users:
            # Contar respostas
            answer_count = Resposta.query.filter_by(user_id=user.id).count()
            
            # Contar soluções (respostas marcadas como solução)
            solution_count = Resposta.query.filter_by(user_id=user.id, solucao=True).count()
            
            # Calcular total de votos positivos recebidos em respostas
            answer_ids = [r.id for r in Resposta.query.filter_by(user_id=user.id).all()]
            positive_votes = 0
            if answer_ids:
                positive_votes = db.session.query(func.sum(RespostaVoto.valor)).filter(
                    RespostaVoto.resposta_id.in_(answer_ids),
                    RespostaVoto.valor > 0
                ).scalar() or 0
            
            # Calcular reputação
            reputation = (answer_count * 2) + (solution_count * 20) + (positive_votes * 5)
            
            # Adicionar ao ranking
            ranking_data.append({
                'user': user,
                'answer_count': answer_count,
                'solution_count': solution_count,
                'positive_votes': positive_votes,
                'reputation': reputation
            })
        
        # Ordenar por reputação (do maior para o menor)
        ranking_data.sort(key=lambda x: x['reputation'], reverse=True)
        
        # Calcular posição no ranking
        for i, data in enumerate(ranking_data):
            data['position'] = i + 1
        
        # Obter intervalo de tempo (para mostrar "Ranking da Semana" ou "Ranking do Mês")
        periodo = request.args.get('periodo', 'geral')
        title = "Ranking Geral"
        
        if periodo == 'semana':
            title = "Ranking da Semana"
        elif periodo == 'mes':
            title = "Ranking do Mês"
    except Exception as e:
        # Em caso de erro, retornar uma lista vazia
        print(f"Erro ao gerar ranking: {e}")
        ranking_data = []
        periodo = request.args.get('periodo', 'geral')
        title = "Ranking Geral"
    
    return render_template('helpzone/ranking.html',
                          ranking_data=ranking_data,
                          title=title,
                          periodo=periodo)

@helpzone_bp.route('/badges')
def badges():
    """Página que mostra todas as badges disponíveis no Help Zone"""
    try:
        badges = Badge.query.all()
        
        # Agrupar badges por tipo
        badges_by_type = {}
        for badge in badges:
            if badge.req_tipo not in badges_by_type:
                badges_by_type[badge.req_tipo] = []
            badges_by_type[badge.req_tipo].append(badge)
        
        # Verificar quais badges o usuário atual já conquistou
        user_badges = []
        if current_user.is_authenticated:
            user_badges = [ub.badge_id for ub in UserBadge.query.filter_by(user_id=current_user.id).all()]
    except Exception as e:
        # Em caso de erro, mostrar mensagem e retornar listas vazias
        print(f"Erro ao obter badges: {e}")
        badges_by_type = {}
        user_badges = []
        flash('Não foi possível carregar as badges. O sistema pode estar em manutenção.', 'warning')
    
    return render_template('helpzone/badges.html',
                          badges_by_type=badges_by_type,
                          user_badges=user_badges)

@helpzone_bp.route('/notificacoes')
@login_required
def notificacoes():
    try:
        notificacoes = Notificacao.query.filter_by(
            user_id=current_user.id
        ).order_by(Notificacao.data_criacao.desc()).all()
    except Exception as e:
        # Em caso de erro, mostrar mensagem e retornar lista vazia
        print(f"Erro ao obter notificações: {e}")
        notificacoes = []
        flash('Não foi possível carregar as notificações. O sistema pode estar em manutenção.', 'warning')
    
    return render_template('helpzone/notificacoes.html', notificacoes=notificacoes)

@helpzone_bp.route('/notificacoes/<int:notificacao_id>/marcar-lida', methods=['POST'])
@login_required
def marcar_notificacao_lida(notificacao_id):
    try:
        notificacao = Notificacao.query.filter_by(id=notificacao_id, user_id=current_user.id).first_or_404()
        notificacao.lida = True
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Erro ao marcar notificação como lida: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Não foi possível marcar a notificação como lida'})

@helpzone_bp.route('/notificacoes/marcar-todas-lidas', methods=['POST'])
@login_required
def marcar_todas_notificacoes_lidas():
    try:
        Notificacao.query.filter_by(user_id=current_user.id, lida=False).update({'lida': True})
        db.session.commit()
    except Exception as e:
        print(f"Erro ao marcar todas notificações como lidas: {e}")
        db.session.rollback()
        flash('Não foi possível marcar todas as notificações como lidas.', 'warning')
    
    return redirect(url_for('helpzone.notificacoes'))

# Função para verificar e conceder badges ao usuário
def check_and_award_badges(user_id):
    """
    Verifica se o usuário cumpre os requisitos para novas badges e concede se necessário.
    Retorna uma lista de novas badges concedidas (vazia se nenhuma).
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return []
        
        # Obter todas as badges que o usuário ainda não conquistou
        try:
            user_badge_ids = [ub.badge_id for ub in UserBadge.query.filter_by(user_id=user_id).all()]
            available_badges = Badge.query.filter(~Badge.id.in_(user_badge_ids) if user_badge_ids else True).all()
        except Exception as e:
            print(f"Erro ao buscar badges: {e}")
            return []
        
        # Obter estatísticas do usuário
        answers_count = Resposta.query.filter_by(user_id=user_id).count()
        solution_count = Resposta.query.filter_by(user_id=user_id, solucao=True).count()
        
        # Votos positivos recebidos em respostas
        answer_ids = [r.id for r in Resposta.query.filter_by(user_id=user_id).all()]
        positive_votes = 0
        if answer_ids:
            try:
                positive_votes = db.session.query(func.sum(RespostaVoto.valor)).filter(
                    RespostaVoto.resposta_id.in_(answer_ids),
                    RespostaVoto.valor > 0
                ).scalar() or 0
            except Exception as e:
                print(f"Erro ao calcular votos positivos: {e}")
        
        # Lista para armazenar novas badges conquistadas
        new_badges = []
        
        # Verificar cada badge disponível
        for badge in available_badges:
            concedido = False
            
            if badge.req_tipo == 'respostas' and answers_count >= badge.req_quantidade:
                concedido = True
            elif badge.req_tipo == 'solucoes' and solution_count >= badge.req_quantidade:
                concedido = True
            elif badge.req_tipo == 'votos' and positive_votes >= badge.req_quantidade:
                concedido = True
            
            if concedido:
                # Tentar conceder a badge
                try:
                    # Conceder a badge
                    user_badge = UserBadge(user_id=user_id, badge_id=badge.id)
                    db.session.add(user_badge)
                    new_badges.append(badge)
                    
                    # Tentar criar notificação para o usuário
                    try:
                        notificacao = Notificacao(
                            user_id=user_id,
                            conteudo=f"Você conquistou a badge \"{badge.nome}\"!",
                            link=url_for('helpzone.user_profile', user_id=user_id)
                        )
                        db.session.add(notificacao)
                    except Exception as e:
                        print(f"Erro ao criar notificação de badge: {e}")
                except Exception as e:
                    print(f"Erro ao conceder badge: {e}")
        
        if new_badges:
            try:
                db.session.commit()
            except Exception as e:
                print(f"Erro ao salvar novas badges: {e}")
                db.session.rollback()
                
                # Tentar salvar apenas as badges sem notificações
                for badge in new_badges:
                    user_badge = UserBadge(user_id=user_id, badge_id=badge.id)
                    db.session.add(user_badge)
                try:
                    db.session.commit()
                except Exception as e:
                    print(f"Erro persistente ao salvar badges: {e}")
                    db.session.rollback()
                    return []
        
        return new_badges
    except Exception as e:
        print(f"Erro geral ao verificar badges: {e}")
        return []

# Função para inicializar badges padrão no banco de dados
def initialize_badges():
    """
    Cria as badges padrão no banco de dados, se não existirem.
    Esta função pode ser chamada durante a inicialização da aplicação.
    """
    try:
        badges = [
            # Badges de Respostas
            {
                'nome': 'Ajudante Iniciante',
                'descricao': 'Deu 5 respostas no Help Zone',
                'icon': 'bi bi-chat',
                'cor': 'primary',
                'req_quantidade': 5,
                'req_tipo': 'respostas'
            },
            {
                'nome': 'Ajudante Ativo',
                'descricao': 'Deu 25 respostas no Help Zone',
                'icon': 'bi bi-chat-dots',
                'cor': 'info',
                'req_quantidade': 25,
                'req_tipo': 'respostas'
            },
            {
                'nome': 'Super Ajudante',
                'descricao': 'Deu 100 respostas no Help Zone',
                'icon': 'bi bi-chat-dots-fill',
                'cor': 'info',
                'req_quantidade': 100,
                'req_tipo': 'respostas'
            },
            
            # Badges de Soluções
            {
                'nome': 'Solucionador',
                'descricao': 'Teve 3 respostas marcadas como solução',
                'icon': 'bi bi-check-circle',
                'cor': 'success',
                'req_quantidade': 3,
                'req_tipo': 'solucoes'
            },
            {
                'nome': 'Mestre Solucionador',
                'descricao': 'Teve 10 respostas marcadas como solução',
                'icon': 'bi bi-check-circle-fill',
                'cor': 'success',
                'req_quantidade': 10,
                'req_tipo': 'solucoes'
            },
            {
                'nome': 'Guru das Soluções',
                'descricao': 'Teve 25 respostas marcadas como solução',
                'icon': 'bi bi-patch-check-fill',
                'cor': 'success',
                'req_quantidade': 25,
                'req_tipo': 'solucoes'
            },
            
            # Badges de Votos
            {
                'nome': 'Respeitado',
                'descricao': 'Recebeu 10 votos positivos',
                'icon': 'bi bi-hand-thumbs-up',
                'cor': 'warning',
                'req_quantidade': 10,
                'req_tipo': 'votos'
            },
            {
                'nome': 'Muito Respeitado',
                'descricao': 'Recebeu 50 votos positivos',
                'icon': 'bi bi-hand-thumbs-up-fill',
                'cor': 'warning',
                'req_quantidade': 50,
                'req_tipo': 'votos'
            },
            {
                'nome': 'Referência da Comunidade',
                'descricao': 'Recebeu 100 votos positivos',
                'icon': 'bi bi-star-fill',
                'cor': 'warning',
                'req_quantidade': 100,
                'req_tipo': 'votos'
            }
        ]
        
        # Verificar cada badge e criar se não existir
        for badge_data in badges:
            badge = Badge.query.filter_by(nome=badge_data['nome']).first()
            if not badge:
                badge = Badge(**badge_data)
                db.session.add(badge)
        
        db.session.commit()
        print("[+] Badges inicializadas com sucesso!")
    except Exception as e:
        print(f"[-] Erro ao inicializar badges: {e}")
        db.session.rollback()

# Adicionar funções auxiliares ao contexto do template
@helpzone_bp.context_processor
def utility_processor():
    def unread_notifications_count():
        if current_user.is_authenticated:
            try:
                return Notificacao.query.filter_by(user_id=current_user.id, lida=False).count()
            except Exception as e:
                print(f"Erro ao contar notificações não lidas: {e}")
                return 0
        return 0
    
    return {'unread_notifications_count': unread_notifications_count}
