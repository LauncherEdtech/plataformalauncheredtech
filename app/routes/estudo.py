# app/routes/estudo.py
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.decorators.freemium import requer_aula_disponivel
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from app import db
import os
from werkzeug.utils import secure_filename
import uuid
from PIL import Image
from app.models.estatisticas import TempoEstudo




# ===== Blueprint =====
estudo_bp = Blueprint('estudo', __name__, url_prefix='/estudo')

# ===== Constantes de upload =====
UPLOAD_FOLDER = 'app/static/uploads/materiais'
MATERIAS_FOLDER = 'app/static/images/covers/materias'
ALLOWED_IMAGES = {'jpg', 'jpeg', 'png', 'webp'}
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'gif'}

# ===== Helpers genéricos =====
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGES

def salvar_imagem_materia(form_picture):
    """Salva a imagem da matéria com nome único e redimensiona para 400x225."""
    random_hex = uuid.uuid4().hex
    _, file_ext = os.path.splitext(form_picture.filename)
    picture_filename = f"materia_{random_hex}{file_ext}"

    picture_folder = os.path.join(current_app.root_path, 'static', 'images', 'covers', 'materias')
    os.makedirs(picture_folder, exist_ok=True)
    picture_path = os.path.join(picture_folder, picture_filename)

    try:
        img = Image.open(form_picture)
        if img.mode == 'RGBA':
            img = img.convert('RGB')

        target_size = (400, 225)
        img.thumbnail(target_size, Image.Resampling.LANCZOS)

        new_img = Image.new('RGB', target_size, (0, 0, 0))
        x = (target_size[0] - img.width) // 2
        y = (target_size[1] - img.height) // 2
        new_img.paste(img, (x, y))
        new_img.save(picture_path, optimize=True, quality=85)

        return f"images/covers/materias/{picture_filename}"
    except Exception as e:
        current_app.logger.error(f"Erro ao processar imagem: {e}")
        raise e

def deletar_imagem_materia(capa_url):
    """Deleta a imagem antiga da matéria, se existir."""
    if capa_url and not capa_url.startswith('images/covers/placeholder'):
        try:
            image_path = os.path.join(current_app.root_path, 'static', capa_url)
            if os.path.exists(image_path):
                os.remove(image_path)
                current_app.logger.info(f"Imagem deletada: {image_path}")
        except Exception as e:
            current_app.logger.error(f"Erro ao deletar imagem: {e}")

def calcular_xp_por_tempo(tempo_segundos):
    """2 XP + 1 diamante a cada 3 minutos."""
    minutos = tempo_segundos // 60
    intervalos_3min = minutos // 3
    return {'xp': intervalos_3min * 2, 'diamantes': intervalos_3min * 1, 'intervalos': intervalos_3min}

def calcular_recompensa_aula_finalizada():
    """4 XP + 2 diamantes por aula concluída."""
    return {'xp': 4, 'diamantes': 2}

def _is_admin():
    return bool(getattr(current_user, 'is_admin', False))

# ==========================
# PROGRESSO – Helpers
# ==========================
def preparar_dados_materia(materia, user_id):
    from app.models.estudo import Modulo, Aula, ProgressoAula
    total_aulas = db.session.query(Aula).join(Modulo).filter(
        Modulo.materia_id == materia.id, Aula.ativa == True
    ).count()
    aulas_concluidas = 0
    if total_aulas > 0:
        aulas_concluidas = db.session.query(ProgressoAula).join(Aula).join(Modulo).filter(
            Modulo.materia_id == materia.id,
            ProgressoAula.user_id == user_id,
            ProgressoAula.concluida == True
        ).count()
    materia.progresso_calculado = (aulas_concluidas / total_aulas * 100) if total_aulas > 0 else 0
    materia.total_aulas = total_aulas
    materia.aulas_concluidas = aulas_concluidas
    return materia

def preparar_dados_modulo(modulo, user_id):
    from app.models.estudo import Aula, ProgressoAula
    total_aulas = modulo.aulas.filter_by(ativa=True).count()
    aulas_concluidas = 0
    if total_aulas > 0:
        aulas_concluidas = db.session.query(ProgressoAula).join(Aula).filter(
            Aula.modulo_id == modulo.id,
            ProgressoAula.user_id == user_id,
            ProgressoAula.concluida == True
        ).count()
    modulo.progresso_calculado = (aulas_concluidas / total_aulas * 100) if total_aulas > 0 else 0
    modulo.total_aulas = total_aulas
    modulo.aulas_concluidas = aulas_concluidas
    return modulo

def calcular_sequencia_estudo(user_id):
    from app.models.estudo import SessaoEstudo
    hoje = datetime.now().date()
    sequencia = 0
    data_verificacao = hoje
    while sequencia < 365:
        sessoes_do_dia = SessaoEstudo.query.filter(
            SessaoEstudo.user_id == user_id,
            func.date(SessaoEstudo.inicio) == data_verificacao,
            SessaoEstudo.tempo_ativo >= 300
        ).first()
        if sessoes_do_dia:
            sequencia += 1
            data_verificacao -= timedelta(days=1)
        else:
            break
    return sequencia

# ==========================
# PÚBLICO
# ==========================
@estudo_bp.route('/')
@login_required
def index():
    """
    Página de 'Matérias' nativa do sistema.
    CORRIGIDO: Agora filtra apenas matérias do núcleo global (secao_id IS NULL).
    """
    try:
        inspector = db.inspect(db.engine)
        if 'materia' not in inspector.get_table_names():
            flash('Sistema de estudos em manutenção.', 'info')
            return redirect(url_for('dashboard.index'))

        from app.models.estudo import Materia
        
        # CORRIGIDO: Buscar apenas matérias do núcleo global
        materias = (Materia.query
                    .filter(Materia.ativa == True, Materia.secao_id.is_(None))
                    .order_by(Materia.ordem, Materia.id)
                    .all())

        for materia in materias:
            # Usar função safe para evitar erros
            try:
                from app.routes.estudo import preparar_dados_materia
                preparar_dados_materia(materia, current_user.id)
                materia.progresso_usuario = materia.progresso_calculado
            except Exception as e:
                print(f"Erro ao preparar dados da materia {materia.id}: {e}")
                materia.progresso_usuario = 0
                materia.progresso_calculado = 0

        return render_template('estudo/index.html', materias=materias)

    except Exception as e:
        current_app.logger.error(f"Erro na página de estudos: {e}")
        flash('Erro ao carregar página de estudos.', 'error')
        return redirect(url_for('dashboard.index'))

