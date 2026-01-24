#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corrigir configurações de banco em launcheredit - SEM ERROS DE SINTAXE
Execute: python3 fix_banco_correto.py
"""

import os
import re
import shutil

# Configurações corretas
CORRECT_HOST = '34.63.141.69'
CORRECT_PORT = '5432'
CORRECT_DATABASE = 'plataforma'
CORRECT_USER = 'postgres'
CORRECT_PASSWORD = '22092021Dd$'

# String de conexão correta
CORRECT_URI = f"postgresql://postgres:22092021Dd$@34.63.141.69:5432/plataforma"

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

def fix_python_file(file_path):
    """Corrige arquivos Python com configurações de banco"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        backup_file(file_path)
        
        changes_made = 0
        
        # Lista de correções sem f-strings problemáticas
        # Corrige SQLALCHEMY_DATABASE_URI
        if "'postgresql://postgres:22092021Dd$@34.63.141.69:5432/plataforma'postgresql://[^']*'", f"'{CORRECT_URI}'", content)
            changes_made += 1
        
        if '"postgresql://postgres:22092021Dd$@34.63.141.69:5432/plataforma"postgresql://[^"]*"', f'"{CORRECT_URI}"', content)
            changes_made += 1
        
        # Corrige host localhost
        if "'host': '34.63.141.69'" in content:
            content = content.replace("'host': '34.63.141.69'", f"'host': '{CORRECT_HOST}'")
            changes_made += 1
        
        if '"host": "34.63.141.69"' in content:
            content = content.replace('"host": "34.63.141.69"', f'"host": "{CORRECT_HOST}"')
            changes_made += 1
        
        if "host='34.63.141.69'" in content:
            content = content.replace("host='34.63.141.69'", f"host='{CORRECT_HOST}'")
            changes_made += 1
        
        if 'host="34.63.141.69"' in content:
            content = content.replace('host="34.63.141.69"', f'host="{CORRECT_HOST}"')
            changes_made += 1
        
        # Corrige senha 1469
        if "'password': '22092021Dd$'" in content:
            content = content.replace("'password': '22092021Dd$'", f"'password': '{CORRECT_PASSWORD}'")
            changes_made += 1
        
        if '"password": "22092021Dd$"' in content:
            content = content.replace('"password": "22092021Dd$"', f'"password": "{CORRECT_PASSWORD}"')
            changes_made += 1
        
        if "password='22092021Dd$'" in content:
            content = content.replace("password='22092021Dd$'", f"password='{CORRECT_PASSWORD}'")
            changes_made += 1
        
        if 'password="22092021Dd$"' in content:
            content = content.replace('password="22092021Dd$"', f'password="{CORRECT_PASSWORD}"')
            changes_made += 1
        
        # Corrige database launcher_db
        if "'database': 'plataforma'" in content:
            content = content.replace("'database': 'plataforma'", f"'database': '{CORRECT_DATABASE}'")
            changes_made += 1
        
        if '"database": "plataforma"' in content:
            content = content.replace('"database": "plataforma"', f'"database": "{CORRECT_DATABASE}"')
            changes_made += 1
        
        if "database='plataforma'" in content:
            content = content.replace("database='plataforma'", f"database='{CORRECT_DATABASE}'")
            changes_made += 1
        
        if 'database="plataforma"' in content:
            content = content.replace('database="plataforma"', f'database="{CORRECT_DATABASE}"')
            changes_made += 1
        
        # Corrige conn_params dict completo
        if 'conn_params = {
        'host': '34.63.141.69',
        'port': '5432',
        'database': 'plataforma',
        'user': 'postgres',
        'password': '22092021Dd$'
    }',
        'port': '{CORRECT_PORT}',
        'database': '{CORRECT_DATABASE}',
        'user': '{CORRECT_USER}',
        'password': '{CORRECT_PASSWORD}'
    }}"""
            
            # Encontra o padrão conn_params = {
        'host': '34.63.141.69',
        'port': '5432',
        'database': 'plataforma',
        'user': 'postgres',
        'password': '22092021Dd$'
    }
            pattern = r'conn_params\s*=\s*{[^}]+}'
            if re.search(pattern, content):
                content = re.sub(pattern, new_conn_params, content)
                changes_made += 1
        
        # Corrige self.conn_params dict completo
        if 'self.conn_params = {
            'host': '34.63.141.69',
            'port': '5432',
            'database': 'plataforma',
            'user': 'postgres',
            'password': '22092021Dd$'
        }',
            'port': '{CORRECT_PORT}',
            'database': '{CORRECT_DATABASE}',
            'user': '{CORRECT_USER}',
            'password': '{CORRECT_PASSWORD}'
        }}"""
            
            pattern = r'self\.conn_params\s*=\s*{[^}]+}'
            if re.search(pattern, content):
                content = re.sub(pattern, new_self_conn, content)
                changes_made += 1
        
        # Salva apenas se houve mudanças
        if changes_made > 0 and content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return changes_made
        
        return 0
    except Exception as e:
        print(f"❌ Erro ao corrigir {file_path}: {e}")
        return 0

