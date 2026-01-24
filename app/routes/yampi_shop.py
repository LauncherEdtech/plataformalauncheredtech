# app/routes/yampi_shop.py - VERSÃO FINAL COM CATEGORIAS DINÂMICAS DA API

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.yampi_shop import ProdutoYampi, DescontoDesbloqueado
from app.services.yampi_service import get_yampi_service
import logging
import json

logger = logging.getLogger(__name__)

yampi_bp = Blueprint('yampi', __name__, url_prefix='/shop')

@yampi_bp.route('/yampi', methods=['GET'])
@login_required
def listar_produtos():
    """Página principal do shop"""
    try:
        # Busca produtos ativos
        produtos = ProdutoYampi.query.filter_by(ativo=True).order_by(
            ProdutoYampi.ordem.asc()
        ).all()
        
        produtos_dict = [p.to_dict(user=current_user) for p in produtos]
        
        # ===== EXTRAIR CATEGORIAS ÚNICAS DINÂMICAMENTE =====
        categorias_unicas = set()
        for p in produtos:
            if p.categoria and p.categoria != 'Geral':
                categorias_unicas.add(p.categoria)
        
        # Ordenar alfabeticamente
        categorias_unicas = sorted(list(categorias_unicas))
        
        logger.info(f"📁 Categorias disponíveis: {categorias_unicas}")
        
        descontos_ativos = DescontoDesbloqueado.query.filter_by(
            user_id=current_user.id,
            usado=False
        ).filter(
            DescontoDesbloqueado.expira_em > db.func.now()
        ).all()
        
        return render_template(
            'shop_yampi.html',
            produtos=produtos_dict,
            categorias=categorias_unicas,  # ✅ CATEGORIAS DINÂMICAS
            descontos_ativos=descontos_ativos,
            user_diamantes=current_user.diamantes
        )
    except Exception as e:
        logger.error(f"Erro ao listar produtos: {e}")
        flash("Erro ao carregar produtos.", "error")
        return redirect(url_for('dashboard.index'))


