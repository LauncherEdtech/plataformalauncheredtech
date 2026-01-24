#!/usr/bin/env python3
"""
Script para verificar se o arquivo .env está sendo carregado corretamente
Uso: python3 check_env.py
"""

import os
import sys
from pathlib import Path

def print_header(title):
    """Imprime um cabeçalho formatado"""
    print(f"\n{'='*50}")
    print(f" {title}")
    print(f"{'='*50}")

def check_dotenv_installation():
    """Verifica se python-dotenv está instalado"""
    print_header("VERIFICANDO PYTHON-DOTENV")
    try:
        import dotenv
        print("✅ python-dotenv está instalado")
        try:
            print(f"   Versão: {dotenv.__version__}")
        except AttributeError:
            print("   Versão: [não disponível]")
        return True
    except ImportError:
        print("❌ python-dotenv NÃO está instalado")
        print("   Instale com: pip3 install python-dotenv")
        return False

def check_current_directory():
    """Mostra o diretório atual"""
    print_header("DIRETÓRIO ATUAL")
    current_dir = Path.cwd()
    print(f"📁 Diretório atual: {current_dir}")
    return current_dir

def find_env_files():
    """Procura por arquivos .env"""
    print_header("PROCURANDO ARQUIVOS .env")
    
    # Caminho específico mencionado
    specific_path = Path("/home/launchercursos/launcheredit/launcher-app/.env")
    
    current_dir = Path.cwd()
    env_files = []
    
    print(f"🔍 Verificando caminho específico: {specific_path}")
    if specific_path.exists():
        print("✅ Arquivo .env encontrado no caminho específico!")
        env_files.append(specific_path)
    else:
        print("❌ Arquivo .env NÃO encontrado no caminho específico")
    
    print(f"\n🔍 Procurando .env no diretório atual e superiores...")
    
    # Verifica diretório atual
    env_file = current_dir / ".env"
    if env_file.exists():
        print(f"✅ Encontrado: {env_file}")
        if env_file not in env_files:
            env_files.append(env_file)
    
    # Verifica diretórios superiores (até 5 níveis)
    for i in range(5):
        current_dir = current_dir.parent
        env_file = current_dir / ".env"
        if env_file.exists():
            print(f"✅ Encontrado: {env_file}")
            if env_file not in env_files:
                env_files.append(env_file)
    
    if not env_files:
        print("❌ Nenhum arquivo .env encontrado")
    
    return env_files

def read_env_file(env_path):
    """Lê e analisa o conteúdo do arquivo .env"""
    print(f"\n📖 Analisando: {env_path}")
    variables = {}
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"   📝 Total de linhas: {len(lines)}")
        
        for line_num, line in enumerate(lines, 1):
            original_line = line
            line = line.strip()
            
            # Pular linhas vazias e comentários
            if not line or line.startswith('#'):
                continue
            
            # Verificar se tem formato KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                variables[key] = value
                
                # Mostrar variável (mascarar valores sensíveis)
                if any(sensitive in key.upper() for sensitive in ['PASSWORD', 'SECRET', 'KEY']):
                    display_value = f"[{len(value)} caracteres]"
                else:
                    display_value = value[:50] + "..." if len(value) > 50 else value
                
                print(f"   ✅ {key} = {display_value}")
            else:
                print(f"   ⚠️  Linha {line_num} mal formatada: {original_line.strip()}")
        
        print(f"   📊 Total de variáveis válidas: {len(variables)}")
        return variables
        
    except Exception as e:
        print(f"   ❌ Erro ao ler arquivo: {e}")
        return {}

def test_dotenv_loading():
    """Testa o carregamento do .env com dotenv"""
    print_header("TESTANDO CARREGAMENTO COM DOTENV")
    
    try:
        from dotenv import load_dotenv
        
        # Salvar variáveis atuais que começam com OPENAI
        original_openai = os.environ.get('OPENAI_API_KEY')
        
        print("🔄 Executando load_dotenv()...")
        result = load_dotenv()
        
        print(f"📋 Resultado load_dotenv(): {result}")
        
        # Verificar se OPENAI_API_KEY foi carregada
        new_openai = os.environ.get('OPENAI_API_KEY')
        
        if new_openai:
            if new_openai != original_openai:
                print("✅ OPENAI_API_KEY foi carregada do .env!")
            else:
                print("ℹ️  OPENAI_API_KEY já estava definida")
            print(f"   Valor: {new_openai[:10]}..." if len(new_openai) > 10 else new_openai)
        else:
            print("❌ OPENAI_API_KEY não foi carregada")
            
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar dotenv: {e}")
        return False

