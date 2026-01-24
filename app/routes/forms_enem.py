from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_login import current_user
from datetime import datetime
import random

# Importar models
from app.models.forms import FormsQuestao, FormsAlternativa, FormsParticipante
from app import db

forms_bp = Blueprint('forms', __name__, url_prefix='/forms')

def gerar_numero_sorte():
    """Gera um número da sorte único de 6 dígitos"""
    while True:
        numero = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        existe = FormsParticipante.query.filter_by(numero_sorte=numero).first()
        if not existe:
            return numero

def ofuscar_numero(numero):
    """Ofusca as primeiras 4 posições"""
    return '****' + numero[-2:]

@forms_bp.route('/')
def inicio():
    """Página inicial do formulário"""
    try:
        todas_questoes = FormsQuestao.query.filter_by(ativo=True).all()
        
        if len(todas_questoes) < 5:
            flash('Não há questões suficientes disponíveis.', 'warning')
            return render_template('forms/inicio.html')
        
        questoes_selecionadas = random.sample(todas_questoes, 5)
        session['questoes_ids'] = [q.id for q in questoes_selecionadas]
        session['questao_atual'] = 0
        session['respostas'] = {}
        session.modified = True
        
        return render_template('forms/inicio.html')
    except Exception as e:
        print(f"Erro: {str(e)}")
        flash('Erro ao carregar formulário.', 'danger')
        return render_template('forms/inicio.html')

@forms_bp.route('/questao/<int:numero>')
def questao(numero):
    if 'questoes_ids' not in session:
        return redirect(url_for('forms.inicio'))
    if numero < 1 or numero > 5:
        return redirect(url_for('forms.inicio'))
    
    questoes_ids = session['questoes_ids']
    questao_id = questoes_ids[numero - 1]
    questao = FormsQuestao.query.get_or_404(questao_id)
    questao.numero = numero
    
    respostas = session.get('respostas', {})
    resposta_salva = respostas.get(str(questao_id))
    
    return render_template('forms/questao.html', 
                         questao=questao, 
                         total_questoes=5,
                         resposta_salva=resposta_salva)

@forms_bp.route('/questao/<int:numero>', methods=['POST'])
def salvar_resposta(numero):
    if 'questoes_ids' not in session:
        return redirect(url_for('forms.inicio'))
    
    questoes_ids = session['questoes_ids']
    questao_id = questoes_ids[numero - 1]
    resposta = request.form.get('resposta')
    
    if resposta:
        respostas = session.get('respostas', {})
        respostas[str(questao_id)] = resposta
        session['respostas'] = respostas
        session.modified = True
    
    if numero < 5:
        return redirect(url_for('forms.questao', numero=numero + 1))
    else:
        return redirect(url_for('forms.resultado'))

@forms_bp.route('/resultado')
def resultado():
    if 'questoes_ids' not in session or 'respostas' not in session:
        return redirect(url_for('forms.inicio'))
    
    questoes_ids = session['questoes_ids']
    respostas_usuario = session['respostas']
    questoes_com_resultado = []
    acertos = 0
    
    for questao_id in questoes_ids:
        questao = FormsQuestao.query.get(questao_id)
        if questao:
            resposta_usuario = respostas_usuario.get(str(questao_id))
            acertou = resposta_usuario == questao.resposta_correta
            if acertou:
                acertos += 1
            questoes_com_resultado.append({
                'questao': questao,
                'resposta_usuario': resposta_usuario,
                'acertou': acertou
            })
    
    numero_sorte = gerar_numero_sorte()
    session['numero_sorte'] = numero_sorte
    session['acertos'] = acertos
    session.modified = True
    numero_ofuscado = ofuscar_numero(numero_sorte)
    
    return render_template('forms/resultado.html',
                         questoes=questoes_com_resultado,
                         acertos=acertos,
                         total=5,
                         numero_ofuscado=numero_ofuscado)

@forms_bp.route('/cadastro')
def cadastro():
    if 'numero_sorte' not in session:
        return redirect(url_for('forms.inicio'))
    return render_template('forms/cadastro.html')

@forms_bp.route('/cadastro', methods=['POST'])
def processar_cadastro():
    if 'numero_sorte' not in session:
        flash('Erro ao processar cadastro.', 'danger')
        return redirect(url_for('forms.inicio'))
    
    nome = request.form.get('nome_completo', '').strip()
    email = request.form.get('email', '').strip()
    telefone = request.form.get('telefone', '').strip()
    ano_escolar = request.form.get('ano_escolar', '').strip()
    curso_desejado = request.form.get('curso_desejado', '').strip()
    
    if not all([nome, email, telefone, ano_escolar, curso_desejado]):
        flash('Preencha todos os campos.', 'danger')
        return redirect(url_for('forms.cadastro'))
    
    existe = FormsParticipante.query.filter_by(email=email).first()
    if existe:
        flash('E-mail já cadastrado!', 'warning')
        session['numero_sorte'] = existe.numero_sorte
        session['acertos'] = existe.acertos
        session['cadastro_completo'] = True
        session.modified = True
        return redirect(url_for('forms.numero_completo'))
    
    participante = FormsParticipante(
        nome=nome,
        email=email,
        telefone=telefone,
        ano_escolar=ano_escolar,
        curso_desejado=curso_desejado,
        numero_sorte=session['numero_sorte'],
        acertos=session.get('acertos', 0),
        respostas=session.get('respostas', {})
    )
    
    try:
        db.session.add(participante)
        db.session.commit()
        session['cadastro_completo'] = True
        session.modified = True
        flash('Cadastro realizado!', 'success')
        return redirect(url_for('forms.numero_completo'))
    except Exception as e:
        db.session.rollback()
        print(f"Erro: {str(e)}")
        flash('Erro ao cadastrar.', 'danger')
        return redirect(url_for('forms.cadastro'))

@forms_bp.route('/numero-sorte')
def numero_completo():
    if not session.get('cadastro_completo'):
        return redirect(url_for('forms.cadastro'))
    
    numero_sorte = session.get('numero_sorte')
    acertos = session.get('acertos', 0)
    
    if not numero_sorte:
        return redirect(url_for('forms.inicio'))
    
    return render_template('forms/numero_completo.html',
                         numero_sorte=numero_sorte,
                         acertos=acertos)

@forms_bp.route('/admin/participantes')
def admin_participantes():
    if not current_user.is_authenticated:
        flash('Acesso restrito.', 'danger')
        return redirect(url_for('auth.login'))
    
    participantes = FormsParticipante.query.order_by(
        FormsParticipante.data_cadastro.desc()
    ).all()
    return render_template('forms/admin_participantes.html', 
                         participantes=participantes)
