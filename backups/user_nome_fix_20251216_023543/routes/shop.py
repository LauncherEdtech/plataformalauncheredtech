# app/routes/shop.py - VERSÃO COMPLETA CORRIGIDA PARA DIAMANTES
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, abort
from flask_login import login_required, current_user
from app.models.shop import Produto, Resgate
from app.models.user import User
from app import db
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
from functools import wraps

import pytz

# Definir timezone de Brasília
timezone_brasil = pytz.timezone('America/Sao_Paulo')

# Funções para trabalhar com datas no fuso horário do Brasil
def get_datetime_brasil():
    """Retorna a data e hora atual no fuso horário do Brasil"""
    return datetime.now(timezone_brasil)

def format_datetime_brasil(dt):
    """Converte um datetime para o timezone do Brasil"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Se a data não tem timezone, assume UTC
        dt = pytz.utc.localize(dt)
    return dt.astimezone(timezone_brasil)

shop_bp = Blueprint('shop', __name__, url_prefix='/shop')

# Decorador para verificar se o usuário é administrador
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)  # Acesso negado
        return f(*args, **kwargs)
    return decorated_function

@shop_bp.route('/')
def index():
    """
    Exibe a página principal da loja com os produtos disponíveis.
    Permite filtrar e ordenar os produtos.
    *** ATUALIZADO PARA DIAMANTES ***
    """
    # Obter parâmetros de filtragem e ordenação
    search = request.args.get('search', '')
    categoria = request.args.get('categoria', '')
    preco_min = request.args.get('preco_min', '')
    preco_max = request.args.get('preco_max', '')
    ordenar = request.args.get('ordenar', 'maior_preco')
    disponibilidade = request.args.get('disponibilidade', 'todos')
    
    # Consulta base
    query = Produto.query
    
    # Aplicar filtros
    if search:
        query = query.filter(Produto.nome.ilike(f'%{search}%'))
    
    if categoria:
        query = query.filter(Produto.categoria == categoria)
    
    # MUDANÇA: Usar preco_diamantes ao invés de preco_xp
    if preco_min:
        if hasattr(Produto, 'preco_diamantes'):
            query = query.filter(Produto.preco_diamantes >= int(preco_min))
        else:
            # Fallback para compatibilidade - converter XP para diamantes
            query = query.filter(Produto.preco_xp >= int(preco_min) * 2)
    
    if preco_max:
        if hasattr(Produto, 'preco_diamantes'):
            query = query.filter(Produto.preco_diamantes <= int(preco_max))
        else:
            # Fallback para compatibilidade
            query = query.filter(Produto.preco_xp <= int(preco_max) * 2)
    
    if disponibilidade == 'disponivel':
        query = query.filter(Produto.disponivel == True, Produto.estoque > 0)
    elif disponibilidade == 'esgotado':
        query = query.filter((Produto.disponivel == False) | (Produto.estoque <= 0))
    
    # MUDANÇA: Aplicar ordenação por diamantes
    if ordenar == 'menor_preco':
        if hasattr(Produto, 'preco_diamantes'):
            query = query.order_by(Produto.preco_diamantes)
        else:
            query = query.order_by(Produto.preco_xp)
    elif ordenar == 'maior_preco':
        if hasattr(Produto, 'preco_diamantes'):
            query = query.order_by(Produto.preco_diamantes.desc())
        else:
            query = query.order_by(Produto.preco_xp.desc())
    elif ordenar == 'mais_recentes':
        query = query.order_by(Produto.data_criacao.desc())
    elif ordenar == 'todos':
        # CORRIGIDO: Agora dentro do bloco if/elif correto
        if hasattr(Produto, 'preco_diamantes'):
            query = query.order_by(Produto.preco_diamantes.desc())
        else:
            query = query.order_by(Produto.preco_xp.desc())
    


    # Executar consulta
    produtos = query.all()
    
    # Garantir que produtos têm preço em diamantes
    for produto in produtos:
        if hasattr(produto, 'preco_diamantes') and produto.preco_diamantes:
            continue
        elif hasattr(produto, 'preco_xp') and produto.preco_xp:
            # Converter XP para diamantes na exibição (1 diamante = 2 XP)
            produto.preco_diamantes_display = produto.preco_xp // 2
        else:
            produto.preco_diamantes_display = 50  # Valor padrão
    
    # Obter categorias disponíveis para o filtro
    categorias = db.session.query(Produto.categoria).distinct().all()
    categorias = [cat[0] for cat in categorias if cat[0]]
    
    # MUDANÇA: Obter valores mínimos e máximos de preço em diamantes
    if hasattr(Produto, 'preco_diamantes'):
        min_preco = db.session.query(db.func.min(Produto.preco_diamantes)).scalar() or 0
        max_preco = db.session.query(db.func.max(Produto.preco_diamantes)).scalar() or 1000
    else:
        # Fallback: converter XP para diamantes
        min_preco_xp = db.session.query(db.func.min(Produto.preco_xp)).scalar() or 0
        max_preco_xp = db.session.query(db.func.max(Produto.preco_xp)).scalar() or 2000
        min_preco = min_preco_xp // 2
        max_preco = max_preco_xp // 2
    
    # MUDANÇA: Verificar diamantes do usuário atual + reset mensal
    diamantes_atual = 0
    if current_user.is_authenticated:
        # Verificar reset mensal automático
        try:
            from app.services.xp_service import XpService
            XpService.verificar_e_resetar_diamantes_mensais(current_user)
        except ImportError:
            # Se XpService não estiver disponível, usar valor atual
            pass
        
        diamantes_atual = current_user.diamantes or 0
    
    return render_template('shop/index.html',
                          produtos=produtos,
                          diamantes_atual=diamantes_atual,  # MUDANÇA: xp_atual → diamantes_atual
                          ordenar=ordenar,
                          categoria=categoria,
                          disponibilidade=disponibilidade,
                          categorias=categorias,
                          min_preco=min_preco,
                          max_preco=max_preco)

@shop_bp.route('/produto/<int:produto_id>')
def produto(produto_id):
    """
    Exibe os detalhes de um produto específico.
    *** ATUALIZADO PARA DIAMANTES ***
    """
    produto = Produto.query.get_or_404(produto_id)
    
    # Garantir que produto tem preço em diamantes
    if not hasattr(produto, 'preco_diamantes') or not produto.preco_diamantes:
        if hasattr(produto, 'preco_xp') and produto.preco_xp:
            produto.preco_diamantes_display = produto.preco_xp // 2
        else:
            produto.preco_diamantes_display = 50
    
    # MUDANÇA: Verificar diamantes do usuário atual + reset mensal
    diamantes_atual = 0
    pode_resgatar = False
    if current_user.is_authenticated:
        # Verificar reset mensal automático
        try:
            from app.services.xp_service import XpService
            XpService.verificar_e_resetar_diamantes_mensais(current_user)
        except ImportError:
            pass
        
        diamantes_atual = current_user.diamantes or 0
        
        # MUDANÇA: Verificar se pode resgatar baseado em diamantes
        preco_produto = getattr(produto, 'preco_diamantes', None) or getattr(produto, 'preco_diamantes_display', 50)
        pode_resgatar = diamantes_atual >= preco_produto
    
    # Verificar se o usuário já possui um resgate ativo deste produto
    ja_possui_resgate = False
    if current_user.is_authenticated:
        resgates_ativos = Resgate.query.filter_by(
            user_id=current_user.id,
            produto_id=produto.id,
            status='Pendente'
        ).first()
        ja_possui_resgate = resgates_ativos is not None
    
    # MUDANÇA: Produtos similares baseados em preço de diamantes
    preco_base = getattr(produto, 'preco_diamantes', None) or getattr(produto, 'preco_diamantes_display', 50)
    
    if hasattr(Produto, 'preco_diamantes'):
        produtos_similares = Produto.query.filter(
            Produto.id != produto.id, 
            Produto.disponivel == True,
            Produto.estoque > 0,
            (Produto.categoria == produto.categoria) | 
            (Produto.preco_diamantes.between(preco_base * 0.7, preco_base * 1.3))
        ).limit(4).all()
    else:
        # Fallback para preco_xp
        produtos_similares = Produto.query.filter(
            Produto.id != produto.id, 
            Produto.disponivel == True,
            Produto.estoque > 0,
            (Produto.categoria == produto.categoria) | 
            (Produto.preco_xp.between(preco_base * 1.4, preco_base * 2.6))  # Convertido para XP
        ).limit(4).all()
    
    return render_template('shop/produto.html',
                          produto=produto,
                          produtos_similares=produtos_similares,
                          diamantes_atual=diamantes_atual,  # MUDANÇA
                          pode_resgatar=pode_resgatar,
                          ja_possui_resgate=ja_possui_resgate)

@shop_bp.route('/resgatar/<int:produto_id>', methods=['GET', 'POST'])
@login_required
def resgatar(produto_id):
    """
    Permite o resgate de um produto.
    GET: Exibe formulário de resgate
    POST: Processa o resgate do produto
    *** ATUALIZADO PARA DIAMANTES ***
    """
    produto = Produto.query.get_or_404(produto_id)
    
    # Verificar reset mensal automático
    try:
        from app.services.xp_service import XpService
        XpService.verificar_e_resetar_diamantes_mensais(current_user)
    except ImportError:
        pass
    
    # Obter preço em diamantes
    preco_diamantes = getattr(produto, 'preco_diamantes', None)
    if not preco_diamantes:
        if hasattr(produto, 'preco_xp') and produto.preco_xp:
            preco_diamantes = produto.preco_xp // 2
        else:
            preco_diamantes = 50
    
    # MUDANÇA: Verificar se usuário tem diamantes suficientes
    if not current_user.pode_gastar_diamantes(preco_diamantes):
        flash(f'Você não tem diamantes suficientes. Necessário: {preco_diamantes} 💎, Você tem: {current_user.diamantes} 💎', 'danger')
        return redirect(url_for('shop.produto', produto_id=produto_id))
    
    # Verificar se produto está disponível e em estoque
    if not produto.disponivel or produto.estoque <= 0:
        flash('Este produto não está disponível no momento.', 'danger')
        return redirect(url_for('shop.produto', produto_id=produto_id))
    
    # Verificar se o usuário já possui um resgate ativo deste produto
    resgate_ativo = Resgate.query.filter_by(
        user_id=current_user.id,
        produto_id=produto.id,
        status='Pendente'
    ).first()


    if resgate_ativo:
        flash('Você já possui um resgate ativo deste produto. Finalize o resgate atual antes de solicitar outro.', 'warning')
        return redirect(url_for('shop.produto', produto_id=produto_id))
    
    if request.method == 'POST':
        # Obter informações de contato
        nome = request.form.get('nome')
        email = request.form.get('email')
        telefone = request.form.get('telefone')
        
        # MUDANÇA: Tentar gastar diamantes usando o método do usuário
        if current_user.gastar_diamantes(preco_diamantes, f"Resgate: {produto.nome}"):
            # Criar string de informações de contato
            info_contato = f"Nome: {nome}<br>Email: {email}<br>WhatsApp: {telefone}"
            
            # Criar resgate com a data no timezone do Brasil
            data_resgate_brasil = get_datetime_brasil()
            
            resgate = Resgate(
                produto_id=produto_id,
                user_id=current_user.id,
                endereco_entrega=info_contato,
                status='Pendente',
                data_resgate=data_resgate_brasil.replace(tzinfo=None),  # Salvar sem timezone
                nome_contato=nome,
                email_contato=email,
                telefone_contato=telefone,
                diamantes_gastos=preco_diamantes

            )
            
            # Atualizar estoque do produto
            produto.estoque -= 1
            
            # Se for o último item, marcar como indisponível
            if produto.estoque <= 0:
                produto.disponivel = False
            
            db.session.add(resgate)
            db.session.commit()
            
            flash(f'Produto resgatado com sucesso! Foram gastos {preco_diamantes} 💎. Nossa equipe de suporte entrará em contato em breve.', 'success')
            return redirect(url_for('shop.meus_resgates'))
        else:
            # Se falhou ao gastar diamantes, tentar método legado
            try:
                # Método legado: descontar diretamente (só como fallback)
                current_user.diamantes = (current_user.diamantes or 0) - preco_diamantes
                
                # Criar resgate mesmo assim
                info_contato = f"Nome: {nome}<br>Email: {email}<br>WhatsApp: {telefone}"
                data_resgate_brasil = get_datetime_brasil()
                
                resgate = Resgate(
                    produto_id=produto_id,
                    user_id=current_user.id,
                    endereco_entrega=info_contato,
                    status='Pendente',
                    data_resgate=data_resgate_brasil.replace(tzinfo=None),
                    nome_contato=nome,
                    email_contato=email,
                    telefone_contato=telefone
                )
                
                produto.estoque -= 1
                if produto.estoque <= 0:
                    produto.disponivel = False
                
                db.session.add(resgate)
                db.session.commit()
                
                flash(f'Produto resgatado com sucesso! Foram gastos {preco_diamantes} 💎.', 'success')
                return redirect(url_for('shop.meus_resgates'))
                
            except Exception as e:
                current_app.logger.error(f"Erro ao processar resgate: {e}")
                flash('Erro ao processar resgate. Tente novamente.', 'danger')
                return redirect(url_for('shop.produto', produto_id=produto_id))
    
    return render_template('shop/resgatar.html', produto=produto, preco_diamantes=preco_diamantes)

@shop_bp.route('/meus-resgates')
@login_required
def meus_resgates():
    """
    Exibe a página de histórico de resgates do usuário.
    """
    resgates = Resgate.query.filter_by(user_id=current_user.id).order_by(Resgate.data_resgate.desc()).all()
    
    # Converter todas as datas para o fuso horário do Brasil
    for resgate in resgates:
        resgate.data_resgate_brasil = format_datetime_brasil(resgate.data_resgate)
        
        # Converter datas de envio e entrega se existirem
        if resgate.data_envio:
            resgate.data_envio_brasil = format_datetime_brasil(resgate.data_envio)
        else:
            resgate.data_envio_brasil = None
        
        if resgate.data_entrega:
            resgate.data_entrega_brasil = format_datetime_brasil(resgate.data_entrega)
        else:
            resgate.data_entrega_brasil = None
    
    # Usar o timezone do Brasil para now
    now = get_datetime_brasil()
    
    return render_template('shop/meus_resgates.html', resgates=resgates, now=now, timedelta=timedelta)

@shop_bp.route('/cancelar-resgate/<int:resgate_id>', methods=['POST'])
@login_required
def cancelar_resgate(resgate_id):
    """
    Permite cancelar um resgate pendente
    *** ATUALIZADO PARA DIAMANTES ***
    """
    resgate = Resgate.query.get_or_404(resgate_id)
    
    # Verificar se o resgate pertence ao usuário atual
    if resgate.user_id != current_user.id:
        flash('Você não tem permissão para cancelar este resgate.', 'danger')
        return redirect(url_for('shop.meus_resgates'))
    
    # Verificar se o resgate ainda está pendente
    if resgate.status != 'Pendente':
        flash('Apenas resgates pendentes podem ser cancelados.', 'danger')
        return redirect(url_for('shop.meus_resgates'))
    
    # MUDANÇA: Devolver diamantes ao invés de XP
    produto = resgate.produto
    preco_diamantes = getattr(produto, 'preco_diamantes', None)
    
    if not preco_diamantes:
        if hasattr(produto, 'preco_xp') and produto.preco_xp:
            preco_diamantes = produto.preco_xp // 2
        else:
            preco_diamantes = 50  # Valor padrão
    
    # Devolver diamantes
    current_user.diamantes = (current_user.diamantes or 0) + preco_diamantes
    
    # Atualizar estoque do produto
    produto.estoque += 1
    
    # Se o produto estava indisponível (estoque zerado), torná-lo disponível novamente
    if not produto.disponivel and produto.estoque > 0:
        produto.disponivel = True
    
    # Remover o resgate
    db.session.delete(resgate)
    db.session.commit()
    
    flash(f'Seu resgate foi cancelado e {preco_diamantes} 💎 foram devolvidos.', 'success')
    return redirect(url_for('shop.meus_resgates'))

# =====================================================
# ROTAS DE ADMINISTRAÇÃO
# =====================================================

@shop_bp.route('/admin')
@login_required
@admin_required
def admin():
    """
    Página de administração da loja
    """
    produtos = Produto.query.order_by(Produto.id.desc()).all()
    resgates = Resgate.query.order_by(Resgate.data_resgate.desc()).all()
    
    # Processar as informações de contato para cada resgate
    for resgate in resgates:
        # Extrair o nome do contato do endereço de entrega se o nome do usuário estiver vazio
        if resgate.endereco_entrega and ("Nome:" in resgate.endereco_entrega):
            info_lines = resgate.endereco_entrega.split("<br>")
            for line in info_lines:
                if line.startswith("Nome:"):
                    resgate.nome_contato_display = line.replace("Nome:", "").strip()
                    break
        else:
            resgate.nome_contato_display = resgate.usuario.nome_completo if resgate.usuario else "N/A"
    
    return render_template('shop/admin.html', produtos=produtos, resgates=resgates)

@shop_bp.route('/admin/add-produto', methods=['POST'])
@login_required
@admin_required
def admin_add_produto():
    """
    Adiciona um novo produto
    *** ATUALIZADO PARA DIAMANTES ***
    """
    nome = request.form.get('nome')
    categoria = request.form.get('categoria')
    estoque = request.form.get('estoque')
    descricao = request.form.get('descricao')
    disponivel = 'disponivel' in request.form
    
    # MUDANÇA: Usar preco_diamantes ao invés de preco_xp
    preco_diamantes = request.form.get('preco_diamantes') or request.form.get('preco_xp')
    if not preco_diamantes:
        flash('Preço em diamantes é obrigatório.', 'danger')
        return redirect(url_for('shop.admin'))
    
    try:
        preco_diamantes = int(preco_diamantes)
        # Se veio como XP, converter para diamantes
        if request.form.get('preco_xp') and not request.form.get('preco_diamantes'):
            preco_diamantes = preco_diamantes // 2
    except ValueError:
        flash('Preço deve ser um número válido.', 'danger')
        return redirect(url_for('shop.admin'))
    
    # Processar imagem
    imagem_file = request.files.get('imagem')
    if imagem_file and imagem_file.filename:
        filename = secure_filename(imagem_file.filename)
        # Gerar nome único para evitar conflitos
        nome_arquivo = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        # Criar diretório se não existir
        produtos_dir = os.path.join(current_app.static_folder, 'images/produtos')
        os.makedirs(produtos_dir, exist_ok=True)
        # Salvar imagem
        imagem_path = os.path.join(produtos_dir, nome_arquivo)
        imagem_file.save(imagem_path)
    else:
        nome_arquivo = 'default.jpg'  # Imagem padrão
    
    # Criar produto
    produto_data = {
        'nome': nome,
        'categoria': categoria,
        'estoque': int(estoque),
        'descricao': descricao,
        'disponivel': disponivel,
        'imagem': nome_arquivo
    }
    
    # Adicionar preço em diamantes se campo existir
    if hasattr(Produto, 'preco_diamantes'):
        produto_data['preco_diamantes'] = preco_diamantes
    else:
        # Fallback: salvar como XP (converter de volta)
        produto_data['preco_xp'] = preco_diamantes * 2
    
    produto = Produto(**produto_data)
    
    db.session.add(produto)
    db.session.commit()
    
    flash(f'Produto adicionado com sucesso! Preço: {preco_diamantes} 💎', 'success')
    return redirect(url_for('shop.admin'))

@shop_bp.route('/admin/edit-produto/<int:produto_id>', methods=['POST'])
@login_required
@admin_required
def admin_edit_produto(produto_id):
    """
    Edita um produto existente
    *** ATUALIZADO PARA DIAMANTES ***
    """
    produto = Produto.query.get_or_404(produto_id)
    
    produto.nome = request.form.get('nome')
    produto.categoria = request.form.get('categoria')
    produto.estoque = int(request.form.get('estoque'))
    produto.descricao = request.form.get('descricao')
    produto.disponivel = 'disponivel' in request.form
    
    # MUDANÇA: Atualizar preço em diamantes
    preco_diamantes = request.form.get('preco_diamantes') or request.form.get('preco_xp')
    if preco_diamantes:
        try:
            preco_diamantes = int(preco_diamantes)
            # Se veio como XP, converter para diamantes
            if request.form.get('preco_xp') and not request.form.get('preco_diamantes'):
                preco_diamantes = preco_diamantes // 2
                
            if hasattr(produto, 'preco_diamantes'):
                produto.preco_diamantes = preco_diamantes
            else:
                # Fallback: salvar como XP
                produto.preco_xp = preco_diamantes * 2
        except ValueError:
            flash('Preço deve ser um número válido.', 'danger')
            return redirect(url_for('shop.admin'))
    
    # Processar imagem se uma nova for enviada
    imagem_file = request.files.get('imagem')
    if imagem_file and imagem_file.filename:
        filename = secure_filename(imagem_file.filename)
        # Gerar nome único para evitar conflitos
        nome_arquivo = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        # Criar diretório se não existir
        produtos_dir = os.path.join(current_app.static_folder, 'images/produtos')
        os.makedirs(produtos_dir, exist_ok=True)
        # Salvar imagem
        imagem_path = os.path.join(produtos_dir, nome_arquivo)
        imagem_file.save(imagem_path)
        
        # Atualizar caminho da imagem
        produto.imagem = nome_arquivo
    
    db.session.commit()
    
    flash('Produto atualizado com sucesso!', 'success')
    return redirect(url_for('shop.admin'))

@shop_bp.route('/admin/delete-produto/<int:produto_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_produto(produto_id):
    """
    Exclui um produto
    """
    produto = Produto.query.get_or_404(produto_id)
    
    # Verificar se há resgates ativos para este produto
    resgates_ativos = Resgate.query.filter_by(produto_id=produto_id, status='Pendente').count()
    if resgates_ativos > 0:
        flash(f'Não é possível excluir este produto pois existem {resgates_ativos} resgates pendentes.', 'danger')
        return redirect(url_for('shop.admin'))
    
    # Remover produto
    db.session.delete(produto)
    db.session.commit()
    
    flash('Produto excluído com sucesso!', 'success')
    return redirect(url_for('shop.admin'))

@shop_bp.route('/admin/update-status/<int:resgate_id>', methods=['POST'])
@login_required
@admin_required
def admin_update_status(resgate_id):
    """
    Atualiza o status de um resgate
    """
    resgate = Resgate.query.get_or_404(resgate_id)
    
    status_anterior = resgate.status
    novo_status = request.form.get('status')
    observacao = request.form.get('observacao', '')
    
    # Obter data e hora atual no fuso horário do Brasil
    data_atual = get_datetime_brasil()
    
    # Atualizar status e registrar a data real da mudança
    resgate.status = novo_status
    
    # Registrar data específica conforme o status - sem timezone para evitar problemas
    if novo_status == 'Enviado' and status_anterior != 'Enviado':
        resgate.data_envio = data_atual.replace(tzinfo=None)
    elif novo_status == 'Entregue' and status_anterior != 'Entregue':
        resgate.data_entrega = data_atual.replace(tzinfo=None)
    
    # Adicionar observação se fornecida
    if observacao:
        # Formatamos a data em um formato legível
        data_formatada = data_atual.strftime('%d/%m/%Y %H:%M')
        # Adicionamos a observação ao campo de endereço com a data real
        resgate.endereco_entrega += f"<br><br>Observação ({data_formatada}): {observacao}"
    
    db.session.commit()

    flash(f'Status do resgate atualizado de {status_anterior} para {novo_status}.', 'success')
    return redirect(url_for('shop.admin'))

# =====================================================
# ROTAS DE API
# =====================================================

@shop_bp.route('/api/status')
@login_required
def api_status():
    """API para status atual do usuário - DIAMANTES"""
    try:
        # Verificar reset mensal
        from app.services.xp_service import XpService
        foi_resetado, diamantes = XpService.verificar_e_resetar_diamantes_mensais(current_user)
    except ImportError:
        foi_resetado = False
        diamantes = current_user.diamantes or 0
    
    return {
        'success': True,
        'xp_total': current_user.xp_total or 0,
        'diamantes': current_user.diamantes or 0,
        'foi_resetado': foi_resetado,
        'proximo_reset': current_user.calcular_proximo_reset().isoformat() if hasattr(current_user, 'calcular_proximo_reset') and current_user.calcular_proximo_reset() else None
    }

@shop_bp.context_processor
def utility_processor():
    """Adiciona funções úteis ao contexto de template"""
    return {
        'format_datetime_brasil': format_datetime_brasil,
        'get_datetime_brasil': get_datetime_brasil
    }
