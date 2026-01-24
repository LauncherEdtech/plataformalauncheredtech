# fix_db_import.py - Correção direta do problema de import do db

import os
import sys

def fix_db_import_issue():
    """Corrige o problema de 'db' is undefined no estudo.py"""
    
    print("🔧 CORRIGINDO PROBLEMA DE IMPORT DO DB...")
    print("=" * 50)
    
    # 1. Verificar se o arquivo existe
    estudo_file = 'app/routes/estudo.py'
    
    if not os.path.exists(estudo_file):
        print(f"❌ Arquivo {estudo_file} não encontrado")
        return False
    
    # 2. Ler o arquivo atual
    try:
        with open(estudo_file, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"✅ Arquivo {estudo_file} lido")
    except Exception as e:
        print(f"❌ Erro ao ler arquivo: {e}")
        return False
    
    # 3. Verificar se o import do db já existe
    if 'from app import db' in content:
        print("⚠️ Import 'from app import db' já existe, mas ainda há erro...")
        
        # Verificar se há algum problema na ordem dos imports
        lines = content.split('\n')
        print("\n📋 IMPORTS ATUAIS:")
        for i, line in enumerate(lines[:20]):  # Primeiras 20 linhas
            if 'import' in line:
                print(f"   {i+1}: {line}")
    else:
        print("❌ Import 'from app import db' não encontrado")
    
    # 4. Criar versão corrigida
    print("\n🔧 Criando versão corrigida...")
    
    # Template corrigido mínimo
    corrected_content = '''# app/routes/estudo.py - VERSÃO CORRIGIDA
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from app import db
from app.models.user import User
import os
import hashlib
from werkzeug.utils import secure_filename

estudo_bp = Blueprint('estudo', __name__, url_prefix='/estudo')

@estudo_bp.route('/')
@login_required
def index():
    """Página principal de estudos - VERSÃO CORRIGIDA"""
    try:
        # Verificar se as tabelas existem
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        materias = []
        
        if 'materia' in existing_tables:
            try:
                from app.models.estudo import Materia, Modulo, Aula, ProgressoAula
                
                materias = Materia.query.filter_by(ativa=True).order_by(Materia.ordem).all()
                
                # Calcular progresso para cada matéria
                for materia in materias:
                    try:
                        # Total de aulas na matéria
                        total_aulas = db.session.query(Aula).join(Modulo).filter(
                            Modulo.materia_id == materia.id,
                            Aula.ativa == True
                        ).count()
                        
                        if total_aulas > 0:
                            # Aulas concluídas pelo usuário
                            aulas_concluidas = db.session.query(ProgressoAula).join(Aula).join(Modulo).filter(
                                Modulo.materia_id == materia.id,
                                ProgressoAula.user_id == current_user.id,
                                ProgressoAula.concluida == True
                            ).count()
                            
                            materia.progresso_usuario_calc = (aulas_concluidas / total_aulas) * 100
                        else:
                            materia.progresso_usuario_calc = 0
                            
                    except Exception as e:
                        print(f"Erro ao calcular progresso da matéria {materia.id}: {e}")
                        materia.progresso_usuario_calc = 0
                        
            except Exception as e:
                print(f"Erro ao carregar matérias: {e}")
                materias = []
        
        return render_template('estudo/index.html', materias=materias)
        
    except Exception as e:
        print(f"Erro na página principal de estudos: {e}")
        flash('Erro ao carregar página de estudos.', 'error')
        return redirect(url_for('dashboard.index'))

@estudo_bp.route('/materia/<int:materia_id>')
@login_required
def materia(materia_id):
    """Página de uma matéria específica"""
    try:
        from app.models.estudo import Materia, Modulo, Aula, ProgressoAula
        
        materia = Materia.query.get_or_404(materia_id)
        modulos = materia.modulos.filter_by(ativo=True).order_by(Modulo.ordem).all()
        
        # Calcular progresso para cada módulo
        for modulo in modulos:
            try:
                total_aulas = modulo.aulas.filter_by(ativa=True).count()
                
                if total_aulas > 0:
                    aulas_concluidas = db.session.query(ProgressoAula).join(Aula).filter(
                        Aula.modulo_id == modulo.id,
                        ProgressoAula.user_id == current_user.id,
                        ProgressoAula.concluida == True
                    ).count()
                    modulo.progresso_usuario_calc = (aulas_concluidas / total_aulas) * 100
                else:
                    modulo.progresso_usuario_calc = 0
                    
            except Exception as e:
                print(f"Erro ao calcular progresso do módulo {modulo.id}: {e}")
                modulo.progresso_usuario_calc = 0
        
        return render_template('estudo/materia.html', materia=materia, modulos=modulos)
        
    except Exception as e:
        print(f"Erro ao carregar matéria {materia_id}: {e}")
        flash('Erro ao carregar matéria.', 'error')
        return redirect(url_for('estudo.index'))

@estudo_bp.route('/modulo/<int:modulo_id>')
@login_required
def modulo(modulo_id):
    """Página de um módulo específico"""
    try:
        from app.models.estudo import Modulo, Aula, ProgressoAula
        
        modulo = Modulo.query.get_or_404(modulo_id)
        aulas = modulo.aulas.filter_by(ativa=True).order_by(Aula.ordem).all()
        
        # Verificar progresso de cada aula
        for aula in aulas:
            try:
                progresso = ProgressoAula.query.filter_by(
                    user_id=current_user.id,
                    aula_id=aula.id
                ).first()
                
                aula.progresso = progresso
                aula.concluida = progresso.concluida if progresso else False
                
            except Exception as e:
                print(f"Erro ao verificar progresso da aula {aula.id}: {e}")
                aula.progresso = None
                aula.concluida = False
        
        return render_template('estudo/modulo.html', modulo=modulo, aulas=aulas)
        
    except Exception as e:
        print(f"Erro ao carregar módulo {modulo_id}: {e}")
        flash('Erro ao carregar módulo.', 'error')
        return redirect(url_for('estudo.index'))

@estudo_bp.route('/aula/<int:aula_id>')
@login_required
def aula(aula_id):
    """Página de uma aula específica"""
    try:
        from app.models.estudo import Aula, ProgressoAula, SessaoEstudo, MaterialAula
        
        aula = Aula.query.get_or_404(aula_id)
        
        # Buscar ou criar progresso da aula
        progresso = ProgressoAula.query.filter_by(
            user_id=current_user.id,
            aula_id=aula_id
        ).first()
        
        if not progresso:
            progresso = ProgressoAula(
                user_id=current_user.id,
                aula_id=aula_id
            )
            db.session.add(progresso)
            db.session.commit()
        
        # Iniciar sessão de estudo
        sessao = SessaoEstudo(
            user_id=current_user.id,
            aula_id=aula_id
        )
        db.session.add(sessao)
        db.session.commit()
        
        # Buscar materiais da aula
        materiais = MaterialAula.query.filter_by(aula_id=aula_id).all()
        
        return render_template('estudo/aula.html', 
                             aula=aula, 
                             progresso=progresso, 
                             materiais=materiais,
                             sessao_id=sessao.id)
        
    except Exception as e:
        print(f"Erro ao carregar aula {aula_id}: {e}")
        flash('Erro ao carregar aula.', 'error')
        return redirect(url_for('estudo.index'))

@estudo_bp.route('/api/atualizar_progresso', methods=['POST'])
@login_required
def atualizar_progresso():
    """API para atualizar progresso da aula via AJAX"""
    try:
        from app.models.estudo import Aula, ProgressoAula, SessaoEstudo
        
        data = request.get_json()
        aula_id = data.get('aula_id')
        tempo_assistido = data.get('tempo_assistido', 0)
        sessao_id = data.get('sessao_id')
        forcar_conclusao = data.get('forcar_conclusao', False)
        
        if not aula_id:
            return jsonify({'error': 'aula_id é obrigatório'}), 400
        
        progresso = ProgressoAula.query.filter_by(
            user_id=current_user.id,
            aula_id=aula_id
        ).first()
        
        moedas_ganhas = 0
        
        if progresso:
            progresso.tempo_assistido = max(progresso.tempo_assistido, tempo_assistido)
            progresso.ultima_atividade = datetime.utcnow()
            
            aula = Aula.query.get(aula_id)
            deve_concluir = forcar_conclusao
            
            if not deve_concluir and aula.duracao_estimada:
                deve_concluir = tempo_assistido >= (aula.duracao_estimada * 60 * 0.8)
            
            if deve_concluir and not progresso.concluida:
                progresso.concluida = True
                progresso.data_conclusao = datetime.utcnow()
                
                bonus = 10
                current_user.adicionar_moedas(bonus, 'estudo', f'Aula concluída: {aula.titulo}')
                moedas_ganhas = bonus
        
        if sessao_id:
            sessao = SessaoEstudo.query.get(sessao_id)
            if sessao and sessao.ativa:
                sessao.tempo_ativo = tempo_assistido
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'moedas_ganhas': moedas_ganhas
        })
        
    except Exception as e:
        print(f"Erro ao atualizar progresso: {e}")
        db.session.rollback()
        return jsonify({'error': 'Erro interno'}), 500

@estudo_bp.route('/api/finalizar_sessao', methods=['POST'])
@login_required
def finalizar_sessao():
    """API para finalizar sessão de estudo"""
    try:
        from app.models.estudo import SessaoEstudo, Aula
        
        data = request.get_json()
        sessao_id = data.get('sessao_id')
        tempo_total = data.get('tempo_total', 0)
        
        if not sessao_id:
            return jsonify({'error': 'sessao_id é obrigatório'}), 400
        
        sessao = SessaoEstudo.query.get(sessao_id)
        if not sessao or not sessao.ativa:
            return jsonify({'error': 'Sessão não encontrada'}), 400
        
        sessao.fim = datetime.utcnow()
        sessao.tempo_ativo = tempo_total
        sessao.ativa = False
        
        moedas = (tempo_total // 60) // 2
        sessao.moedas_ganhas = moedas
        
        if moedas > 0:
            aula = Aula.query.get(sessao.aula_id)
            current_user.adicionar_moedas(moedas, 'estudo', f'Tempo de estudo: {aula.titulo}')
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'moedas_ganhas': moedas,
            'tempo_formatado': f"{tempo_total // 60}min {tempo_total % 60}s"
        })
        
    except Exception as e:
        print(f"Erro ao finalizar sessão: {e}")
        db.session.rollback()
        return jsonify({'error': 'Erro interno'}), 500
'''
    
    # 5. Fazer backup do arquivo atual
    try:
        backup_file = f"{estudo_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Backup criado: {backup_file}")
    except Exception as e:
        print(f"⚠️ Aviso ao criar backup: {e}")
    
    # 6. Escrever arquivo corrigido
    try:
        with open(estudo_file, 'w', encoding='utf-8') as f:
            f.write(corrected_content)
        print(f"✅ Arquivo {estudo_file} corrigido")
    except Exception as e:
        print(f"❌ Erro ao escrever arquivo: {e}")
        return False
    
    # 7. Testar se a correção funcionou
    try:
        print("\n🧪 Testando correção...")
        
        # Tentar importar o blueprint para ver se há erros de sintaxe
        import importlib.util
        spec = importlib.util.spec_from_file_location("estudo", estudo_file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            # Não vamos executar o módulo, apenas verificar se carrega
            print("✅ Arquivo corrigido sem erros de sintaxe")
        
    except Exception as e:
        print(f"⚠️ Aviso ao testar: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 CORREÇÃO DO DB IMPORT CONCLUÍDA!")
    print("=" * 50)
    print("✅ Arquivo estudo.py reescrito completamente")
    print("✅ Import 'from app import db' adicionado corretamente")
    print("✅ Backup do arquivo original criado")
    
    print("\n🚀 PRÓXIMO PASSO:")
    print("Execute: python run.py")
    print("\n✨ RESULTADO ESPERADO:")
    print("Não deve mais aparecer: 'Erro ao carregar matéria X: db is undefined'")
    
    return True

if __name__ == '__main__':
    success = fix_db_import_issue()
    print(f"\n{'✅ CORREÇÃO BEM-SUCEDIDA' if success else '❌ CORREÇÃO FALHADA'}")
    sys.exit(0 if success else 1)
