#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para resolver conflito de rotas duplicadas para '/'
Execute: python3 fix_route_conflict.py
"""

import os
import re
import shutil

def backup_file(file_path):
    """Cria backup de um arquivo"""
    try:
        backup_path = file_path + '.backup_route'
        if not os.path.exists(backup_path):
            shutil.copy2(file_path, backup_path)
            return True
    except:
        pass
    return False

def fix_dashboard_route():
    """Remove ou modifica a rota conflitante no dashboard"""
    print("🔧 CORRIGINDO CONFLITO DE ROTAS")
    print("=" * 50)
    
    app_dir = '/home/launchercursos/launcheredit/launcher-app'
    
    # Procura pelo arquivo dashboard
    dashboard_files = [
        'app/routes/dashboard.py',
        'app/dashboard.py',
        'app/routes/main.py'
    ]
    
    for file_rel_path in dashboard_files:
        file_path = os.path.join(app_dir, file_rel_path)
        
        if os.path.exists(file_path):
            print(f"\n📄 Verificando: {file_rel_path}")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Procura por rotas '/'
                if "@dashboard_bp.route('/')" in content or '@dashboard_bp.route("/")' in content:
                    print(f"✅ Encontrada rota '/' conflitante em {file_rel_path}")
                    
                    backup_file(file_path)
                    
                    # Substitui a rota '/' por '/dashboard'
                    new_content = content.replace("@dashboard_bp.route('/')", "@dashboard_bp.route('/dashboard')")
                    new_content = new_content.replace('@dashboard_bp.route("/")', '@dashboard_bp.route("/dashboard")')
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    print(f"✅ Rota modificada: '/' -> '/dashboard' em {file_rel_path}")
                    return True
                
                elif ".route('/')" in content and 'dashboard' in file_rel_path.lower():
                    print(f"✅ Encontrada rota '/' genérica em {file_rel_path}")
                    
                    backup_file(file_path)
                    
                    # Modifica qualquer rota '/' para '/dashboard'
                    new_content = re.sub(r"\.route\(['\"]\/['\"]\)", ".route('/dashboard')", content)
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    print(f"✅ Rota genérica modificada em {file_rel_path}")
                    return True
                    
            except Exception as e:
                print(f"❌ Erro ao processar {file_path}: {e}")
    
    return False

def ensure_single_main_route():
    """Garante que só existe uma rota para '/'"""
    print(f"\n🏠 VERIFICANDO ROTA PRINCIPAL ÚNICA")
    print("-" * 30)
    
    app_dir = '/home/launchercursos/launcheredit/launcher-app'
    main_routes_path = os.path.join(app_dir, 'app/routes/main.py')
    
    if os.path.exists(main_routes_path):
        try:
            with open(main_routes_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verifica se tem a rota principal correta
            if "@main_bp.route('/')" in content:
                print("✅ Rota principal '/' encontrada em main.py")
                return True
            else:
                print("⚠️ Rota principal não encontrada, criando...")
                
                # Cria rota principal simples
                backup_file(main_routes_path)
                
                simple_main = '''from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Rota principal única - sem conflitos"""
    if current_user.is_authenticated:
        # Usuário logado - vai para dashboard
        return redirect(url_for('dashboard.index'))
    else:
        # Usuário não logado - vai para login
        return redirect(url_for('auth.login'))

@main_bp.route('/home')
def home():
    """Página inicial pública"""
    return render_template('index.html')
'''
                
                with open(main_routes_path, 'w', encoding='utf-8') as f:
                    f.write(simple_main)
                
                print("✅ Nova rota principal criada")
                return True
                
        except Exception as e:
            print(f"❌ Erro ao verificar main.py: {e}")
    
    return False

def update_dashboard_references():
    """Atualiza referências para a nova rota do dashboard"""
    print(f"\n🔗 ATUALIZANDO REFERÊNCIAS")
    print("-" * 30)
    
    app_dir = '/home/launchercursos/launcheredit/launcher-app'
    
    # Lista de arquivos que podem ter referências ao dashboard
    files_to_check = []
    
    # Encontra todos os arquivos Python
    for root, dirs, files in os.walk(app_dir):
        # Pula venv e __pycache__
        dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git']]
        
        for file in files:
            if file.endswith('.py'):
                files_to_check.append(os.path.join(root, file))
    
    updates_made = 0
    
    for file_path in files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Atualiza referências para dashboard.index
            if "url_for('dashboard.index')" in content:
                # Verifica se ainda existe a rota '/' para dashboard
                # Se não, precisa atualizar para '/dashboard'
                content = content.replace(
                    "url_for('dashboard.index')",
                    "url_for('dashboard.index')"  # Mantém o mesmo, só verificando
                )
            
            # Se houve mudanças, salva
            if content != original_content:
                backup_file(file_path)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                rel_path = os.path.relpath(file_path, app_dir)
                print(f"✅ Atualizado: {rel_path}")
                updates_made += 1
                
        except Exception as e:
            continue
    
    print(f"📊 {updates_made} arquivos atualizados")
    return updates_made > 0

def test_fixed_routes():
    """Testa se as rotas foram corrigidas"""
    print(f"\n🧪 TESTANDO ROTAS CORRIGIDAS")
    print("-" * 30)
    
    app_dir = '/home/launchercursos/launcheredit/launcher-app'
    
    try:
        os.chdir(app_dir)
        
        import sys
        sys.path.insert(0, app_dir)
        
        from app import create_app
        app = create_app()
        
        with app.app_context():
            print("✅ Aplicação inicializada")
            
            # Verifica rotas para '/'
            root_routes = []
            for rule in app.url_map.iter_rules():
                if rule.rule == '/':
                    root_routes.append(rule.endpoint)
            
            print(f"📍 Rotas para '/': {root_routes}")
            
            if len(root_routes) == 1:
                print("✅ Apenas uma rota para '/' - CONFLITO RESOLVIDO!")
                return True
            else:
                print(f"❌ Ainda há {len(root_routes)} rotas para '/'")
                return False
                
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def main():
    """Função principal"""
    print("⚡ RESOLVER CONFLITO DE ROTAS DUPLICADAS")
    print("=" * 50)
    print("Problema: Duas rotas registradas para '/'")
    print("Solução: Mover dashboard para '/dashboard'")
    print("=" * 50)
    
    fixes_applied = 0
    
    # Corrige rota conflitante do dashboard
    if fix_dashboard_route():
        fixes_applied += 1
    
    # Garante rota principal única
    if ensure_single_main_route():
        fixes_applied += 1
    
    # Atualiza referências
    if update_dashboard_references():
        fixes_applied += 1
    
    # Testa resultado
    if test_fixed_routes():
        print(f"\n🎉 CONFLITO RESOLVIDO!")
        print(f"✅ {fixes_applied} correções aplicadas")
        print(f"💡 Próximos passos:")
        print(f"   1. Pare a aplicação Flask (Ctrl+C)")
        print(f"   2. Execute: python3 run.py")
        print(f"   3. Acesse: http://SEU_IP:8080")
        print(f"   4. Dashboard agora em: http://SEU_IP:8080/dashboard")
        print(f"   5. Sem mais loops de redirect!")
    else:
        print(f"\n⚠️ Ainda há problemas")
        print(f"💡 Pode ser necessário verificar manualmente")

if __name__ == "__main__":
    main()
