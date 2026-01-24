# app/routes/roleta.py
from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models.roleta import RoletaPrimeiroAcesso
from app.models.shop import Produto, Resgate
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

roleta_bp = Blueprint('roleta', __name__, url_prefix='/roleta')

@roleta_bp.route('/primeiro-acesso')
@login_required
def primeiro_acesso():
    """
    Exibe a roleta do primeiro acesso
    """
    # Verifica se o usuário já girou a roleta
    roleta_existente = RoletaPrimeiroAcesso.query.filter_by(user_id=current_user.id).first()
    
    if roleta_existente:
        # Se já girou, redireciona para o status do prêmio
        return redirect(url_for('roleta.status_premio'))
    
    # Buscar ou criar a garrafinha no banco
    garrafinha = Produto.query.filter_by(nome='Garrafinha Launcher').first()
    
    if not garrafinha:
        # Criar a garrafinha se não existir
        garrafinha = Produto(
            nome='Garrafinha Launcher',
            descricao='Garrafinha térmica exclusiva Launcher 500ml - Mantém sua bebida gelada ou quente por até 12 horas!',
            preco_diamantes=0,  # Grátis, ganho na roleta
            estoque=999,  # Estoque alto para todos ganharem
            categoria='Brindes',
            disponivel=True,
            imagem='garrafinha.jpg'  # Você precisa adicionar esta imagem
        )
        db.session.add(garrafinha)
        db.session.commit()
    
    # Lista de prêmios falsos para exibir na roleta (apenas visual)
    premios_visuais = [
        {
            'id': 1,
            'nome': 'iPhone 15 Pro',
            'imagem': 'iphone.jpg',
            'valor': 8000
        },
        {
            'id': 2, 
            'nome': 'Garrafinha Launcher',
            'imagem': 'garrafinha.jpg',
            'valor': 0
        },
        {
            'id': 3,
            'nome': 'Notebook Dell',
            'imagem': 'notebook.jpg', 
            'valor': 4500
        },
        {
            'id': 4,
            'nome': 'Fone JBL',
            'imagem': 'fone.jpg',
            'valor': 350
        },
        {
            'id': 5,
            'nome': 'Kit de Livros',
            'imagem': 'livros.jpg',
            'valor': 200
        },
        {
            'id': 6,
            'nome': 'Garrafinha Launcher',
            'imagem': 'garrafinha.jpg',
            'valor': 0
        },
        {
            'id': 7,
            'nome': 'Caderno Moleskine',
            'imagem': 'caderno.jpg',
            'valor': 120
        },
        {
            'id': 8,
            'nome': 'Tablet Samsung',
            'imagem': 'tablet.jpg',
            'valor': 2000
        }
    ]
    
    return render_template('roleta/primeiro_acesso.html', 
                         premios=premios_visuais,
                         garrafinha_id=garrafinha.id)

@roleta_bp.route('/girar', methods=['POST'])
@login_required
def girar_roleta():
    """
    Processa o giro da roleta (sempre ganha a garrafinha)
    """
    try:
        # Verifica se já girou
        roleta_existente = RoletaPrimeiroAcesso.query.filter_by(user_id=current_user.id).first()
        
        if roleta_existente:
            return jsonify({
                'success': False,
                'message': 'Você já girou a roleta do primeiro acesso!'
            })
        
        # Buscar a garrafinha
        garrafinha = Produto.query.filter_by(nome='Garrafinha Launcher').first()
        
        if not garrafinha:
            return jsonify({
                'success': False,
                'message': 'Erro ao processar prêmio. Tente novamente.'
            })
        
        # Criar registro da roleta
        roleta = RoletaPrimeiroAcesso(
            user_id=current_user.id,
            produto_id=garrafinha.id,
            dias_espera=8  # 8 dias de espera
        )
        
        db.session.add(roleta)
        db.session.commit()
        
        # A posição 1 é sempre a garrafinha (índice começa em 0)
        # Vamos fazer parar sempre no índice 1 ou 5 (que são as garrafinhas)
        posicao_final = 1  # Sempre para na segunda posição (garrafinha)
        
        return jsonify({
            'success': True,
            'posicao': posicao_final,
            'premio': {
                'nome': garrafinha.nome,
                'descricao': garrafinha.descricao,
                'imagem': garrafinha.imagem
            },
            'dias_espera': 8,
            'message': 'Parabéns! Você ganhou uma Garrafinha Launcher!'
        })
        
    except Exception as e:
        logger.error(f"Erro ao girar roleta: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Erro ao processar. Tente novamente.'
        })

