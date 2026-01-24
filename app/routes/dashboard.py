# app/routes/dashboard.py
from flask import Blueprint, render_template, jsonify, request, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.models.user import User
from sqlalchemy import func, desc
from app import db

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    """Dashboard principal com correções e suporte a seções (owner e vínculo)."""

    # Reset mensal de diamantes (mantido)
    try:
        from app.services.xp_service import XpService
        XpService.verificar_e_resetar_diamantes_mensais(current_user)
    except ImportError:
        pass

    try:
        # 1) Verificar tabelas existentes
        inspector = db.inspect(db.engine)
        existing_tables = set(inspector.get_table_names())

        materias = []
        aulas_em_andamento = []

        # Containers de seções
        secoes_materias = []   # legado puro (não usamos, mas mantemos para template)
        secoes_render = []     # cards prontos para render

        # 2) Matérias do núcleo (apenas as que NÃO pertencem a nenhuma seção)
        if 'materia' in existing_tables:
            try:
                from app.models.estudo import Materia, Modulo, Aula, ProgressoAula

                materias = (
                    Materia.query
                    .filter(Materia.ativa == True, Materia.secao_id.is_(None))
                    .order_by(Materia.ordem, Materia.id)
                    .all()
                )

                for materia in materias:
                    try:
                        materia.progresso_usuario_calc = calcular_progresso_materia_safe(
                            materia.id, current_user.id
                        )
                    except Exception as e:
                        print(f"Erro ao calcular progresso da matéria {materia.id}: {e}")
                        materia.progresso_usuario_calc = 0

                if 'progresso_aula' in existing_tables:
                    aulas_em_andamento = obter_aulas_em_andamento_safe(current_user.id)

            except ImportError as e:
                print(f"Erro ao importar modelos de estudo: {e}")

        # 3) Seções no dashboard — mostrar matérias da própria seção (owner) e, se houver, vínculos por pivô
        try:
            if 'secao' in existing_tables and 'materia' in existing_tables:
                from app.models.estudo import Secao, Materia as MateriaModel

                # Suporte ao pivô legado (se existir)
                has_pivo = 'secao_materia' in existing_tables
                if has_pivo:
                    from app.models.estudo import SecaoMateria

                secoes = (
                    Secao.query
                    .filter_by(ativo=True)
                    .order_by(Secao.ordem, Secao.id)
                    .all()
                )

                # zera/garante o container usado no template
                secoes_render = []

                for s in secoes:
                    itens_cards = []
                    ja_adicionados = set()  # evita duplicatas por id de matéria

                    # a) matérias "donas" da seção (exclusivas)
                    materias_own = (
                        MateriaModel.query
                        .filter(
                            MateriaModel.ativa == True,
                            MateriaModel.secao_id == s.id
                        )
                        .order_by(MateriaModel.ordem, MateriaModel.id)
                        .all()
                    )
                    for m in materias_own:
                        ja_adicionados.add(m.id)
                        prog = calcular_progresso_materia_safe(m.id, current_user.id)
                        img_url = (
                            (m.capa_url and f"static/{m.capa_url}")
                            or url_for('static', filename='images/covers/placeholder-subject.jpg')
                        )
                        itens_cards.append({
                            'tipo': 'materia',
                            'titulo': m.nome,
                            'sub': f'{m.modulos.count()} módulos',
                            'progresso': prog,
                            'href': url_for('estudo.materia', materia_id=m.id),
                            'img': img_url,
                            'badge': None
                        })

                    # b) matérias vinculadas via pivô (legado), se existir a tabela
                    if has_pivo:
                        links = (
                            SecaoMateria.query
                            .filter_by(secao_id=s.id, ativo=True)
                            .join(MateriaModel, MateriaModel.id == SecaoMateria.materia_id)
                            .order_by(SecaoMateria.ordem, SecaoMateria.id)
                            .all()
                        )
                        for link in links:
                            m = link.materia
                            if not m or not m.ativa or m.id in ja_adicionados:
                                continue
                            ja_adicionados.add(m.id)
                            prog = calcular_progresso_materia_safe(m.id, current_user.id)
                            img_url = (
                                (link.imagem_url and link.imagem_url.strip())
                                or (m.capa_url and f"static/{m.capa_url}")
                                or url_for('static', filename='images/covers/placeholder-subject.jpg')
                            )
                            titulo = link.titulo_override or m.nome
                            itens_cards.append({
                                'tipo': 'materia',
                                'titulo': titulo,
                                'sub': f'{m.modulos.count()} módulos',
                                'progresso': prog,
                                'href': url_for('estudo.materia', materia_id=m.id),
                                'img': img_url,
                                'badge': link.badge
                            })

                    # ✅ SEMPRE adiciona a seção (mesmo sem itens) para o cabeçalho aparecer
                    secoes_render.append({
                        'titulo': s.titulo,
                        'icone': s.icone or '🧩',
                        'itens': itens_cards
                    })

        except Exception as e:
            print(f"Erro ao montar seções no dashboard: {e}")



        # 4) Estatísticas do usuário
        stats = calcular_estatisticas_usuario_safe(current_user.id)

        # 5) Acesso rápido
        stats_extras = {
            'ultima_nota_simulado': obter_ultima_nota_simulado_safe(current_user.id),
            'duvidas_respondidas': obter_duvidas_respondidas_safe(current_user.id),
            'posicao_ranking': obter_posicao_ranking_safe(current_user.id)
        }

        # 6) Conquistas recentes
        conquistas_recentes = verificar_conquistas_safe(current_user.id)

        return render_template(
            'dashboard.html',
            materias=materias,
            aulas_em_andamento=aulas_em_andamento,
            conquistas_recentes=conquistas_recentes,
            secoes_materias=secoes_materias,  # legado (não usado)
            secoes_render=secoes_render,      # usado no template
            **stats,
            **stats_extras
        )

    except Exception as e:
        print(f"Erro no dashboard: {e}")
        return render_template(
            'dashboard.html',
            materias=[],
            aulas_em_andamento=[],
            conquistas_recentes=[],
            secoes_materias=[],
            secoes_render=[],
            tempo_estudo_hoje=0,
            aulas_concluidas=0,
            sequencia_dias=0,
            ultima_nota_simulado='N/A',
            duvidas_respondidas=0,
            posicao_ranking='N/A'
        )


