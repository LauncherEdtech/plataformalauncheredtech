# app/routes/redacao.py

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app.models.redacao import Redacao
from app.services.redacao_service import RedacaoService
from app.services.progresso_service import ProgressoService
from app.decorators.freemium import requer_redacao_disponivel
from app import db
from datetime import datetime
from flask import current_app
import json
import traceback

redacao_bp = Blueprint('redacao', __name__, url_prefix='/redacao')

@redacao_bp.route('/')
@login_required
def index():
    """
    Exibe a página principal do módulo de redação com histórico e opção de nova redação
    """
    # Obter redações do usuário (mais recentes primeiro)
    redacoes = Redacao.query.filter_by(user_id=current_user.id).order_by(Redacao.data_envio.desc()).all()
    
    # Estatísticas básicas
    total_redacoes = len(redacoes)
    media_notas = 0
    melhor_nota = 0
    
    if total_redacoes > 0:
        notas_validas = [r.nota_final for r in redacoes if r.nota_final is not None]
        if notas_validas:
            media_notas = sum(notas_validas) / len(notas_validas)
            melhor_nota = max(notas_validas)
    
    # Preparar dados das redações para os gráficos (JSON)
    redacoes_data = []
    for redacao in redacoes:
        redacao_dict = {
            'id': redacao.id,
            'titulo': redacao.titulo,
            'data_envio': redacao.data_envio.isoformat(),
            'nota_final': redacao.nota_final,
            'competencia1': redacao.competencia1,
            'competencia2': redacao.competencia2,
            'competencia3': redacao.competencia3,
            'competencia4': redacao.competencia4,
            'competencia5': redacao.competencia5,
            'status': redacao.status
        }
        redacoes_data.append(redacao_dict)
    
    redacoes_json = json.dumps(redacoes_data)
    
    # Redações avaliadas para cálculos dos gráficos
    redacoes_avaliadas = [r for r in redacoes if r.nota_final is not None]
    
    return render_template('redacao/index.html',
                          redacoes=redacoes,
                          redacoes_json=redacoes_json,
                          redacoes_avaliadas=redacoes_avaliadas,
                          total_redacoes=total_redacoes,
                          media_notas=media_notas,
                          melhor_nota=melhor_nota)


