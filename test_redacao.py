#!/usr/bin/env python3
"""
Teste específico da funcionalidade de redação
Execute: python3 test_redacao.py
"""

import sys
import traceback
from flask import Flask

def test_redacao_routes():
    """Testa as rotas de redação especificamente"""
    print("=== TESTANDO ROTAS DE REDAÇÃO ===")
    
    try:
        from app import create_app
        app = create_app()
        
        with app.test_client() as client:
            # Teste 1: Página principal de redação (sem login)
            print("Testando rota principal de redação...")
            response = client.get('/redacao/')
            print(f"GET /redacao/ -> Status: {response.status_code}")
            
            if response.status_code == 302:
                print("✓ Redirecionamento para login (esperado sem autenticação)")
            elif response.status_code == 500:
                print("✗ ERRO 500 encontrado!")
                return False
                
            # Teste 2: Página de nova redação (sem login)
            print("Testando rota nova redação...")
            response = client.get('/redacao/nova')
            print(f"GET /redacao/nova -> Status: {response.status_code}")
            
            if response.status_code == 302:
                print("✓ Redirecionamento para login (esperado sem autenticação)")
            elif response.status_code == 500:
                print("✗ ERRO 500 encontrado!")
                return False
                
            # Teste 3: Temas sugeridos
            print("Testando rota temas sugeridos...")
            response = client.get('/redacao/temas-sugeridos')
            print(f"GET /redacao/temas-sugeridos -> Status: {response.status_code}")
            
            # Teste 4: Dicas
            print("Testando rota dicas...")
            response = client.get('/redacao/dicas')
            print(f"GET /redacao/dicas -> Status: {response.status_code}")
            
        print("✓ Testes básicos de rota concluídos")
        return True
        
    except Exception as e:
        print(f"✗ Erro ao testar rotas: {e}")
        traceback.print_exc()
        return False

def test_redacao_service():
    """Testa o serviço de avaliação de redação"""
    print("\n=== TESTANDO SERVIÇO DE REDAÇÃO ===")
    
    try:
        from app.services.redacao_service import RedacaoService
        from app.models.redacao import Redacao
        from app import create_app, db
        
        app = create_app()
        with app.app_context():
            # Criar uma redação fake para teste
            fake_redacao = Redacao(
                titulo="Teste",
                conteudo="Esta é uma redação de teste com mais de 500 caracteres. " * 10,
                user_id=1,  # ID fake
                status="Enviada"
            )
            
            # Não salvar no banco, só testar o serviço
            print("Testando construção de prompt...")
            prompt = RedacaoService._construir_prompt(fake_redacao)
            print(f"✓ Prompt construído: {len(prompt)} caracteres")
            
            print("Testando resposta simulada...")
            resposta_sim = RedacaoService._resposta_simulada()
            print(f"✓ Resposta simulada gerada: {len(resposta_sim)} campos")
            
            print("Testando chamada da API (modo simulado)...")
            resposta_api = RedacaoService._chamar_api_chatgpt("teste", "simulado")
            print(f"✓ API chamada com sucesso: {type(resposta_api)}")
            
        return True
        
    except Exception as e:
        print(f"✗ Erro no serviço de redação: {e}")
        traceback.print_exc()
        return False

def test_template_rendering():
    """Testa renderização dos templates"""
    print("\n=== TESTANDO RENDERIZAÇÃO DE TEMPLATES ===")
    
    try:
        from app import create_app
        from flask import render_template_string
        
        app = create_app()
        with app.app_context():
            # Testar template básico
            template_test = """
            {% extends "layout.html" %}
            {% block content %}
            <h1>Teste</h1>
            {% endblock %}
            """
            
            try:
                result = render_template_string(template_test)
                print("✗ Template base não encontrado (esperado)")
            except Exception as e:
                if "layout.html" in str(e):
                    print("✓ Template engine funcionando (layout.html não encontrado é normal)")
                else:
                    print(f"✗ Erro no template engine: {e}")
                    return False
                    
        return True
        
    except Exception as e:
        print(f"✗ Erro nos templates: {e}")
        traceback.print_exc()
        return False

def test_authentication_flow():
    """Testa fluxo de autenticação"""
    print("\n=== TESTANDO FLUXO DE AUTENTICAÇÃO ===")
    
    try:
        from app import create_app
        from app.models.user import User
        from flask_login import login_user
        
        app = create_app()
        with app.test_client() as client:
            with app.app_context():
                # Verificar se existe pelo menos um usuário
                user = User.query.first()
                if user:
                    print(f"✓ Usuário encontrado: {user.email}")
                else:
                    print("⚠️ Nenhum usuário encontrado no banco")
                
                # Testar login page
                response = client.get('/login')
                print(f"GET /login -> Status: {response.status_code}")
                
                if response.status_code == 200:
                    print("✓ Página de login carregando")
                elif response.status_code == 500:
                    print("✗ ERRO 500 na página de login!")
                    return False
                    
        return True
        
    except Exception as e:
        print(f"✗ Erro no fluxo de autenticação: {e}")
        traceback.print_exc()
        return False

def test_static_files():
    """Testa acesso a arquivos estáticos"""
    print("\n=== TESTANDO ARQUIVOS ESTÁTICOS ===")
    
    try:
        from app import create_app
        import os
        
        app = create_app()
        
        # Verificar diretórios estáticos
        static_dir = os.path.join(app.instance_path, '../app/static')
        templates_dir = os.path.join(app.instance_path, '../app/templates')
        
        if os.path.exists('app/static'):
            print("✓ Diretório static encontrado")
        else:
            print("⚠️ Diretório static não encontrado")
            
        if os.path.exists('app/templates'):
            print("✓ Diretório templates encontrado")
            template_files = os.listdir('app/templates')
            print(f"  Templates encontrados: {len(template_files)} diretórios/arquivos")
            
            # Verificar se template de redação existe
            redacao_templates = 'app/templates/redacao'
            if os.path.exists(redacao_templates):
                redacao_files = os.listdir(redacao_templates)
                print(f"  Templates de redação: {redacao_files}")
            else:
                print("✗ Diretório de templates de redação não encontrado!")
                return False
        else:
            print("✗ Diretório templates não encontrado!")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ Erro ao verificar arquivos estáticos: {e}")
        return False

def main():
    """Executa todos os testes específicos"""
    print("TESTE ESPECÍFICO DA FUNCIONALIDADE DE REDAÇÃO")
    print("=" * 60)
    
    tests = [
        test_redacao_routes,
        test_redacao_service, 
        test_template_rendering,
        test_authentication_flow,
        test_static_files
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Erro em {test.__name__}: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print(f"Sucessos: {sum(results)}/{len(results)}")
    
    if not all(results):
        print("\n🚨 PROBLEMAS ENCONTRADOS:")
        print("Execute a aplicação com logs detalhados:")
        print("export FLASK_ENV=development")
        print("export FLASK_DEBUG=1") 
        print("python3 run.py")
    else:
        print("\n✅ Todos os testes passaram!")
        print("O erro 500 pode estar relacionado a:")
        print("1. Configuração do servidor web")
        print("2. Permissões de arquivo")
        print("3. Middleware específico")

if __name__ == "__main__":
    main()