def calcular_progresso_materia_safe(materia_id, user_id):
    """Calcula o progresso do usuário considerando apenas módulos visíveis na página de Matérias."""
    try:
        from app.models.estudo import Aula, Modulo, ProgressoAula

        # Se não existir a coluna 'visivel_na_materia', remova essa condição das duas queries.
        total_aulas = db.session.query(Aula).join(Modulo).filter(
            Modulo.materia_id == materia_id,
            Modulo.visivel_na_materia == True,
            Aula.ativa == True
        ).count()

        if total_aulas == 0:
            return 0

        aulas_concluidas = db.session.query(ProgressoAula).join(Aula).join(Modulo).filter(
            Modulo.materia_id == materia_id,
            Modulo.visivel_na_materia == True,
            ProgressoAula.user_id == user_id,
            ProgressoAula.concluida == True
        ).count()

        return (aulas_concluidas / total_aulas) * 100

    except Exception as e:
        print(f"Erro ao calcular progresso da matéria {materia_id}: {e}")
        return 0

def calcular_estatisticas_usuario_safe(user_id):
    """Calcula estatísticas gerais do usuário de forma segura"""
    hoje = datetime.now().date()

    try:
        if not hasattr(current_user, 'total_moedas') or current_user.total_moedas is None:
            current_user.total_moedas = 0
            db.session.commit()
    except:
        pass

    tempo_estudo_hoje = 0
    try:
        from app.models.estudo import SessaoEstudo
        sessoes_hoje = SessaoEstudo.query.filter(
            SessaoEstudo.user_id == user_id,
            func.date(SessaoEstudo.inicio) == hoje,
            SessaoEstudo.ativa == False
        ).all()
        tempo_estudo_hoje = sum(sessao.tempo_ativo for sessao in sessoes_hoje) // 60
    except Exception as e:
        print(f"Erro ao calcular tempo de estudo: {e}")
        tempo_estudo_hoje = 0

    aulas_concluidas = 0
    try:
        from app.models.estudo import ProgressoAula
        aulas_concluidas = ProgressoAula.query.filter_by(
            user_id=user_id,
            concluida=True
        ).count()
    except Exception as e:
        print(f"Erro ao calcular aulas concluídas: {e}")

    sequencia_dias = calcular_sequencia_estudo_safe(user_id)

    return {
        'tempo_estudo_hoje': tempo_estudo_hoje,
        'aulas_concluidas': aulas_concluidas,
        'sequencia_dias': sequencia_dias
    }