@redacao_bp.route('/nova', methods=['GET', 'POST'])
@login_required
def nova_redacao():
    """
    Permite ao usuário criar e enviar uma nova redação
    VERSÃO MODIFICADA COM DEBUG DETALHADO
    """
    if request.method == 'POST':
        try:
            # Log inicial
            current_app.logger.info(f"🚀 [REDAÇÃO DEBUG] Nova redação iniciada pelo usuário {current_user.id}")
            
            titulo = request.form.get('titulo', '').strip()
            tema = request.form.get('tema', '').strip()
            conteudo = request.form.get('conteudo', '').strip()
            
            current_app.logger.info(f"📝 [REDAÇÃO DEBUG] Dados recebidos: título={bool(titulo)}, tema={bool(tema)}, caracteres={len(conteudo)}")
            
            # Validações básicas - TÍTULO AGORA É OPCIONAL
            if not conteudo:
                error_msg = 'O conteúdo da redação é obrigatório'
                current_app.logger.warning(f"⚠️ [REDAÇÃO DEBUG] Validação falhou: {error_msg}")
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'error': error_msg}), 400
                
                flash(error_msg, 'warning')
                return render_template('redacao/nova.html', 
                                     titulo=titulo, 
                                     tema=tema, 
                                     conteudo=conteudo)
            
            # Verificar tamanho mínimo da redação
            if len(conteudo) < 500:
                error_msg = 'Sua redação deve ter pelo menos 500 caracteres'
                current_app.logger.warning(f"⚠️ [REDAÇÃO DEBUG] Validação falhou: {error_msg} (atual: {len(conteudo)})")
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'error': error_msg}), 400
                
                flash(error_msg, 'warning')
                return render_template('redacao/nova.html', 
                                     titulo=titulo, 
                                     tema=tema, 
                                     conteudo=conteudo)
            
            # Se não tem título, gerar um automaticamente ou deixar vazio
            if not titulo:
                titulo = f"Redação de {datetime.now().strftime('%d/%m/%Y')}"
                current_app.logger.info(f"📝 [REDAÇÃO DEBUG] Título gerado automaticamente: {titulo}")
            
            # Criar redação
            current_app.logger.info(f"💾 [REDAÇÃO DEBUG] Criando objeto Redacao no banco")
            redacao = Redacao(
                titulo=titulo,
                tema=tema if tema else None,
                conteudo=conteudo,
                user_id=current_user.id,
                status="Enviada"
            )
            
            db.session.add(redacao)
            db.session.commit()
            current_app.logger.info(f"✅ [REDAÇÃO EBUG] Redação ID {redacao.id} salva no banco")
            current_user.consumir_redacao_gratuita()

            # Iniciar avaliação
            current_app.logger.info(f"🔍 [REDAÇÃO DEBUG] Iniciando avaliação da redação ID {redacao.id}")
            try:
                resultado = RedacaoService.avaliar_redacao(redacao.id)
                current_app.logger.info(f"📊 [REDAÇÃO DEBUG] Resultado da avaliação: {resultado.get('sucesso', False)}")
                
                if resultado["sucesso"]:
                    # Registrar tempo de estudo (30 minutos por redação)
                    try:
                        current_app.logger.info(f"⏱️ [REDAÇÃO DEBUG] Registrando tempo de estudo")
                        ProgressoService.registrar_tempo_estudo(
                            current_user.id,
                            30,  # 30 minutos de tempo de estudo
                            "redacao"
                        )
                    except Exception as e:
                        current_app.logger.error(f"❌ [REDAÇÃO DEBUG] Erro ao registrar XP: {str(e)}")
                    
                    # Conceder moedas baseadas na nota
                    current_app.logger.info(f"💰 [REDAÇÃO DEBUG] Concedendo moedas")
                    moedas = redacao.conceder_moedas()
                    if moedas:
                        success_msg = f'Redação avaliada com sucesso! Você ganhou {moedas} moedas!'
                        current_app.logger.info(f"💰 [REDAÇÃO DEBUG] {moedas} moedas concedidas")
                    else:
                        success_msg = 'Redação avaliada com sucesso!'
                        current_app.logger.info(f"💰 [REDAÇÃO DEBUG] Nenhuma moeda concedida")
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return jsonify({
                            'success': True, 
                            'message': success_msg,
                            'redirect_url': url_for('redacao.visualizar', redacao_id=redacao.id)
                        })
                    
                    flash(success_msg, 'success')
                else:
                    error_msg = f'Ocorreu um erro ao avaliar sua redação: {resultado.get("erro", "Erro desconhecido")}'
                    current_app.logger.error(f"❌ [REDAÇÃO DEBUG] Erro na avaliação: {resultado.get('erro')}")
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return jsonify({'error': error_msg}), 500
                    
                    flash(error_msg, 'danger')
                
            except Exception as e:
                error_msg = f'Ocorreu um erro ao processar sua redação: {str(e)}'
                current_app.logger.error(f"💥 [REDAÇÃO DEBUG] Exceção durante avaliação: {str(e)}")
                current_app.logger.error(f"💥 [REDAÇÃO DEBUG] Stack trace: {traceback.format_exc()}")
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'error': error_msg,
                        'error_type': type(e).__name__,
                        'error_details': str(e)
                    }), 500
                
                flash(error_msg, 'danger')
            
            current_app.logger.info(f"🎯 [REDAÇÃO DEBUG] Redirecionando para visualização da redação ID {redacao.id}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'redirect_url': url_for('redacao.visualizar', redacao_id=redacao.id)
                })
            
            return redirect(url_for('redacao.visualizar', redacao_id=redacao.id))
            
        except Exception as e:
            # Erro geral não capturado
            current_app.logger.error(f"💥 [REDAÇÃO DEBUG] Erro geral não capturado: {str(e)}")
            current_app.logger.error(f"💥 [REDAÇÃO DEBUG] Stack trace completo: {traceback.format_exc()}")
            
            error_msg = f'Erro interno do servidor: {str(e)}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'error': error_msg,
                    'error_type': type(e).__name__,
                    'error_details': str(e),
                    'stack_trace': traceback.format_exc()
                }), 500
            
            flash('Ocorreu um erro interno. Por favor, tente novamente.', 'danger')
            return render_template('redacao/nova.html')
    
    # GET - Verificar se tem tema passado como parâmetro
    tema_sugerido = request.args.get('tema', '')
    current_app.logger.info(f"📄 [REDAÇÃO DEBUG] Carregando página GET, tema sugerido: {tema_sugerido}")
    
    return render_template('redacao/nova.html', tema_sugerido=tema_sugerido)