@estudo_bp.route('/materia/<int:materia_id>')
@login_required
def materia(materia_id):
    try:
        from app.models.estudo import Materia, Modulo, Aula, ProgressoAula
        materia = Materia.query.get_or_404(materia_id)
        if not materia.ativa:
            flash('Esta matéria não está disponível no momento.', 'warning')
            return redirect(url_for('estudo.index'))

        preparar_dados_materia(materia, current_user.id)
        modulos = materia.modulos.filter_by(ativo=True).order_by(Modulo.ordem).all()

        total_aulas_geral = 0
        for modulo in modulos:
            preparar_dados_modulo(modulo, current_user.id)
            modulo.progresso_usuario = modulo.progresso_calculado
            total_aulas_geral += modulo.total_aulas

        materia.total_aulas_geral = total_aulas_geral
        materia.progresso_usuario = materia.progresso_calculado

        return render_template('estudo/materia.html', materia=materia, modulos=modulos)
    except Exception as e:
        current_app.logger.error(f"Erro ao carregar matéria {materia_id}: {e}")
        import traceback; current_app.logger.error(traceback.format_exc())
        flash('Erro ao carregar matéria.', 'error')
        return redirect(url_for('estudo.index'))

@estudo_bp.route('/modulo/<int:modulo_id>')
@login_required
def modulo(modulo_id):
    try:
        from app.models.estudo import Modulo, Aula, ProgressoAula
        modulo = Modulo.query.get_or_404(modulo_id)
        if not modulo.ativo:
            flash('Este módulo não está disponível no momento.', 'warning')
            return redirect(url_for('estudo.materia', materia_id=modulo.materia_id))

        preparar_dados_modulo(modulo, current_user.id)
        modulo.progresso_usuario = modulo.progresso_calculado

        aulas = modulo.aulas.filter_by(ativa=True).order_by(Aula.ordem).all()
        for aula in aulas:
            progresso = ProgressoAula.query.filter_by(
                user_id=current_user.id, aula_id=aula.id
            ).first()
            aula.progresso = progresso
            aula.concluida = progresso.concluida if progresso else False
            if progresso and aula.duracao_estimada:
                tempo_total_segundos = aula.duracao_estimada * 60
                aula.progresso_percentual = min((progresso.tempo_assistido / tempo_total_segundos) * 100, 100)
            else:
                aula.progresso_percentual = 0

        return render_template('estudo/modulo.html', modulo=modulo, aulas=aulas)
    except Exception as e:
        current_app.logger.error(f"Erro ao carregar módulo {modulo_id}: {e}")
        import traceback; current_app.logger.error(traceback.format_exc())
        flash('Erro ao carregar módulo.', 'error')
        return redirect(url_for('estudo.index'))

@estudo_bp.route('/aula/<int:aula_id>')
@login_required
@requer_aula_disponivel
def aula(aula_id):
    try:
        from app.models.estudo import Aula, ProgressoAula, SessaoEstudo, MaterialAula
        aula = Aula.query.get_or_404(aula_id)
        if not aula.ativa:
            flash('Esta aula não está disponível no momento.', 'warning')
            return redirect(url_for('estudo.modulo', modulo_id=aula.modulo_id))

        progresso = ProgressoAula.query.filter_by(user_id=current_user.id, aula_id=aula_id).first()
        if not progresso:
            current_user.consumir_aula_gratuita()
            progresso = ProgressoAula(user_id=current_user.id, aula_id=aula_id, tempo_assistido=0, concluida=False)
            db.session.add(progresso)
            db.session.commit()

        sessao = TempoEstudo(user_id=current_user.id, data_inicio=datetime.utcnow(), atividade='aula', minutos=0)
        db.session.add(sessao); db.session.commit()

        materiais = MaterialAula.query.filter_by(aula_id=aula_id).all()
        return render_template('estudo/aula.html', aula=aula, progresso=progresso, materiais=materiais, sessao_id=sessao.id)
    except Exception as e:
        current_app.logger.error(f"Erro ao carregar aula {aula_id}: {e}")
        flash('Erro ao carregar aula.', 'error')
        return redirect(url_for('estudo.index'))

