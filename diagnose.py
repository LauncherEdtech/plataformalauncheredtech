#!/usr/bin/env python3
"""
Script de diagnóstico para aplicação Flask
Execute: python3 diagnose.py
"""

import os
import sys
import traceback
from dotenv import load_dotenv

def test_env():
    """Testa variáveis de ambiente"""
    print("=== TESTANDO VARIÁVEIS DE AMBIENTE ===")
    load_dotenv()
    
    vars_to_check = [
        'SECRET_KEY', 'OPENAI_API_KEY', 'DB_HOST', 
        'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD'
    ]
    
    for var in vars_to_check:
        value = os.environ.get(var)
        if value:
            if 'KEY' in var or 'PASSWORD' in var:
                print(f"✓ {var}: {value[:10]}...")
            else:
                print(f"✓ {var}: {value}")
        else:
            print(f"✗ {var}: NÃO CONFIGURADA")

def test_imports():
    """Testa imports principais"""
    print("\n=== TESTANDO IMPORTS ===")
    
    imports_to_test = [
        ('flask', 'Flask'),
        ('app', 'create_app'),
        ('app.models.user', 'User'),
        ('app.models.redacao', 'Redacao'),
        ('app.services.redacao_service', 'RedacaoService'),
        ('app.routes.redacao', 'redacao_bp'),
    ]
    
    for module, item in imports_to_test:
        try:
            exec(f"from {module} import {item}")
            print(f"✓ {module}.{item}")
        except Exception as e:
            print(f"✗ {module}.{item}: {e}")

def test_database():
    """Testa conexão com banco"""
    print("\n=== TESTANDO BANCO DE DADOS ===")
    
    try:
        from app import create_app, db
        from sqlalchemy import inspect, text
        
        app = create_app()
        with app.app_context():
            # Testar conexão básica
            try:
                db.session.execute(text('SELECT 1'))
                print("✓ Conexão com banco: OK")
            except Exception as e:
                print(f"✗ Conexão com banco: {e}")
                return
            
            # Verificar tabelas
            try:
                inspector = inspect(db.engine)
                tables = inspector.get_table_names()
                print(f"✓ Tabelas encontradas ({len(tables)}): {', '.join(tables[:5])}...")
                
                # Verificar tabelas específicas
                required_tables = ['user', 'redacao', 'simulado']
                for table in required_tables:
                    if table in tables:
                        print(f"✓ Tabela '{table}': Existe")
                    else:
                        print(f"✗ Tabela '{table}': Não encontrada")
                        
            except Exception as e:
                print(f"✗ Erro ao verificar tabelas: {e}")
                
    except Exception as e:
        print(f"✗ Erro geral no banco: {e}")
        traceback.print_exc()

def test_openai_api():
    """Testa configuração da OpenAI API"""
    print("\n=== TESTANDO OPENAI API ===")
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("✗ OPENAI_API_KEY não configurada - usando modo simulado")
        return
    
    if api_key == "simulado" or len(api_key) < 20:
        print("✓ Modo simulado ativado (chave inválida)")
        return
    
    try:
        import requests
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get("https://api.openai.com/v1/models", headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✓ OpenAI API: Chave válida")
        elif response.status_code == 401:
            print("✗ OpenAI API: Chave inválida")
        else:
            print(f"✗ OpenAI API: Erro {response.status_code}")
            
    except Exception as e:
        print(f"✗ Erro ao testar OpenAI API: {e}")

def test_app_creation():
    """Testa criação da aplicação"""
    print("\n=== TESTANDO CRIAÇÃO DA APP ===")
    
    try:
        from app import create_app
        app = create_app()
        print("✓ Aplicação criada com sucesso")
        
        # Testar blueprints
        blueprints = [bp.name for bp in app.blueprints.values()]
        print(f"✓ Blueprints registrados: {', '.join(blueprints)}")
        
        # Testar rota básica
        with app.test_client() as client:
            response = client.get('/healthz')
            if response.status_code == 200:
                print("✓ Rota de health check: OK")
            else:
                print(f"✗ Rota de health check: {response.status_code}")
                
    except Exception as e:
        print(f"✗ Erro ao criar aplicação: {e}")
        traceback.print_exc()

def main():
    """Executa todos os testes"""
    print("DIAGNÓSTICO DA APLICAÇÃO FLASK")
    print("=" * 50)
    
    test_env()
    test_imports()
    test_database()
    test_openai_api()
    test_app_creation()
    
    print("\n" + "=" * 50)
    print("DIAGNÓSTICO CONCLUÍDO")
    print("\nSe houver erros marcados com ✗, corrija-os antes de executar a aplicação.")

if __name__ == "__main__":
    main()