@roleta_bp.route('/status-premio')
@login_required
def status_premio():
    """
    Exibe o status do prêmio ganho na roleta
    """
    roleta = RoletaPrimeiroAcesso.query.filter_by(user_id=current_user.id).first()
    
    if not roleta:
        return redirect(url_for('roleta.primeiro_acesso'))
    pode_resgatar = current_user.pode_resgatar_roleta
    return render_template('roleta/status_premio.html', 
                         roleta=roleta,
                         pode_resgatar=pode_resgatar,
                         link_taxa_resgate='https://pay.kiwify.com.br/2HipOfz')

@roleta_bp.route('/resgatar-premio', methods=['POST'])
@login_required
def resgatar_premio():
    """
    Resgata o prêmio (só se pagou a taxa de resgate ou for assinante)
    """
    roleta = RoletaPrimeiroAcesso.query.filter_by(user_id=current_user.id).first()

    if not roleta:
        flash('Você ainda não girou a roleta!', 'warning')
        return redirect(url_for('roleta.primeiro_acesso'))

    if roleta.foi_resgatado:
        flash('Você já resgatou seu prêmio!', 'info')
        return redirect(url_for('shop.meus_resgates'))

    # 🚫 Caso não tenha plano ativo e não tenha pago a taxa de resgate
    if not current_user.tem_plano_ativo and not current_user.pode_resgatar_roleta:
        # Retorna JSON para o front exibir o modal freemium (Taxa de Resgate)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'show_freemium_modal': True,
                'tipo': 'taxa_resgate',
                'link_pagamento': 'https://pay.kiwify.com.br/2HipOfz'
            }), 403
        else:
            flash('Para resgatar seu prêmio, é necessário pagar a taxa de resgate.', 'warning')
            return redirect(url_for('roleta.status_premio'))

    # ✅ Libera o resgate se já for assinante ou tiver pago a taxa
    try:
        nome = request.form.get('nome')
        email = request.form.get('email')
        telefone = request.form.get('telefone')
        endereco = request.form.get('endereco')

        info_contato = f"Nome: {nome}<br>Email: {email}<br>WhatsApp: {telefone}<br>Endereço: {endereco}"

        from app.models.shop import Resgate, Produto
        resgate = Resgate(
            produto_id=roleta.produto_ganho_id,
            user_id=current_user.id,
            endereco_entrega=info_contato,
            status='Pendente',
            nome_contato=nome,
            email_contato=email,
            telefone_contato=telefone,
            diamantes_gastos=0
        )

        db.session.add(resgate)
        roleta.foi_resgatado = True
        roleta.resgate_id = resgate.id

        produto = roleta.produto_ganho
        if produto and produto.estoque > 0:
            produto.estoque -= 1

        db.session.commit()

        flash('🎉 Seu prêmio foi resgatado com sucesso! Entraremos em contato em breve.', 'success')
        return redirect(url_for('shop.meus_resgates'))

    except Exception as e:
        logger.error(f"Erro ao resgatar prêmio: {e}")
        db.session.rollback()
        flash('Erro ao processar resgate.', 'danger')
        return redirect(url_for('roleta.status_premio'))

@roleta_bp.route('/verificar-primeiro-acesso')
@login_required
def verificar_primeiro_acesso():
    """
    API para verificar se o usuário precisa ver a roleta
    """
    roleta = RoletaPrimeiroAcesso.query.filter_by(user_id=current_user.id).first()
    
    return jsonify({
        'precisa_roleta': roleta is None,
        'ja_girou': roleta is not None,
        'status': roleta.to_dict() if roleta else None
    })