# ==========================
# APIs
# ==========================
@estudo_bp.route('/api/atualizar_progresso', methods=['POST'])
@login_required
def atualizar_progresso():
    try:
        from app.models.estudo import Aula, ProgressoAula, SessaoEstudo
        from app.services.xp_service import XpService

        data = request.get_json()
        aula_id = data.get('aula_id')
        tempo_assistido = data.get('tempo_assistido', 0)
        sessao_id = data.get('sessao_id')
        forcar_conclusao = data.get('forcar_conclusao', False)

        if not aula_id:
            return jsonify({'error': 'aula_id é obrigatório'}), 400

        progresso = ProgressoAula.query.filter_by(user_id=current_user.id, aula_id=aula_id).first()
        if not progresso:
            progresso = ProgressoAula(user_id=current_user.id, aula_id=aula_id, tempo_assistido=0, concluida=False)
            db.session.add(progresso)

        tempo_anterior = progresso.tempo_assistido
        progresso.tempo_assistido = max(progresso.tempo_assistido, tempo_assistido)
        tempo_adicional = progresso.tempo_assistido - tempo_anterior
        progresso.ultima_atividade = datetime.utcnow()

        xp_ganho_tempo = 0
        diamantes_ganhos_tempo = 0
        if tempo_adicional >= 180:
            intervalos_3min = int(tempo_adicional // 180)
            xp_ganho_tempo = intervalos_3min * 2
            diamantes_ganhos_tempo = intervalos_3min * 1
            XpService.conceder_xp(current_user, xp_ganho_tempo, 'aula_tempo', f'Estudo contínuo: {intervalos_3min} intervalos de 3min')

        aula = Aula.query.get(aula_id)
        deve_concluir = forcar_conclusao
        if not deve_concluir and aula.duracao_estimada:
            deve_concluir = tempo_assistido >= (aula.duracao_estimada * 60 * 0.8)

        xp_ganho_conclusao = 0
        diamantes_ganhos_conclusao = 0
        if deve_concluir and not progresso.concluida:
            progresso.concluida = True
            progresso.data_conclusao = datetime.utcnow()
            xp_ganho_conclusao = 4
            diamantes_ganhos_conclusao = 2
            XpService.conceder_xp(current_user, xp_ganho_conclusao, 'aula_finalizada', f'Aula concluída: {aula.titulo}')

        if sessao_id:
            sessao = TempoEstudo.query.get(sessao_id)
            if sessao and not sessao.data_fim:
                minutos_atuais = max(1, int(tempo_assistido / 60))
                sessao.minutos = minutos_atuais
                #sessao.tempo_ativo = tempo_assistido

        db.session.commit()
        return jsonify({
            'success': True,
            'xp_ganho_tempo': xp_ganho_tempo,
            'diamantes_ganhos_tempo': diamantes_ganhos_tempo,
            'xp_ganho_conclusao': xp_ganho_conclusao,
            'diamantes_ganhos_conclusao': diamantes_ganhos_conclusao,
            'aula_concluida': progresso.concluida,
            'tempo_total': progresso.tempo_assistido
        })
    except Exception as e:
        current_app.logger.error(f"Erro ao atualizar progresso: {e}")
        db.session.rollback()
        return jsonify({'error': 'Erro interno'}), 500


@estudo_bp.route('/api/finalizar_sessao', methods=['POST'])
@login_required
def finalizar_sessao():
    """Finaliza sessão e concede XP por tempo (a cada 3 min)."""
    try:
        from app.models.estudo import SessaoEstudo
        from app.services.xp_service import XpService

        data = request.get_json()
        sessao_id = data.get('sessao_id')
        tempo_total = data.get('tempo_total', 0)

        if not sessao_id:
            return jsonify({'error': 'sessao_id é obrigatório'}), 400

        sessao = TempoEstudo.query.get(sessao_id)
        if not sessao or sessao.data_fim:

            return jsonify({'error': 'Sessão não encontrada ou já finalizada'}), 400

        sessao.fim = datetime.utcnow()
        #sessao.tempo_ativo = tempo_total
        #sessao.ativa = False
        minutos_estudados = max(1, int(tempo_total / 60))
        sessao.minutos = minutos_estudados


        #recompensas_tempo = calcular_xp_por_tempo(tempo_total)
        #xp_total_ganho = 0
        #diamantes_total_ganhos = 0

        xp_ganho = min(minutos_estudados * 2, 240)
        if xp_ganho > 0: XpService.conceder_xp(current_user, xp_ganho,'aula_tempo',f'Estudo de aula: {minutos_estudados} minutos')



        if recompensas_tempo['xp'] > 0:
            XpService.conceder_xp(current_user, recompensas_tempo['xp'], 'aula_tempo',
                                  f"Tempo de estudo: {recompensas_tempo['intervalos']} intervalos de 3min")
            xp_total_ganho += recompensas_tempo['xp']
            diamantes_total_ganhos += recompensas_tempo['diamantes']

        db.session.commit()
        return jsonify({
            'success': True,
            'tempo_total': tempo_total,
            'xp_ganho': xp_total_ganho,
            'diamantes_ganhos': diamantes_total_ganhos,
            'intervalos_3min': recompensas_tempo['intervalos'],
            'mensagem': f'Sessão finalizada! +{xp_total_ganho} XP + {diamantes_total_ganhos} 💎'
        })
    except Exception as e:
        current_app.logger.error(f"Erro ao finalizar sessão: {e}")
        db.session.rollback()
        return jsonify({'error': 'Erro interno'}), 500

@estudo_bp.route('/api/estatisticas_detalhadas')
@login_required
def estatisticas_detalhadas():
    try:
        from app.models.estudo import Materia, Modulo, Aula, SessaoEstudo, Moeda, ProgressoAula
        user_id = current_user.id

        tempo_total = db.session.query(func.sum(SessaoEstudo.tempo_ativo)).filter_by(
            user_id=user_id, ativa=False
        ).scalar() or 0

        tempo_por_materia = db.session.query(
            Materia.nome, func.sum(SessaoEstudo.tempo_ativo).label('tempo_total')
        ).join(Modulo).join(Aula).join(SessaoEstudo).filter(
            SessaoEstudo.user_id == user_id, SessaoEstudo.ativa == False
        ).group_by(Materia.id, Materia.nome).all()

        stats_aulas = {
            'concluidas': ProgressoAula.query.filter_by(user_id=user_id, concluida=True).count(),
            'em_andamento': ProgressoAula.query.filter(
                ProgressoAula.user_id == user_id, ProgressoAula.concluida == False, ProgressoAula.tempo_assistido > 0
            ).count(),
            'nao_iniciadas': db.session.query(Aula).outerjoin(
                ProgressoAula, and_(Aula.id == ProgressoAula.aula_id, ProgressoAula.user_id == user_id)
            ).filter(ProgressoAula.id.is_(None), Aula.ativa == True).count()
        }

        trinta_dias_atras = datetime.now() - timedelta(days=30)
        historico_moedas = db.session.query(
            func.date(Moeda.data).label('data'), func.sum(Moeda.quantidade).label('moedas')
        ).filter(
            Moeda.user_id == user_id, Moeda.data >= trinta_dias_atras, Moeda.quantidade > 0
        ).group_by(func.date(Moeda.data)).order_by('data').all()

        return jsonify({
            'tempo_total_minutos': tempo_total // 60,
            'tempo_por_materia': [{'materia': nome, 'tempo_minutos': tempo // 60} for nome, tempo in tempo_por_materia],
            'stats_aulas': stats_aulas,
            'historico_moedas': [{'data': data.strftime('%Y-%m-%d'), 'moedas': int(moedas)} for data, moedas in historico_moedas]
        })
    except Exception as e:
        current_app.logger.error(f"Erro ao obter estatísticas: {e}")
        return jsonify({'error': 'Erro ao obter estatísticas'}), 500

@estudo_bp.route('/api/visualizar_materia', methods=['POST'])
@login_required
def visualizar_materia():
    data = request.get_json()
    _ = data.get('materia_id')
    return jsonify({'success': True})

@estudo_bp.route('/api/visualizar_modulo', methods=['POST'])
@login_required
def visualizar_modulo():
    data = request.get_json()
    _ = data.get('modulo_id')
    return jsonify({'success': True})

@estudo_bp.route('/api/ranking_estudo')
@login_required
def ranking_estudo():
    try:
        from app.models.estudo import SessaoEstudo
        from app.models.user import User
        ranking = db.session.query(
            User.id, User.nome_completo, func.sum(SessaoEstudo.tempo_ativo).label('tempo_total')
        ).join(SessaoEstudo).filter(
            SessaoEstudo.ativa == False
        ).group_by(User.id, User.nome_completo).order_by(
            func.sum(SessaoEstudo.tempo_ativo).desc()
        ).limit(10).all()

        posicao_atual = 1
        for i, (user_id, _, _) in enumerate(ranking, 1):
            if user_id == current_user.id:
                posicao_atual = i; break

        return jsonify({
            'ranking': [
                {'posicao': i, 'nome': nome, 'tempo_horas': tempo // 3600, 'e_usuario_atual': uid == current_user.id}
                for i, (uid, nome, tempo) in enumerate(ranking, 1)
            ],
            'posicao_usuario': posicao_atual
        })
    except Exception as e:
        current_app.logger.error(f"Erro ao obter ranking: {e}")
        return jsonify({'error': 'Erro ao obter ranking'}), 500

@estudo_bp.route('/api/sugerir_revisao')
@login_required
def sugerir_revisao():
    try:
        from app.models.estudo import Aula, ProgressoAula
        user_id = current_user.id
        agora = datetime.now()
        aulas_para_revisar = db.session.query(Aula).join(ProgressoAula).filter(
            ProgressoAula.user_id == user_id,
            ProgressoAula.concluida == True,
            ProgressoAula.data_conclusao < (agora - timedelta(days=7))
        ).order_by(ProgressoAula.data_conclusao).limit(5).all()

        sugestoes = []
        for aula in aulas_para_revisar:
            progresso = ProgressoAula.query.filter_by(user_id=user_id, aula_id=aula.id).first()
            dias_desde_conclusao = (agora - progresso.data_conclusao).days if progresso and progresso.data_conclusao else 999
            sugestoes.append({
                'aula_id': aula.id,
                'titulo': aula.titulo,
                'materia': aula.modulo.materia.nome,
                'modulo': aula.modulo.titulo,
                'dias_desde_conclusao': dias_desde_conclusao,
                'prioridade': min(dias_desde_conclusao / 7, 1.0)
            })

        return jsonify({'sugestoes': sorted(sugestoes, key=lambda x: x['prioridade'], reverse=True)})
    except Exception as e:
        current_app.logger.error(f"Erro ao sugerir revisão: {e}")
        return jsonify({'error': 'Erro ao sugerir revisão'}), 500

# ==========================
# ADMIN – Painel geral
# ==========================
@estudo_bp.route('/admin')
@login_required
def admin():
    if not _is_admin():
        flash('Acesso negado.', 'danger'); return redirect(url_for('main.index'))
    try:
        from app.models.estudo import Materia
        from app.models.user import User
        materias = Materia.query.order_by(Materia.ordem).all()
        total_usuarios = User.query.count()
        usuarios_ativos = User.query.filter_by(is_active=True).count()
        return render_template('estudo/admin/index.html', materias=materias, usuarios_ativos=usuarios_ativos)
    except Exception as e:
        current_app.logger.error(f"Erro no painel admin: {e}")
        flash('Erro ao carregar painel administrativo.', 'error')
        return redirect(url_for('dashboard.index'))

# ==========================
# ADMIN – Matérias / Módulos / Aulas
# ==========================
@estudo_bp.route('/admin/materia/nova', methods=['GET', 'POST'])
@login_required
def nova_materia():
    """
    Cria nova matéria.
    CORRIGIDO: Agora cria matérias como ATIVAS por padrão
    """
    if not _is_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))

    # secao_id pode vir por GET (?secao_id=) ou por POST (campo hidden)
    secao_id = request.args.get('secao_id', type=int) or request.form.get('secao_id', type=int)

    if request.method == 'POST':
        try:
            from app.models.estudo import Materia

            nome = request.form.get('nome', '').strip()
            if not nome:
                flash('O nome da matéria é obrigatório.', 'error')
                return render_template('estudo/admin/materia_form.html', secao_id=secao_id)

            # Validar duplicata no escopo correto
            query = Materia.query.filter(Materia.nome == nome)
            if secao_id:
                query = query.filter(Materia.secao_id == secao_id)
            else:
                query = query.filter(Materia.secao_id.is_(None))
            
            if query.first():
                escopo = f'seção' if secao_id else 'núcleo global'
                flash(f'Já existe uma matéria com este nome no {escopo}.', 'error')
                return render_template('estudo/admin/materia_form.html', secao_id=secao_id)

            # Criar matéria - CORRIGIDO: SEMPRE ATIVA POR PADRÃO
            materia = Materia(
                nome=nome,
                descricao=request.form.get('descricao', '').strip() or None,
                icone=request.form.get('icone', '📖').strip(),
                cor=request.form.get('cor', '#00b4d8').strip(),
                ordem=int(request.form.get('ordem', 0)),
                ativa=True,  # 🔥 SEMPRE ATIVA POR PADRÃO
                secao_id=secao_id  # NULL = núcleo global, valor = seção específica
            )

            # Upload opcional de capa
            if 'capa_imagem' in request.files:
                file = request.files['capa_imagem']
                if file and file.filename != '' and allowed_image(file.filename):
                    materia.capa_url = salvar_imagem_materia(file)

            db.session.add(materia)
            db.session.commit()

            escopo_msg = f' na seção' if secao_id else ' no núcleo global'
            flash(f'Matéria "{materia.nome}" criada com sucesso{escopo_msg}!', 'success')

            # Redirecionar para local apropriado
            if secao_id:
                return redirect(url_for('estudo.admin_secao_materias', secao_id=secao_id))
            else:
                return redirect(url_for('estudo.admin'))

        except ValueError:
            flash('Erro nos dados fornecidos. Verifique os valores numéricos.', 'error')
        except Exception as e:
            current_app.logger.error(f"Erro ao criar matéria: {e}")
            db.session.rollback()
            flash('Erro interno ao criar matéria.', 'error')

    # GET: renderizar formulário
    return render_template('estudo/admin/materia_form.html', secao_id=secao_id)



# ✅ NOVA ROTA: criar matéria já dentro de uma seção (endpoint usado no template)
@estudo_bp.route('/admin/secoes/<int:secao_id>/materias/nova', methods=['GET', 'POST'])
@login_required
def admin_nova_materia_secao(secao_id):
    if not _is_admin():
        flash('Acesso negado.', 'danger'); return redirect(url_for('main.index'))

    from app.models.estudo import Secao, Materia
    s = Secao.query.get_or_404(secao_id)

    if request.method == 'POST':
        try:
            nome = (request.form.get('nome') or '').strip()
            if not nome:
                flash('Informe o nome da matéria.', 'warning')
                return render_template('estudo/admin/materia_form.html', secao=s, materia=None, secao_id=secao_id)

            # Evitar duplicado dentro da mesma seção
            existe = Materia.query.filter(Materia.nome == nome, Materia.secao_id == secao_id).first()
            if existe:
                flash('Já existe uma matéria com este nome nesta seção.', 'warning')
                return render_template('estudo/admin/materia_form.html', secao=s, materia=None, secao_id=secao_id)

            m = Materia(
                nome=nome,
                descricao=(request.form.get('descricao') or '').strip(),
                icone=(request.form.get('icone') or '📖').strip(),
                cor=(request.form.get('cor') or '#00b4d8').strip(),
                capa_url=(request.form.get('capa_url') or '').strip(),
                ordem=int(request.form.get('ordem') or 0),
                ativa=True if request.form.get('ativa') in ('on','true','1') else False,
                secao_id=secao_id  # 👈 essencial: propriedade da seção (exclusividade)
            )

            # Upload opcional de capa
            if 'capa_imagem' in request.files:
                file = request.files['capa_imagem']
                if file and file.filename != '' and allowed_image(file.filename):
                    m.capa_url = salvar_imagem_materia(file)

            db.session.add(m)
            db.session.commit()
            flash('Matéria criada na seção com sucesso.', 'success')
            return redirect(url_for('estudo.admin_secao_materias', secao_id=secao_id))
        except Exception as e:
            current_app.logger.error(f"Erro ao criar matéria na seção: {e}")
            db.session.rollback()
            flash('Erro ao criar matéria na seção.', 'error')

    # GET
    return render_template('estudo/admin/materia_form.html', secao=s, materia=None, secao_id=secao_id)

@estudo_bp.route('/admin/materia/editar/<int:materia_id>', methods=['GET', 'POST'])
@login_required
def editar_materia(materia_id):
    if not _is_admin():
        flash('Acesso negado.', 'danger'); return redirect(url_for('main.index'))

    from app.models.estudo import Materia
    materia = Materia.query.get_or_404(materia_id)

    if request.method == 'POST':
        try:
            nome = request.form['nome']
            materia_existente = Materia.query.filter(Materia.nome == nome, Materia.id != materia.id).first()
            if materia_existente:
                flash('Uma matéria com este nome já existe!', 'error')
                return render_template('estudo/admin/materia_form.html', materia=materia)

            materia.nome = nome
            materia.descricao = request.form.get('descricao')
            materia.icone = request.form.get('icone', '📖')
            materia.cor = request.form.get('cor', '#00b4d8')
            materia.ordem = request.form.get('ordem', 0, type=int)

            if 'capa_imagem' in request.files:
                file = request.files['capa_imagem']
                if file and file.filename and allowed_image(file.filename):
                    if materia.capa_url:
                        deletar_imagem_materia(materia.capa_url)
                    materia.capa_url = salvar_imagem_materia(file)

            db.session.commit()
            flash(f'Matéria "{materia.nome}" atualizada com sucesso!', 'success')
            return redirect(url_for('estudo.admin'))
        except Exception as e:
            current_app.logger.error(f"Erro ao atualizar matéria: {e}")
            db.session.rollback()
            flash(f'Erro ao atualizar matéria: {str(e)}', 'error')

    return render_template('estudo/admin/materia_form.html', materia=materia)



@estudo_bp.route('/admin/materia/<int:materia_id>/toggle', methods=['POST'])
@login_required
def toggle_materia_ativa(materia_id):
    """Nova rota para ativar/desativar matéria"""
    if not _is_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        from app.models.estudo import Materia
        materia = Materia.query.get_or_404(materia_id)
        
        # Alternar estado
        materia.ativa = not materia.ativa
        db.session.commit()
        
        status = "ativada" if materia.ativa else "desativada"
        flash(f'Matéria "{materia.nome}" {status} com sucesso!', 'success')
        
        # Redirecionar de volta
        if materia.secao_id:
            return redirect(url_for('estudo.admin_secao_materias', secao_id=materia.secao_id))
        else:
            return redirect(url_for('estudo.admin'))
            
    except Exception as e:
        current_app.logger.error(f"Erro ao alterar status da matéria {materia_id}: {e}")
        db.session.rollback()
        flash('Erro ao alterar status da matéria.', 'error')
        return redirect(url_for('estudo.admin'))


@estudo_bp.route('/admin/modulo/novo/<int:materia_id>', methods=['GET', 'POST'])
@login_required
def novo_modulo(materia_id):
    if not _is_admin():
        flash('Acesso negado.', 'danger'); return redirect(url_for('main.index'))
    try:
        from app.models.estudo import Materia, Modulo
        materia = Materia.query.get_or_404(materia_id)
        if request.method == 'POST':
            modulo = Modulo(
                titulo=request.form['titulo'],
                descricao=request.form.get('descricao'),
                materia_id=materia_id,
                ordem=request.form.get('ordem', 0, type=int),
                duracao_estimada=request.form.get('duracao_estimada', type=int),
                dificuldade=request.form.get('dificuldade', 'medio'),
                ativo=True
            )
            db.session.add(modulo); db.session.commit()
            flash('Módulo criado com sucesso!', 'success')
            return redirect(url_for('estudo.materia', materia_id=materia_id))
        return render_template('estudo/admin/modulo_form.html', materia=materia)
    except Exception as e:
        current_app.logger.error(f"Erro ao criar módulo: {e}")
        db.session.rollback()
        flash('Erro ao criar módulo.', 'error')
        return redirect(url_for('estudo.admin'))

@estudo_bp.route('/admin/aula/nova/<int:modulo_id>', methods=['GET', 'POST'])
@login_required
def nova_aula(modulo_id):
    if not _is_admin():
        flash('Acesso negado.', 'danger'); return redirect(url_for('main.index'))
    try:
        from app.models.estudo import Modulo, Aula, MaterialAula
        modulo = Modulo.query.get_or_404(modulo_id)
        if request.method == 'POST':
            aula = Aula(
                titulo=request.form['titulo'],
                descricao=request.form.get('descricao'),
                conteudo=request.form.get('conteudo'),
                modulo_id=modulo_id,
                ordem=request.form.get('ordem', 0, type=int),
                duracao_estimada=request.form.get('duracao_estimada', type=int),
                tipo=request.form.get('tipo', 'texto'),
                url_video=request.form.get('url_video'),
                ativa=True
            )
            db.session.add(aula)
            db.session.flush()  # para ter ID

            # PDF da aula (tipo pdf)
            if aula.tipo == 'pdf' and 'pdf_file' in request.files:
                pdf = request.files['pdf_file']
                if pdf and pdf.filename and allowed_file(pdf.filename):
                    filename = secure_filename(pdf.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                    filename = timestamp + filename
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                    pdf.save(os.path.join(UPLOAD_FOLDER, filename))
                    aula.url_pdf = f'uploads/materiais/{filename}'

            # Materiais complementares
            if 'materiais' in request.files:
                for file in request.files.getlist('materiais'):
                    if file and file.filename and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                        filename = timestamp + filename
                        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                        file.save(os.path.join(UPLOAD_FOLDER, filename))
                        material = MaterialAula(
                            nome=file.filename,
                            arquivo=f'uploads/materiais/{filename}',
                            tipo=filename.rsplit('.', 1)[1].lower(),
                            aula_id=aula.id
                        )
                        db.session.add(material)

            db.session.commit()
            flash('Aula criada com sucesso!', 'success')
            return redirect(url_for('estudo.modulo', modulo_id=modulo_id))
        return render_template('estudo/admin/aula_form.html', modulo=modulo)
    except Exception as e:
        current_app.logger.error(f"Erro ao criar aula: {e}")
        import traceback; current_app.logger.error(traceback.format_exc())
        db.session.rollback()
        flash(f'Erro ao criar aula: {str(e)}', 'error')
        return redirect(url_for('estudo.admin'))

def deletar_arquivos_aula(aula):
    """Deleta arquivos físicos de uma aula."""
    try:
        if aula.url_pdf:
            pdf_path = os.path.join(current_app.root_path, 'static', aula.url_pdf)
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
                current_app.logger.info(f"PDF da aula deletado: {pdf_path}")
        for material in aula.materiais:
            if material.arquivo:
                material_path = os.path.join(current_app.root_path, 'static', material.arquivo)
                if os.path.exists(material_path):
                    os.remove(material_path)
                    current_app.logger.info(f"Material deletado: {material_path}")
    except Exception as e:
        current_app.logger.error(f"Erro ao deletar arquivos da aula {aula.id}: {e}")

@estudo_bp.route('/admin/modulo/excluir/<int:modulo_id>', methods=['POST'])
@login_required
def excluir_modulo(modulo_id):
    if not _is_admin():
        flash('Acesso negado.', 'danger'); return redirect(url_for('main.index'))
    try:
        from app.models.estudo import Modulo, Aula, MaterialAula, ProgressoAula, SessaoEstudo
        modulo = Modulo.query.get_or_404(modulo_id)
        materia_id = modulo.materia_id
        for aula in modulo.aulas:
            deletar_arquivos_aula(aula)
        for aula in modulo.aulas:
            SessaoEstudo.query.filter_by(aula_id=aula.id).delete()
            ProgressoAula.query.filter_by(aula_id=aula.id).delete()
            MaterialAula.query.filter_by(aula_id=aula.id).delete()
        db.session.delete(modulo)
        db.session.commit()
        flash(f'Módulo "{modulo.titulo}" excluído com sucesso!', 'success')
    except Exception as e:
        current_app.logger.error(f"Erro ao excluir módulo {modulo_id}: {e}")
        import traceback; current_app.logger.error(traceback.format_exc())
        db.session.rollback()
        flash('Erro ao excluir módulo. Tente novamente.', 'error')
        materia_id = modulo.materia_id if 'modulo' in locals() else None
    return redirect(url_for('estudo.materia', materia_id=materia_id) if materia_id else url_for('estudo.admin'))

@estudo_bp.route('/admin/aula/excluir/<int:aula_id>', methods=['POST'])
@login_required
def excluir_aula(aula_id):
    if not _is_admin():
        flash('Acesso negado.', 'danger'); return redirect(url_for('main.index'))
    try:
        from app.models.estudo import Aula, MaterialAula, ProgressoAula, SessaoEstudo
        aula = Aula.query.get_or_404(aula_id)
        modulo_id = aula.modulo_id
        deletar_arquivos_aula(aula)
        SessaoEstudo.query.filter_by(aula_id=aula_id).delete()
        ProgressoAula.query.filter_by(aula_id=aula_id).delete()
        MaterialAula.query.filter_by(aula_id=aula_id).delete()
        db.session.delete(aula); db.session.commit()
        flash(f'Aula "{aula.titulo}" excluída com sucesso!', 'success')
    except Exception as e:
        current_app.logger.error(f"Erro ao excluir aula {aula_id}: {e}")
        import traceback; current_app.logger.error(traceback.format_exc())
        db.session.rollback()
        flash('Erro ao excluir aula. Tente novamente.', 'error')
        modulo_id = aula.modulo_id if 'aula' in locals() else None
    return redirect(url_for('estudo.modulo', modulo_id=modulo_id) if modulo_id else url_for('estudo.admin'))


@estudo_bp.route('/admin/modulo/editar/<int:modulo_id>', methods=['GET', 'POST'])
@login_required
def editar_modulo(modulo_id):
    if not _is_admin():
        flash('Acesso negado.', 'danger'); return redirect(url_for('main.index'))
    try:
        from app.models.estudo import Modulo
        modulo = Modulo.query.get_or_404(modulo_id)
        materia = modulo.materia
        if request.method == 'POST':
            titulo = request.form['titulo']
            modulo_existente = Modulo.query.filter(
                Modulo.titulo == titulo, Modulo.materia_id == materia.id, Modulo.id != modulo.id
            ).first()
            if modulo_existente:
                flash('Um módulo com este título já existe nesta matéria!', 'error')
                return render_template('estudo/admin/modulo_form.html', modulo=modulo, materia=materia)

            modulo.titulo = titulo
            modulo.descricao = request.form.get('descricao')
            modulo.ordem = request.form.get('ordem', 0, type=int)
            modulo.duracao_estimada = request.form.get('duracao_estimada', type=int)
            modulo.dificuldade = request.form.get('dificuldade', 'medio')
            db.session.commit()
            flash(f'Módulo "{modulo.titulo}" atualizado com sucesso!', 'success')
            return redirect(url_for('estudo.materia', materia_id=materia.id))
        return render_template('estudo/admin/modulo_form.html', modulo=modulo, materia=materia)
    except Exception as e:
        current_app.logger.error(f"Erro ao editar módulo: {e}")
        db.session.rollback()
        flash('Erro ao editar módulo.', 'error')
        return redirect(url_for('estudo.admin'))

@estudo_bp.route('/admin/aula/editar/<int:aula_id>', methods=['GET', 'POST'])
@login_required
def editar_aula(aula_id):
    if not _is_admin():
        flash('Acesso negado.', 'danger'); return redirect(url_for('main.index'))
    try:
        from app.models.estudo import Aula, MaterialAula
        aula = Aula.query.get_or_404(aula_id)
        modulo = aula.modulo
        if request.method == 'POST':
            titulo = request.form['titulo']
            aula_existente = Aula.query.filter(
                Aula.titulo == titulo, Aula.modulo_id == modulo.id, Aula.id != aula.id
            ).first()
            if aula_existente:
                flash('Uma aula com este título já existe neste módulo!', 'error')
                return render_template('estudo/admin/aula_form.html', aula=aula, modulo=modulo)

            aula.titulo = titulo
            aula.descricao = request.form.get('descricao')
            aula.conteudo = request.form.get('conteudo')
            aula.ordem = request.form.get('ordem', 0, type=int)
            aula.duracao_estimada = request.form.get('duracao_estimada', type=int)
            aula.tipo = request.form.get('tipo', 'texto')
            aula.url_video = request.form.get('url_video')

            # PDF
            if aula.tipo == 'pdf' and 'pdf_file' in request.files:
                pdf = request.files['pdf_file']
                if pdf and pdf.filename and allowed_file(pdf.filename):
                    if aula.url_pdf:
                        old_pdf_path = os.path.join(current_app.root_path, 'static', aula.url_pdf)
                        if os.path.exists(old_pdf_path):
                            os.remove(old_pdf_path)
                    filename = secure_filename(pdf.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                    filename = timestamp + filename
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                    pdf.save(os.path.join(UPLOAD_FOLDER, filename))
                    aula.url_pdf = f'uploads/materiais/{filename}'

            if aula.tipo != 'pdf' and aula.url_pdf:
                old_pdf_path = os.path.join(current_app.root_path, 'static', aula.url_pdf)
                if os.path.exists(old_pdf_path):
                    os.remove(old_pdf_path)
                aula.url_pdf = None

            if aula.tipo != 'video':
                aula.url_video = None

            # Materiais complementares
            if 'materiais' in request.files:
                for file in request.files.getlist('materiais'):
                    if file and file.filename and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                        filename = timestamp + filename
                        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                        file.save(os.path.join(UPLOAD_FOLDER, filename))
                        material = MaterialAula(
                            nome=file.filename,
                            arquivo=f'uploads/materiais/{filename}',
                            tipo=filename.rsplit('.', 1)[1].lower(),
                            aula_id=aula.id
                        )
                        db.session.add(material)

            db.session.commit()
            flash(f'Aula "{aula.titulo}" atualizada com sucesso!', 'success')
            return redirect(url_for('estudo.modulo', modulo_id=modulo.id))
        return render_template('estudo/admin/aula_form.html', aula=aula, modulo=modulo)
    except Exception as e:
        current_app.logger.error(f"Erro ao editar aula: {e}")
        import traceback; current_app.logger.error(traceback.format_exc())
        db.session.rollback()
        flash('Erro ao editar aula.', 'error')
        return redirect(url_for('estudo.admin'))


# ==========================
# ADMIN – Seções independentes (OTIMIZADO)
# ==========================
@estudo_bp.route('/admin/secoes')
@login_required
def admin_secoes():
    """Lista todas as seções com estatísticas"""
    if not _is_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    from app.models.estudo import Secao
    secoes = Secao.query.order_by(Secao.ordem, Secao.id).all()
    
    # Calcular estatísticas globais
    total_secoes = len(secoes)
    secoes_ativas = sum(1 for s in secoes if s.ativo)
    total_materias_secoes = sum(s.total_materias for s in secoes)
    
    return render_template('estudo/admin/secoes.html', 
                         secoes=secoes,
                         estatisticas={
                             'total_secoes': total_secoes,
                             'secoes_ativas': secoes_ativas,
                             'total_materias_secoes': total_materias_secoes
                         })


@estudo_bp.route('/admin/secao/nova', methods=['GET', 'POST'])
@login_required
def nova_secao():
    """Cria nova seção"""
    if not _is_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    from app.models.estudo import Secao
    
    if request.method == 'POST':
        try:
            # Validar dados obrigatórios
            titulo = request.form.get('titulo', '').strip()
            if not titulo:
                flash('O título da seção é obrigatório.', 'error')
                return render_template('estudo/admin/secao_form.html')
            
            # Verificar se já existe seção com mesmo título
            secao_existente = Secao.query.filter(Secao.titulo == titulo).first()
            if secao_existente:
                flash('Já existe uma seção com este título.', 'error')
                return render_template('estudo/admin/secao_form.html')
            
            # Criar nova seção
            secao = Secao(
                titulo=titulo,
                subtitulo=request.form.get('subtitulo', '').strip() or None,
                descricao=request.form.get('descricao', '').strip() or None,
                icone=request.form.get('icone', '🧩').strip(),
                cor=request.form.get('cor', '#00b4d8').strip(),
                grid_cols=int(request.form.get('grid_cols', 4)),
                ordem=int(request.form.get('ordem', 0)),
                ativo=bool(request.form.get('ativo'))
            )
            
            db.session.add(secao)
            db.session.commit()
            
            flash(f'Seção "{secao.titulo}" criada com sucesso!', 'success')
            return redirect(url_for('estudo.admin_secoes'))
            
        except ValueError as e:
            flash('Erro nos dados fornecidos. Verifique os valores numéricos.', 'error')
            return render_template('estudo/admin/secao_form.html')
        except Exception as e:
            current_app.logger.error(f"Erro ao criar seção: {e}")
            db.session.rollback()
            flash('Erro interno ao criar seção.', 'error')
            return render_template('estudo/admin/secao_form.html')
    
    # GET: exibir formulário
    return render_template('estudo/admin/secao_form.html')


@estudo_bp.route('/admin/secao/<int:secao_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_secao(secao_id):
    """Edita seção existente"""
    if not _is_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    from app.models.estudo import Secao
    secao = Secao.query.get_or_404(secao_id)
    
    if request.method == 'POST':
        try:
            # Validar título obrigatório
            titulo = request.form.get('titulo', '').strip()
            if not titulo:
                flash('O título da seção é obrigatório.', 'error')
                return render_template('estudo/admin/secao_form.html', secao=secao)
            
            # Verificar duplicatas (exceto a própria seção)
            secao_existente = Secao.query.filter(
                Secao.titulo == titulo,
                Secao.id != secao.id
            ).first()
            if secao_existente:
                flash('Já existe outra seção com este título.', 'error')
                return render_template('estudo/admin/secao_form.html', secao=secao)
            
            # Atualizar dados
            secao.titulo = titulo
            secao.subtitulo = request.form.get('subtitulo', '').strip() or None
            secao.descricao = request.form.get('descricao', '').strip() or None
            secao.icone = request.form.get('icone', '🧩').strip()
            secao.cor = request.form.get('cor', '#00b4d8').strip()
            secao.grid_cols = int(request.form.get('grid_cols', 4))
            secao.ordem = int(request.form.get('ordem', 0))
            secao.ativo = bool(request.form.get('ativo'))
            
            db.session.commit()
            
            flash(f'Seção "{secao.titulo}" atualizada com sucesso!', 'success')
            return redirect(url_for('estudo.admin_secoes'))
            
        except ValueError:
            flash('Erro nos dados fornecidos. Verifique os valores numéricos.', 'error')
            return render_template('estudo/admin/secao_form.html', secao=secao)
        except Exception as e:
            current_app.logger.error(f"Erro ao editar seção {secao_id}: {e}")
            db.session.rollback()
            flash('Erro interno ao editar seção.', 'error')
    
    # GET: exibir formulário preenchido
    return render_template('estudo/admin/secao_form.html', secao=secao)

@estudo_bp.route('/admin/secao/<int:secao_id>/excluir', methods=['POST'])
@login_required
def excluir_secao(secao_id):
    """Exclui seção e todas suas matérias"""
    if not _is_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        from app.models.estudo import Secao, Materia, Modulo, Aula
        secao = Secao.query.get_or_404(secao_id)
        
        # Contar itens que serão excluídos
        materias_count = secao.materias.count()
        titulo_secao = secao.titulo
        
        # Excluir em cascata: Seção -> Matérias -> Módulos -> Aulas
        # (O SQLAlchemy fará a cascata automática se configurado)
        db.session.delete(secao)
        db.session.commit()
        
        flash(f'Seção "{titulo_secao}" e suas {materias_count} matérias foram excluídas com sucesso.', 'success')
        
    except Exception as e:
        current_app.logger.error(f"Erro ao excluir seção {secao_id}: {e}")
        db.session.rollback()
        flash('Erro ao excluir seção. Tente novamente.', 'error')
    
    return redirect(url_for('estudo.admin_secoes'))


@estudo_bp.route('/admin/secao/<int:secao_id>/materias')
@login_required
def admin_secao_materias(secao_id):
    """Lista matérias exclusivas de uma seção"""
    if not _is_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    from app.models.estudo import Secao, Materia
    secao = Secao.query.get_or_404(secao_id)
    
    # Buscar apenas matérias EXCLUSIVAS desta seção
    materias = secao.get_materias_ativas()
    
    # Calcular estatísticas da seção
    estatisticas = {
        'total_materias': secao.total_materias,
        'total_modulos': secao.total_modulos,
        'total_aulas': secao.total_aulas
    }
    
    return render_template('estudo/admin/secao_materias.html', 
                         secao=secao, 
                         materias=materias,
                         estatisticas=estatisticas)


# ✅ ROTA OTIMIZADA: criar matéria exclusiva de uma seção
@estudo_bp.route('/admin/secao/<int:secao_id>/materia/nova', methods=['GET', 'POST'])
@login_required
def admin_nova_materia_secao(secao_id):
    """Cria matéria exclusiva para uma seção específica"""
    if not _is_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))

    from app.models.estudo import Secao, Materia
    secao = Secao.query.get_or_404(secao_id)

    if request.method == 'POST':
        try:
            nome = request.form.get('nome', '').strip()
            if not nome:
                flash('O nome da matéria é obrigatório.', 'error')
                return render_template('estudo/admin/materia_form.html', secao=secao, secao_id=secao_id)

            # Verificar duplicata DENTRO da mesma seção
            materia_existente = Materia.query.filter(
                Materia.nome == nome,
                Materia.secao_id == secao_id
            ).first()
            
            if materia_existente:
                flash('Já existe uma matéria com este nome nesta seção.', 'error')
                return render_template('estudo/admin/materia_form.html', secao=secao, secao_id=secao_id)

            # Criar matéria EXCLUSIVA da seção
            materia = Materia(
                nome=nome,
                descricao=request.form.get('descricao', '').strip() or None,
                icone=request.form.get('icone', '📖').strip(),
                cor=request.form.get('cor', '#00b4d8').strip(),
                ordem=int(request.form.get('ordem', 0)),
                ativa=True,
                secao_id=secao_id  # 🔑 EXCLUSIVIDADE: matéria pertence SÓ a esta seção
            )

            # Upload opcional de capa
            if 'capa_imagem' in request.files:
                file = request.files['capa_imagem']
                if file and file.filename != '' and allowed_image(file.filename):
                    materia.capa_url = salvar_imagem_materia(file)

            db.session.add(materia)
            db.session.commit()

            flash(f'Matéria "{materia.nome}" criada com sucesso na seção "{secao.titulo}"!', 'success')
            return redirect(url_for('estudo.admin_secao_materias', secao_id=secao_id))

        except ValueError:
            flash('Erro nos dados fornecidos. Verifique os valores numéricos.', 'error')
        except Exception as e:
            current_app.logger.error(f"Erro ao criar matéria na seção {secao_id}: {e}")
            db.session.rollback()
            flash('Erro interno ao criar matéria.', 'error')

    # GET: exibir formulário
    return render_template('estudo/admin/materia_form.html', secao=secao, secao_id=secao_id)


# ✅ ATUALIZAR ROTA DE NOVA MATÉRIA para suportar seções
@estudo_bp.route('/admin/materia/nova', methods=['GET', 'POST'])
@login_required
def nova_materia():
    """
    Cria nova matéria.
    - Se secao_id na URL/form = matéria exclusiva da seção
    - Sem secao_id = matéria do núcleo global
    """
    if not _is_admin():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))

    # secao_id pode vir por GET (?secao_id=) ou por POST (campo hidden)
    secao_id = request.args.get('secao_id', type=int) or request.form.get('secao_id', type=int)
    secao = None
    
    if secao_id:
        from app.models.estudo import Secao
        secao = Secao.query.get_or_404(secao_id)

    if request.method == 'POST':
        try:
            from app.models.estudo import Materia

            nome = request.form.get('nome', '').strip()
            if not nome:
                flash('O nome da matéria é obrigatório.', 'error')
                return render_template('estudo/admin/materia_form.html', secao=secao, secao_id=secao_id)

            # Validar duplicata no escopo correto
            query = Materia.query.filter(Materia.nome == nome)
            if secao_id:
                query = query.filter(Materia.secao_id == secao_id)
            else:
                query = query.filter(Materia.secao_id.is_(None))
            
            if query.first():
                escopo = f'seção "{secao.titulo}"' if secao else 'núcleo global'
                flash(f'Já existe uma matéria com este nome no {escopo}.', 'error')
                return render_template('estudo/admin/materia_form.html', secao=secao, secao_id=secao_id)

            # Criar matéria
            materia = Materia(
                nome=nome,
                descricao=request.form.get('descricao', '').strip() or None,
                icone=request.form.get('icone', '📖').strip(),
                cor=request.form.get('cor', '#00b4d8').strip(),
                ordem=int(request.form.get('ordem', 0)),
                ativa=True,
                secao_id=secao_id  # NULL = núcleo global, valor = seção específica
            )

            # Upload opcional de capa
            if 'capa_imagem' in request.files:
                file = request.files['capa_imagem']
                if file and file.filename != '' and allowed_image(file.filename):
                    materia.capa_url = salvar_imagem_materia(file)

            db.session.add(materia)
            db.session.commit()

            escopo_msg = f' na seção "{secao.titulo}"' if secao else ' no núcleo global'
            flash(f'Matéria "{materia.nome}" criada com sucesso{escopo_msg}!', 'success')

            # Redirecionar para local apropriado
            if secao_id:
                return redirect(url_for('estudo.admin_secao_materias', secao_id=secao_id))
            else:
                return redirect(url_for('estudo.admin'))

        except ValueError:
            flash('Erro nos dados fornecidos. Verifique os valores numéricos.', 'error')
        except Exception as e:
            current_app.logger.error(f"Erro ao criar matéria: {e}")
            db.session.rollback()
            flash('Erro interno ao criar matéria.', 'error')

    # GET: renderizar formulário
    return render_template('estudo/admin/materia_form.html', secao=secao, secao_id=secao_id)