def check_environment_variables():
    """Verifica variáveis de ambiente importantes"""
    print_header("VARIÁVEIS DE AMBIENTE ATUAIS")
    
    important_vars = [
        'OPENAI_API_KEY',
        'SECRET_KEY', 
        'DATABASE_URL',
        'FLASK_ENV',
        'FLASK_APP',
        'SMTP_SERVER',
        'SMTP_USER'
    ]
    
    found_vars = 0
    
    for var in important_vars:
        value = os.environ.get(var)
        if value:
            found_vars += 1
            if var == 'OPENAI_API_KEY':
                display_value = f"{value[:10]}..." if len(value) > 10 else value
                print(f"✅ {var}: {display_value}")
            elif any(sensitive in var.upper() for sensitive in ['PASSWORD', 'SECRET']):
                print(f"✅ {var}: [OCULTO - {len(value)} caracteres]")
            else:
                display_value = value[:50] + "..." if len(value) > 50 else value
                print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NÃO DEFINIDA")
    
    print(f"\n📊 Total de variáveis encontradas: {found_vars}/{len(important_vars)}")

def test_flask_app_context():
    """Testa se consegue carregar no contexto da aplicação Flask"""
    print_header("TESTANDO CONTEXTO DA APLICAÇÃO FLASK")
    
    try:
        # Tentar importar e criar a app
        sys.path.insert(0, '/home/launchercursos/launcheredit/launcher-app')
        
        print("🔄 Tentando importar a aplicação...")
        from app import create_app
        
        print("🔄 Criando aplicação Flask...")
        app = create_app()
        
        print("🔄 Testando dentro do contexto da app...")
        with app.app_context():
            openai_key = app.config.get('OPENAI_API_KEY')
            
            if openai_key:
                print(f"✅ OPENAI_API_KEY na config da app: {openai_key[:10]}...")
                print("✅ Aplicação conseguiu carregar a chave do .env!")
            else:
                print("❌ OPENAI_API_KEY não encontrada na config da app")
                
            # Verificar outras configs
            configs_to_check = ['SECRET_KEY', 'DATABASE_URL', 'FLASK_ENV']
            for config in configs_to_check:
                value = app.config.get(config)
                if value:
                    display = value[:30] + "..." if len(str(value)) > 30 else str(value)
                    print(f"✅ {config}: {display}")
                else:
                    print(f"❌ {config}: não definida")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar aplicação Flask: {e}")
        return False

def main():
    """Função principal"""
    print("🔍 VERIFICADOR DE ARQUIVO .env")
    print("="*50)
    
    # 1. Verificar instalação do python-dotenv
    dotenv_ok = check_dotenv_installation()
    
    # 2. Mostrar diretório atual
    current_dir = check_current_directory()
    
    # 3. Procurar arquivos .env
    env_files = find_env_files()
    
    # 4. Analisar arquivos encontrados
    if env_files:
        print_header("ANALISANDO ARQUIVOS .env")
        for env_file in env_files:
            variables = read_env_file(env_file)
    
    # 5. Testar carregamento se dotenv estiver disponível
    if dotenv_ok:
        test_dotenv_loading()
    
    # 6. Verificar variáveis de ambiente atuais
    check_environment_variables()
    
    # 7. Testar contexto da aplicação Flask
    test_flask_app_context()
    
    # 8. Resumo final
    print_header("RESUMO")
    if env_files:
        print("✅ Arquivos .env encontrados")
        if dotenv_ok:
            print("✅ python-dotenv disponível")
            print("✅ Sistema configurado corretamente")
        else:
            print("⚠️  Instale python-dotenv para carregamento automático")
    else:
        print("❌ Nenhum arquivo .env encontrado")
        print("💡 Crie um arquivo .env no diretório do projeto")
    
    print("\n🏁 Verificação concluída!")

if __name__ == "__main__":
    main()
