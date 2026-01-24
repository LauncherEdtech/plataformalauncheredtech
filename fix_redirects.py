#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para diagnosticar e corrigir loop de redirects no Flask
Execute: python3 fix_redirects.py
"""

import os
import re
import shutil

def backup_file(file_path):
    """Cria backup de um arquivo"""
    try:
        backup_path = file_path + '.backup'
        if not os.path.exists(backup_path):
            shutil.copy2(file_path, backup_path)
            return True
    except:
        pass
    return False

def analyze_routes():
    """Analisa as rotas para encontrar problemas de redirect"""
    print("🔍 ANÁLISE DE ROTAS E REDIRECTS")
    print("=" * 50)
    
    app_dir = '/home/launchercursos/launcheredit/launcher-app'
    
    # Arquivos importantes para analisar
    files_to_check = [
        'app/__init__.py',
        'app/routes/__init__.py',
        'run.py',
        'app/routes/auth.py',
        'app/routes/main.py'
    ]
    
    for file_rel_path in files_to_check:
        file_path = os.path.join(app_dir, file_rel_path)
        
        if os.path.exists(file_path):
            print(f"\n📄 Analisando: {file_rel_path}")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Procura por padrões problemáticos
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    line_lower = line.lower().strip()
                    
                    # Procura por redirects problemáticos
                    if 'redirect' in line_lower and ('/' in line or 'url_for' in line):
                        print(f"   🔄 Linha {i}: {line.strip()}")
                    
                    # Procura por login_required
                    if '@login_required' in line:
                        print(f"   🔒 Linha {i}: {line.strip()}")
                        if i < len(lines):
                            print(f"       Próxima linha: {lines[i].strip()}")
                    
                    # Procura por rotas principais
                    if "@app.route('/')" in line or '@app.route("/")' in line:
                        print(f"   🏠 Linha {i}: {line.strip()}")
                        if i < len(lines):
                            print(f"       Próxima linha: {lines[i].strip()}")
                    
                    # Procura por Blueprint routes
                    if '.route(' in line and ("'/' " in line or '"/")' in line):
                        print(f"   📍 Linha {i}: {line.strip()}")
                
            except Exception as e:
                print(f"   ❌ Erro ao ler: {e}")

def fix_main_route():
    """Corrige problemas na rota principal"""
    print(f"\n🔧 CORRIGINDO ROTA PRINCIPAL")
    print("-" * 30)
    
    app_dir = '/home/launchercursos/launcheredit/launcher-app'
    
    # Verifica se existe routes/main.py
    main_routes_path = os.path.join(app_dir, 'app/routes/main.py')
    
    if os.path.exists(main_routes_path):
        try:
            with open(main_routes_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            backup_file(main_routes_path)
            
            # Corrige rota principal que pode estar causando loop
            if '@login_required' in content and 'def index()' in content:
                print("✅ Encontrada rota principal com @login_required")
                
                # Remove @login_required da rota principal se estiver causando problema
                new_content = content.replace('@login_required\ndef index():', 'def index():')
                
                # Adiciona verificação manual de login
                if 'current_user.is_authenticated' not in new_content:
                    new_content = new_content.replace(
                        'def index():',
                        '''def index():
    # Verifica se usuário está logado
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))'''
                    )
                
                with open(main_routes_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print("✅ Rota principal corrigida")
                return True
                
        except Exception as e:
            print(f"❌ Erro ao corrigir main.py: {e}")
    
    return False

def create_simple_main_route():
    """Cria uma rota principal simples e funcional"""
    print(f"\n🆕 CRIANDO ROTA PRINCIPAL SIMPLES")
    print("-" * 30)
    
    app_dir = '/home/launchercursos/launcheredit/launcher-app'
    main_routes_path = os.path.join(app_dir, 'app/routes/main.py')
    
    simple_main_content = '''from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Rota principal sem loop de redirect"""
    if current_user.is_authenticated:
        # Usuário logado - vai para dashboard
        return redirect(url_for('dashboard.index'))
    else:
        # Usuário não logado - mostra página inicial ou vai para login
        return redirect(url_for('auth.login'))