def obter_aulas_em_andamento_safe(user_id):
    """Obtém aulas que estão em andamento de forma segura"""
    try:
        from app.models.estudo import Aula, ProgressoAula, Modulo, Materia
        aulas = db.session.query(Aula).join(ProgressoAula).join(Modulo).join(Materia).filter(
            ProgressoAula.user_id == user_id,
            ProgressoAula.concluida == False,
            ProgressoAula.tempo_assistido > 0
        ).order_by(desc(ProgressoAula.ultima_atividade)).limit(4).all()

        for aula in aulas:
            progresso = ProgressoAula.query.filter_by(
                user_id=user_id,
                aula_id=aula.id
            ).first()
            if progresso and aula.duracao_estimada:
                tempo_total_segundos = aula.duracao_estimada * 60
                aula.progresso_usuario_calc = min((progresso.tempo_assistido / tempo_total_segundos) * 100, 100)
            else:
                aula.progresso_usuario_calc = 0

        return aulas
    except Exception as e:
        print(f"Erro ao obter aulas em andamento: {e}")
        return []


def calcular_sequencia_estudo_safe(user_id):
    """Calcula quantos dias consecutivos o usuário estudou de forma segura"""
    try:
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
    except Exception as e:
        print(f"Erro ao calcular sequência de estudo: {e}")
        return 0


def verificar_conquistas_safe(user_id):
    """Verifica se o usuário desbloqueou novas conquistas de forma segura"""
    conquistas = []
    try:
        from app.models.estudo import ProgressoAula
        primeira_aula = ProgressoAula.query.filter_by(
            user_id=user_id,
            concluida=True
        ).first()
        if primeira_aula:
            conquistas.append({
                'titulo': '🎓 Primeira Aula Concluída!',
                'descricao': 'Você concluiu sua primeira aula. Continue assim!',
                'tipo': 'primeira_aula'
            })

        sequencia = calcular_sequencia_estudo_safe(user_id)
        if sequencia >= 7:
            conquistas.append({
                'titulo': '🔥 Sequência de 7 Dias!',
                'descricao': f'Você estudou por {sequencia} dias consecutivos!',
                'tipo': 'sequencia_7'
            })

        user_moedas = getattr(current_user, 'total_moedas', 0) or 0
        if isinstance(user_moedas, int) and user_moedas >= 100:
            conquistas.append({
                'titulo': '💰 Primeiro Tesouro!',
                'descricao': 'Você alcançou 100 moedas!',
                'tipo': 'moedas_100'
            })
    except Exception as e:
        print(f"Erro ao verificar conquistas: {e}")

    return conquistas[:2]