@yampi_bp.route('/yampi/desbloquear/<int:produto_id>', methods=['POST'])
@login_required
def desbloquear_desconto(produto_id):
    """Desbloqueia desconto"""
    try:
        produto = ProdutoYampi.query.get_or_404(produto_id)
        
        pode, mensagem = produto.usuario_pode_desbloquear(current_user)
        if not pode:
            return jsonify({'success': False, 'message': mensagem}), 400
        
        # Usar purchase_url do produto
        purchase_url = getattr(produto, 'purchase_url', None)
        
        if purchase_url and purchase_url.strip():
            logger.info(f"✅ Usando purchase_url do produto: {purchase_url}")
            link_checkout = purchase_url
        else:
            logger.warning(f"⚠️ Produto sem purchase_url, tentando via API")
            yampi = get_yampi_service()
            link_checkout = yampi.gerar_link_checkout(
                produto_sku=produto.sku,
                percentual_desconto=produto.percentual_desconto,
                user_email=current_user.email,
                purchase_url=None
            )
        
        if not link_checkout:
            return jsonify({'success': False, 'message': 'Erro ao gerar checkout'}), 500
        
        desbloqueio, msg = DescontoDesbloqueado.criar_desbloqueio(
            user=current_user,
            produto=produto,
            link_checkout=link_checkout,
            validade_horas=24
        )
        
        if not desbloqueio:
            return jsonify({'success': False, 'message': msg}), 400
        
        return jsonify({
            'success': True,
            'message': 'Desconto desbloqueado!',
            'desbloqueio': desbloqueio.to_dict(),
            'link_checkout': link_checkout,
            'diamantes_restantes': current_user.diamantes
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao desbloquear: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@yampi_bp.route('/yampi/meus-descontos', methods=['GET'])
@login_required
def meus_descontos():
    """Meus descontos"""
    try:
        descontos = DescontoDesbloqueado.query.filter_by(
            user_id=current_user.id
        ).order_by(DescontoDesbloqueado.criado_em.desc()).all()
        
        descontos_ativos = [d for d in descontos if d.esta_valido]
        descontos_historico = [d for d in descontos if not d.esta_valido]
        
        return render_template(
            'meus_descontos_yampi.html',
            descontos_ativos=descontos_ativos,
            descontos_historico=descontos_historico
        )
    except Exception as e:
        logger.error(f"Erro ao listar descontos: {e}")
        return redirect(url_for('yampi.listar_produtos'))


# ============ ADMIN ============

@yampi_bp.route('/yampi/admin/produtos', methods=['GET'])
@login_required
def admin_produtos():
    """Painel admin"""
    if not current_user.is_admin:
        return redirect(url_for('yampi.listar_produtos'))
    
    produtos = ProdutoYampi.query.order_by(ProdutoYampi.ordem.asc()).all()
    
    yampi_config = {
        'token': 'WnUywC0wcNGFWFlSn6UelW1VqNBOnnfidkczUhkw',
        'secret': 'sk_shYPIoIJ6qasmxlnykpxJsROJwTU8aMZ1jzee',
        'alias': 'plataforma-launcher-shop'
    }
    
    return render_template(
        'admin_produtos_yampi.html',
        produtos=produtos,
        yampi_config=yampi_config
    )


@yampi_bp.route('/yampi/admin/salvar-produtos', methods=['POST'])
@login_required
def admin_salvar_produtos():
    """
    Salva produtos capturando:
    - price_sale (preço "DE" - valor original)
    - price_discount (preço "POR" - valor promocional)
    - purchase_url (link direto de compra)
    - categoria (da API Yampi) ← 100% DINÂMICO
    - Descrição HTML
    - Todas as imagens
    """
    if not current_user.is_admin:
        return jsonify({'success': False}), 403
    
    try:
        produtos_data = request.json.get('produtos', [])
        sincronizados = 0
        
        for p in produtos_data:
            try:
                # ===== 1. EXTRAIR PREÇOS CORRETOS DA YAMPI =====
                price_sale = 0
                price_discount = 0
                purchase_url = None
                
                skus = p.get('skus', {}).get('data', []) if isinstance(p.get('skus'), dict) else []
                if skus:
                    sku_data = skus[0]
                    
                    price_sale = float(sku_data.get('price_sale', 0) or 0)
                    price_discount = float(sku_data.get('price_discount', 0) or 0)
                    purchase_url = sku_data.get('purchase_url', '')
                    
                    logger.info(f"📊 Produto {p.get('name')}: sale={price_sale}, discount={price_discount}")
                
                # ===== 1.5. EXTRAIR CATEGORIA DA API YAMPI (DINÂMICO) =====
                categoria_nome = 'Geral'  # Valor padrão
                
                categorias_data = p.get('categories', {})
                if isinstance(categorias_data, dict):
                    cats = categorias_data.get('data', [])
                    if cats and len(cats) > 0:
                        # ✅ Pegar primeira categoria da API
                        categoria_nome = cats[0].get('name', 'Geral')
                        logger.info(f"🏷️  Categoria da API: {categoria_nome}")
                
                # ===== 2. EXTRAIR IMAGENS =====
                imagem_capa = ''
                lista_todas_imagens = []
                
                imagens_raw = []
                images_data = p.get('images', {})
                if isinstance(images_data, dict):
                    imagens_raw = images_data.get('data', [])
                elif isinstance(images_data, list):
                    imagens_raw = images_data
                
                for img in imagens_raw:
                    url_img = img.get('large', {}).get('url') or img.get('medium', {}).get('url') or img.get('url')
                    thumb_url = img.get('thumb', {}).get('url') or url_img

                    if url_img:
                        lista_todas_imagens.append({
                            'url': url_img,
                            'thumb': {'url': thumb_url}
                        })
                        if not imagem_capa:
                            imagem_capa = url_img

                imagens_json_str = json.dumps(lista_todas_imagens)
                
                # ===== 3. EXTRAIR DESCRIÇÃO HTML =====
                descricao_html = ''
                texts_data = p.get('texts', {}).get('data', {})
                if texts_data and 'description' in texts_data:
                    descricao_html = texts_data.get('description', '')
                else:
                    descricao_html = p.get('description', '')

                # ===== 4. SALVAR NO BANCO =====
                produto_local = ProdutoYampi.query.filter_by(yampi_id=str(p.get('id'))).first()
                
                if not produto_local:
                    # Criar novo produto
                    produto_local = ProdutoYampi(
                        yampi_id=str(p.get('id')),
                        sku=p.get('sku', f"SKU-{p.get('id')}"),
                        nome=p.get('name', 'Produto'),
                        descricao=descricao_html,
                        imagem_url=imagem_capa,
                        imagens_json=imagens_json_str,
                        
                        # ✅ CAMPOS DA YAMPI
                        preco_venda=float(price_sale),
                        preco_desconto=float(price_discount),
                        purchase_url=purchase_url,
                        categoria=categoria_nome,  # ✅ CATEGORIA DA API
                        
                        # Campos legados
                        preco_original=float(price_sale),
                        ordem=sincronizados + 1
                    )
                    
                    db.session.add(produto_local)
                else:
                    # Atualizar produto existente
                    produto_local.nome = p.get('name', produto_local.nome)
                    produto_local.imagem_url = imagem_capa
                    produto_local.imagens_json = imagens_json_str
                    produto_local.descricao = descricao_html
                    
                    # ✅ ATUALIZAR DADOS DA YAMPI
                    produto_local.preco_venda = float(price_sale)
                    produto_local.preco_desconto = float(price_discount)
                    produto_local.purchase_url = purchase_url
                    produto_local.categoria = categoria_nome  # ✅ CATEGORIA DA API
                    
                    # Atualizar campo legado
                    produto_local.preco_original = float(price_sale)
                
                sincronizados += 1
                
            except Exception as e:
                logger.error(f"❌ Erro no produto {p.get('id')}: {e}")
                continue
        
        db.session.commit()
        
        logger.info(f"✅ {sincronizados} produtos sincronizados com categorias da API!")
        
        return jsonify({
            'success': True, 
            'message': f'{sincronizados} produtos sincronizados com categorias!'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Erro ao salvar produtos: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@yampi_bp.route('/yampi/admin/produto/<int:produto_id>/editar', methods=['POST'])
@login_required
def admin_editar_produto(produto_id):
    """Editar produto"""
    if not current_user.is_admin:
        return jsonify({'success': False}), 403
    
    try:
        produto = ProdutoYampi.query.get_or_404(produto_id)
        
        produto.percentual_desconto = int(request.form.get('percentual_desconto', produto.percentual_desconto))
        produto.diamantes_necessarios = int(request.form.get('diamantes_necessarios', produto.diamantes_necessarios))
        produto.ativo = request.form.get('ativo', 'false').lower() == 'true'
        produto.ordem = int(request.form.get('ordem', produto.ordem))
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Produto atualizado!',
            'produto': produto.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