def fix_env_file(file_path):
    """Corrige arquivo .env"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        backup_file(file_path)
        
        # Corrige DATABASE_URL no .env
        if 'DATABASE_URL=' in content:
            content = re.sub(
                r'DATABASE_URL=postgresql://[^\s\n]*',
                f'DATABASE_URL={CORRECT_URI}',
                content
            )
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
    except Exception as e:
        print(f"❌ Erro ao corrigir {file_path}: {e}")
        return False

def fix_launcheredit():
    """Corrige configurações apenas em launcheredit"""
    print("🔧 CORREÇÃO DE CONFIGURAÇÕES - LAUNCHEREDIT")
    print("=" * 50)
    
    launcher_dir = '/home/launchercursos/launcheredit/launcher-app'
    
    if not os.path.exists(launcher_dir):
        print(f"❌ Pasta não encontrada: {launcher_dir}")
        return False
    
    print(f"📂 Corrigindo: {launcher_dir}")
    
    total_fixes = 0
    
    # Lista de arquivos importantes
    important_files = [
        '.env',
        'config.py',
        'app/__init__.py',
        'app/routes/__init__.py',
        'app/services/gerador_questoes.py',
        'app/routes/simulados.py'
    ]
    
    for file_rel_path in important_files:
        file_path = os.path.join(launcher_dir, file_rel_path)
        
        if os.path.exists(file_path):
            if file_rel_path == '.env':
                if fix_env_file(file_path):
                    print(f"✅ .env corrigido")
                    total_fixes += 1
            else:
                changes = fix_python_file(file_path)
                if changes > 0:
                    print(f"✅ {file_rel_path}: {changes} correções")
                    total_fixes += changes
    
    # Procura outros arquivos Python
    print(f"\n🔍 Procurando outros arquivos com configurações incorretas...")
    
    for root, dirs, files in os.walk(launcher_dir):
        dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, launcher_dir)
                
                if rel_path in important_files:
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if any(pattern in content for pattern in ['localhost', '1469', 'launcher_db']):
                        changes = fix_python_file(file_path)
                        if changes > 0:
                            print(f"✅ {rel_path}: {changes} correções")
                            total_fixes += changes
                except:
                    continue
    
    print(f"\n📊 RESUMO:")
    print(f"✅ Total de correções: {total_fixes}")
    print(f"🔧 Configurações aplicadas:")
    print(f"   🌐 Host: {CORRECT_HOST}")
    print(f"   🔑 Database: {CORRECT_DATABASE}")
    print(f"   🔒 Senha: {CORRECT_PASSWORD}")
    
    return total_fixes > 0

def verify_corrections():
    """Verifica se as correções funcionaram"""
    print(f"\n🔍 VERIFICANDO CORREÇÕES...")
    print("-" * 30)
    
    launcher_dir = '/home/launchercursos/launcheredit/launcher-app'
    
    check_files = [
        'app/__init__.py',
        'app/services/gerador_questoes.py',
        '.env'
    ]
    
    for file_rel_path in check_files:
        file_path = os.path.join(launcher_dir, file_rel_path)
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if CORRECT_HOST in content and CORRECT_DATABASE in content:
                    print(f"   ✅ {file_rel_path}: OK")
                else:
                    print(f"   ❌ {file_rel_path}: Ainda incorreto")
            except:
                print(f"   ⚠️ {file_rel_path}: Erro ao verificar")

if __name__ == "__main__":
    success = fix_launcheredit()
    
    if success:
        verify_corrections()
        
        print(f"\n🎉 CORREÇÃO CONCLUÍDA!")
        print(f"💡 Próximos passos:")
        print(f"   1. Pare a aplicação Flask atual (Ctrl+C)")
        print(f"   2. Execute: python3 run.py")
        print(f"   3. Teste 'Agendar Simulado'")
        print(f"   4. As questões agora vêm do banco remoto!")
    else:
        print(f"\n⚠️ Nenhuma correção necessária ou erro na execução")