# NOVA ROTA: Endpoint para debug de API key
@redacao_bp.route('/debug/api-key')
@login_required
def debug_api_key():
    """
    Endpoint para debugar a configuração da API key (apenas para admins)
    """
    if not current_user.is_admin:
        return jsonify({'error': 'Acesso negado'}), 403
    
    import os
    from dotenv import load_dotenv
    
    debug_info = {
        'timestamp': datetime.now().isoformat(),
        'user_id': current_user.id,
        'checks': []
    }
    
    # Verificar arquivo .env
    env_file_exists = os.path.exists('.env')
    debug_info['checks'].append({
        'name': 'Arquivo .env existe',
        'status': env_file_exists,
        'details': '.env encontrado na raiz' if env_file_exists else '.env não encontrado'
    })
    
    # Verificar variável antes do load_dotenv
    env_before = bool(os.environ.get('OPENAI_API_KEY'))
    debug_info['checks'].append({
        'name': 'OPENAI_API_KEY antes do load_dotenv',
        'status': env_before,
        'details': 'Definida' if env_before else 'Não definida'
    })
    
    # Carregar .env
    try:
        load_dotenv()
        debug_info['checks'].append({
            'name': 'load_dotenv()',
            'status': True,
            'details': 'Executado com sucesso'
        })
    except Exception as e:
        debug_info['checks'].append({
            'name': 'load_dotenv()',
            'status': False,
            'details': str(e)
        })
    
    # Verificar variável depois do load_dotenv
    env_after = os.environ.get('OPENAI_API_KEY')
    debug_info['checks'].append({
        'name': 'OPENAI_API_KEY depois do load_dotenv',
        'status': bool(env_after),
        'details': f'Definida (tamanho: {len(env_after)})' if env_after else 'Não definida'
    })
    
    # Verificar Flask config
    flask_key = current_app.config.get('OPENAI_API_KEY')
    debug_info['checks'].append({
        'name': 'Flask config OPENAI_API_KEY',
        'status': bool(flask_key),
        'details': f'Definida (tamanho: {len(flask_key)})' if flask_key else 'Não definida'
    })
    
    # Testar RedacaoService
    try:
        from app.services.redacao_service import RedacaoService
        api_key = RedacaoService._get_api_key()
        debug_info['checks'].append({
            'name': 'RedacaoService._get_api_key()',
            'status': bool(api_key),
            'details': f'Retornou chave (tamanho: {len(api_key)})' if api_key else 'Retornou None'
        })
    except Exception as e:
        debug_info['checks'].append({
            'name': 'RedacaoService._get_api_key()',
            'status': False,
            'details': f'Erro: {str(e)}'
        })
    
    return jsonify(debug_info)