def obter_ultima_nota_simulado_safe(user_id):
    """Obtém a última nota de simulado do usuário de forma segura"""
    try:
        from app.models.simulado import Simulado
        ultimo_simulado = (
            Simulado.query
            .filter_by(user_id=user_id, status='Concluído')
            .order_by(desc(Simulado.data_realizado))
            .first()
        )
        if ultimo_simulado and ultimo_simulado.nota_tri is not None:
            return f"{ultimo_simulado.nota_tri:.0f}"
        return "Sem dados"
    except Exception as e:
        print(f"Erro ao obter última nota de simulado: {e}")
        return "N/A"


def obter_duvidas_respondidas_safe(user_id):
    """Obtém o número de dúvidas respondidas pelo usuário de forma segura"""
    try:
        from app.models.helpzone import Resposta
        return Resposta.query.filter_by(user_id=user_id).count()
    except Exception as e:
        print(f"Erro ao obter dúvidas respondidas: {e}")
        return 0


def obter_posicao_ranking_safe(user_id):
    """Obtém a posição do usuário no ranking de forma segura"""
    try:
        user_moedas = getattr(current_user, 'total_moedas', 0)
        if not isinstance(user_moedas, (int, float)) or user_moedas is None:
            user_moedas = 0
        posicao = db.session.query(User.id).filter(
            User.total_moedas > user_moedas,
            User.total_moedas.isnot(None)
        ).count() + 1
        return f"#{posicao}"
    except Exception as e:
        print(f"Erro ao obter posição no ranking: {e}")
        return "N/A"


@dashboard_bp.route('/api/stats')
@login_required
def api_stats():
    stats = calcular_estatisticas_usuario_safe(current_user.id)
    user_moedas = getattr(current_user, 'total_moedas', 0) or 0
    return jsonify({
        'moedas': user_moedas,
        'tempo_hoje': stats['tempo_estudo_hoje'],
        'aulas_concluidas': stats['aulas_concluidas'],
        'sequencia': stats['sequencia_dias']
    })


@dashboard_bp.route('/api/progresso/<int:materia_id>')
@login_required
def api_progresso_materia(materia_id):
    try:
        from app.models.estudo import Modulo, Aula, ProgressoAula
        progresso = calcular_progresso_materia_safe(materia_id, current_user.id)
        modulos = Modulo.query.filter_by(materia_id=materia_id, ativo=True).all()
        progresso_modulos = []
        for modulo in modulos:
            total_aulas = modulo.aulas.filter_by(ativa=True).count()
            aulas_concluidas = db.session.query(ProgressoAula).join(Aula).filter(
                Aula.modulo_id == modulo.id,
                ProgressoAula.user_id == current_user.id,
                ProgressoAula.concluida == True
            ).count()
            progresso_modulos.append({
                'id': modulo.id,
                'titulo': modulo.titulo,
                'progresso': (aulas_concluidas / total_aulas * 100) if total_aulas > 0 else 0,
                'aulas_total': total_aulas,
                'aulas_concluidas': aulas_concluidas
            })
        return jsonify({'progresso_geral': progresso, 'modulos': progresso_modulos})
    except Exception as e:
        print(f"Erro na API de progresso: {e}")
        return jsonify({'progresso_geral': 0, 'modulos': []})

@dashboard_bp.route('/api/inicializar_usuario')
@login_required
def inicializar_usuario():
    try:
        if not hasattr(current_user, 'total_moedas') or current_user.total_moedas is None:
            current_user.total_moedas = 0
        try:
            from app.models.estudo import Moeda
            total_historico = db.session.query(func.sum(Moeda.quantidade)).filter_by(
                user_id=current_user.id
            ).scalar() or 0
            if total_historico > 0 and current_user.total_moedas == 0:
                current_user.total_moedas = total_historico
        except:
            pass
        db.session.commit()
        return jsonify({'success': True, 'total_moedas': current_user.total_moedas})
    except Exception as e:
        print(f"Erro ao inicializar usuário: {e}")
        return jsonify({'success': False, 'error': str(e)})