@main_bp.route('/home')
def home():
    """Página inicial pública"""
    return render_template('index.html')
'''
    
    try:
        backup_file(main_routes_path)
        
        with open(main_routes_path, 'w', encoding='utf-8') as f:
            f.write(simple_main_content)
        
        print("✅ Nova rota principal criada")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar rota: {e}")
        return False

def fix_app_init():
    """Corrige problemas no __init__.py da app"""
    print(f"\n🔧 VERIFICANDO APP/__INIT__.PY")
    print("-" * 30)
    
    app_dir = '/home/launchercursos/launcheredit/launcher-app'
    init_path = os.path.join(app_dir, 'app/__init__.py')
    
    if os.path.exists(init_path):
        try:
            with open(init_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verifica se tem configuração de login
            has_login_manager = 'LoginManager' in content
            has_login_view = 'login_manager.login_view' in content
            
            print(f"LoginManager presente: {'✅' if has_login_manager else '❌'}")
            print(f"Login view configurada: {'✅' if has_login_view else '❌'}")
            
            if has_login_manager and not has_login_view:
                print("🔧 Adicionando configuração de login_view...")
                
                backup_file(init_path)
                
                # Adiciona configuração de login_view
                if 'login_manager = LoginManager()' in content:
                    content = content.replace(
                        'login_manager = LoginManager()',
                        '''login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Faça login para acessar esta página.'
    login_manager.login_message_category = 'info' '''
                    )
                    
                    with open(init_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    print("✅ Configuração de login adicionada")
                    return True
            
        except Exception as e:
            print(f"❌ Erro ao verificar __init__.py: {e}")
    
    return False

def test_routes():
    """Testa as rotas principais"""
    print(f"\n🧪 TESTANDO CONFIGURAÇÃO")
    print("-" * 30)
    
    app_dir = '/home/launchercursos/launcheredit/launcher-app'
    
    try:
        # Muda para o diretório da aplicação
        os.chdir(app_dir)
        
        # Testa importação da aplicação
        import sys
        sys.path.insert(0, app_dir)
        
        try:
            from app import create_app
            app = create_app()
            
            with app.app_context():
                print("✅ Aplicação inicializada sem erros")
                
                # Lista as rotas registradas
                print("📍 Rotas registradas:")
                for rule in app.url_map.iter_rules():
                    print(f"   {rule.rule} -> {rule.endpoint}")
                
                return True
                
        except Exception as e:
            print(f"❌ Erro ao inicializar app: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def main():
    """Função principal"""
    print("🔄 CORRETOR DE LOOPS DE REDIRECT")
    print("=" * 50)
    
    # Análise inicial
    analyze_routes()
    
    # Tentativas de correção
    fixes_applied = 0
    
    if fix_app_init():
        fixes_applied += 1
    
    if fix_main_route():
        fixes_applied += 1
    
    if fixes_applied == 0:
        if create_simple_main_route():
            fixes_applied += 1
    
    # Teste final
    if test_routes():
        print(f"\n🎉 CORREÇÕES APLICADAS!")
        print(f"💡 Próximos passos:")
        print(f"   1. Pare a aplicação Flask (Ctrl+C)")
        print(f"   2. Execute: python3 run.py")
        print(f"   3. Acesse: http://SEU_IP:8080")
        print(f"   4. O loop de redirects deve estar resolvido!")
    else:
        print(f"\n⚠️ Ainda há problemas na configuração")
        print(f"💡 Verifique manualmente:")
        print(f"   - app/routes/main.py")
        print(f"   - app/routes/auth.py")
        print(f"   - app/__init__.py")

if __name__ == "__main__":
    main()