# NOVA ROTA: Testar avaliação de redação
@redacao_bp.route('/debug/test-evaluation', methods=['POST'])
@login_required
def debug_test_evaluation():
    """
    Endpoint para testar avaliação com texto simples (apenas para admins)
    """
    if not current_user.is_admin:
        return jsonify({'error': 'Acesso negado'}), 403
    
    try:
        # Criar redação de teste
        redacao_teste = Redacao(
            titulo="Teste de Avaliação",
            tema="Teste",
            conteudo="Esta é uma redação de teste para verificar se o sistema de avaliação está funcionando. " * 20,  # Repetir para atingir mínimo de caracteres
            user_id=current_user.id,
            status="Enviada"
        )
        
        db.session.add(redacao_teste)
        db.session.commit()
        
        # Testar avaliação
        resultado = RedacaoService.avaliar_redacao(redacao_teste.id)
        
        # Limpar teste
        db.session.delete(redacao_teste)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'resultado': resultado,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'error_type': type(e).__name__,
            'stack_trace': traceback.format_exc()
        }), 500




@redacao_bp.route('/<int:redacao_id>')
@login_required
def visualizar(redacao_id):
    """
    Exibe uma redação específica com seu feedback
    """
    redacao = Redacao.query.get_or_404(redacao_id)
    
    # Verificar permissão
    if redacao.user_id != current_user.id:
        flash('Você não tem permissão para visualizar esta redação', 'danger')
        return redirect(url_for('redacao.index'))
    
    # Se a redação foi avaliada, verificar se as moedas já foram concedidas
    if redacao.status == "Avaliada" and redacao.nota_final and not redacao.moedas_concedidas:
        moedas = redacao.conceder_moedas()
        if moedas:
            flash(f'Você ganhou {moedas} moedas pela sua nota!', 'success')
    
    return render_template('redacao/visualizar.html', redacao=redacao)

@redacao_bp.route('/<int:redacao_id>/reavaliar', methods=['POST'])
@login_required
def reavaliar(redacao_id):
    """
    Permite reavaliar uma redação
    """
    redacao = Redacao.query.get_or_404(redacao_id)
    
    # Verificar permissão
    if redacao.user_id != current_user.id:
        flash('Você não tem permissão para reavaliar esta redação', 'danger')
        return redirect(url_for('redacao.index'))
    
    try:
        # Reiniciar status
        redacao.status = "Enviada"
        redacao.moedas_concedidas = False
        db.session.commit()
        
        # Realizar a avaliação
        resultado = RedacaoService.avaliar_redacao(redacao.id)
        
        if resultado["sucesso"]:
            # Conceder moedas baseadas na nota
            moedas = redacao.conceder_moedas()
            if moedas:
                flash(f'Redação reavaliada com sucesso! Você ganhou {moedas} moedas!', 'success')
            else:
                flash('Redação reavaliada com sucesso!', 'success')
        else:
            flash(f'Ocorreu um erro ao reavaliar sua redação: {resultado.get("erro", "Erro desconhecido")}', 'danger')
    except Exception as e:
        flash(f'Ocorreu um erro ao processar sua redação: {str(e)}', 'danger')
    
    return redirect(url_for('redacao.visualizar', redacao_id=redacao.id))

