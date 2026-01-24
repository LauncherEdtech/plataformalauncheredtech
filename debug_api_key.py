# debug_api_key.py - Execute este script na raiz do projeto para debugar

import os
from dotenv import load_dotenv

print("=== DEBUG: OPENAI API KEY ===")

# 1. Verificar arquivo .env
if os.path.exists('.env'):
    print("✅ Arquivo .env encontrado")
    with open('.env', 'r') as f:
        lines = f.readlines()
        for line in lines:
            if 'OPENAI_API_KEY' in line:
                print(f"✅ Linha encontrada no .env: {line.strip()[:30]}...")
                break
        else:
            print("❌ OPENAI_API_KEY não encontrada no .env")
else:
    print("❌ Arquivo .env não encontrado na raiz do projeto")

# 2. Verificar variável de ambiente (antes do load_dotenv)
env_before = os.environ.get('OPENAI_API_KEY')
print(f"ENV antes do load_dotenv: {'✅ Definida' if env_before else '❌ Não definida'}")

# 3. Carregar .env
try:
    load_dotenv()
    print("✅ load_dotenv() executado com sucesso")
except Exception as e:
    print(f"❌ Erro no load_dotenv(): {e}")

# 4. Verificar variável de ambiente (depois do load_dotenv)
env_after = os.environ.get('OPENAI_API_KEY')
print(f"ENV depois do load_dotenv: {'✅ Definida' if env_after else '❌ Não definida'}")

if env_after:
    print(f"Chave carregada: {env_after[:15]}... (tamanho: {len(env_after)})")

# 5. Testar contexto Flask
print("\n=== Testando contexto Flask ===")
try:
    from app import create_app
    app = create_app()
    with app.app_context():
        flask_key = app.config.get('OPENAI_API_KEY')
        print(f"Flask config: {'✅ Definida' if flask_key else '❌ Não definida'}")
        if flask_key:
            print(f"Chave no Flask: {flask_key[:15]}... (tamanho: {len(flask_key)})")
except Exception as e:
    print(f"❌ Erro ao testar Flask: {e}")

print("\n=== Resultado ===")
if env_after and len(env_after) > 40:
    print("✅ Configuração parece correta!")
else:
    print("❌ Problema na configuração da API key")