@redacao_bp.route('/<int:redacao_id>/editar', methods=['GET', 'POST'])
@login_required
def editar(redacao_id):
    """
    Permite editar uma redação existente (somente se não foi avaliada)
    """
    redacao = Redacao.query.get_or_404(redacao_id)
    
    # Verificar permissão
    if redacao.user_id != current_user.id:
        flash('Você não tem permissão para editar esta redação', 'danger')
        return redirect(url_for('redacao.index'))
    
    # Verificar se já foi avaliada
    if redacao.status == "Avaliada":
        flash('Não é possível editar uma redação já avaliada', 'warning')
        return redirect(url_for('redacao.visualizar', redacao_id=redacao.id))
    
    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        tema = request.form.get('tema', '').strip()
        conteudo = request.form.get('conteudo', '').strip()
        
        # Validações básicas - TÍTULO AGORA É OPCIONAL
        if not conteudo:
            flash('O conteúdo da redação é obrigatório', 'warning')
            return render_template('redacao/editar.html', redacao=redacao)
        
        # Verificar tamanho mínimo da redação
        if len(conteudo) < 500:
            flash('Sua redação deve ter pelo menos 500 caracteres', 'warning')
            return render_template('redacao/editar.html', redacao=redacao)
        
        # Se não tem título, gerar um automaticamente ou deixar o atual
        if not titulo:
            if not redacao.titulo:
                titulo = f"Redação de {datetime.now().strftime('%d/%m/%Y')}"
            else:
                titulo = redacao.titulo  # Manter o título atual se existir
        
        # Atualizar redação
        redacao.titulo = titulo
        redacao.tema = tema if tema else None
        redacao.conteudo = conteudo
        redacao.status = "Enviada"
        db.session.commit()
        
        # Iniciar avaliação
        try:
            resultado = RedacaoService.avaliar_redacao(redacao.id)
            
            if resultado["sucesso"]:
                # Conceder moedas baseadas na nota
                moedas = redacao.conceder_moedas()
                if moedas:
                    flash(f'Redação atualizada e avaliada com sucesso! Você ganhou {moedas} moedas!', 'success')
                else:
                    flash('Redação atualizada e avaliada com sucesso!', 'success')
            else:
                flash(f'Redação atualizada, mas ocorreu um erro na avaliação: {resultado.get("erro", "Erro desconhecido")}', 'warning')
        except Exception as e:
            flash(f'Redação atualizada, mas ocorreu um erro ao processar sua avaliação: {str(e)}', 'warning')
        
        return redirect(url_for('redacao.visualizar', redacao_id=redacao.id))
    
    return render_template('redacao/editar.html', redacao=redacao)

@redacao_bp.route('/temas-sugeridos')
@login_required
def temas_sugeridos():
    """
    Exibe uma lista de temas sugeridos para redação
    """
    temas = [
        {
            "titulo": "Os desafios da educação inclusiva no Brasil",
            "descricao": "Discuta os desafios e possíveis soluções para a implementação efetiva da educação inclusiva no sistema educacional brasileiro."
        },
        {
            "titulo": "O impacto das redes sociais na saúde mental dos jovens",
            "descricao": "Analise como as redes sociais influenciam a saúde mental da juventude brasileira e proponha intervenções para mitigar efeitos negativos."
        },
        {
            "titulo": "Desafios para a segurança alimentar no contexto das mudanças climáticas",
            "descricao": "Discuta como as mudanças climáticas afetam a produção de alimentos e quais medidas podem ser adotadas para garantir a segurança alimentar."
        },
        {
            "titulo": "Mobilidade urbana sustentável nas grandes cidades brasileiras",
            "descricao": "Analise os problemas de mobilidade urbana nas metrópoles brasileiras e proponha soluções que contemplem aspectos econômicos, sociais e ambientais."
        },
        {
            "titulo": "O papel da tecnologia na democratização do acesso à saúde",
            "descricao": "Discuta como avanços tecnológicos podem contribuir para ampliar o acesso à saúde no Brasil, considerando desafios socioeconômicos."
        },
        {
            "titulo": "A importância da educação financeira na sociedade brasileira",
            "descricao": "Analise a necessidade de educação financeira no Brasil e proponha medidas para implementá-la de forma efetiva."
        },
        {
            "titulo": "Violência contra a mulher: desafios e soluções",
            "descricao": "Discuta as causas da violência contra a mulher no Brasil e apresente propostas para combater esse problema social."
        },
        {
            "titulo": "O futuro do trabalho na era da inteligência artificial",
            "descricao": "Analise como a IA está transformando o mercado de trabalho e quais medidas devem ser tomadas para preparar a sociedade."
        }
    ]
    
    return render_template('redacao/temas_sugeridos.html', temas=temas)

@redacao_bp.route('/dicas')
@login_required
def dicas():
    """
    Exibe dicas para melhorar a escrita de redações
    """
    return render_template('redacao/dicas.html')
