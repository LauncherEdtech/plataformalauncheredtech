# diagnostico_banco.py
"""
Script para diagnosticar problemas de conexão com PostgreSQL
"""

import psycopg2
import sys
import subprocess

def testar_conexao_direta():
    """Testa conexão direta com psycopg2"""
    print("\n" + "="*50)
    print("TESTE 1: CONEXAO DIRETA COM PSYCOPG2")
    print("="*50)
    
    # Configurações da sua string de conexão
    config = {
        'host': '34.63.141.69',
        'port': 5432,
        'user': 'postgres',
        'password': '22092021Dd$',
        'database': 'plataforma'
    }
    
    print(f"Tentando conectar:")
    print(f"  Host: {config['host']}")
    print(f"  Porta: {config['port']}")
    print(f"  Usuario: {config['user']}")
    print(f"  Senha: {'*' * len(config['password'])}")
    print(f"  Banco: {config['database']}")
    
    try:
        # Tentar conectar
        conn = psycopg2.connect(**config)
        print("[OK] Conexao direta bem-sucedida!")
        
        # Testar uma query
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        print(f"[INFO] Versao PostgreSQL: {version[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        print(f"[ERRO] Erro operacional: {e}")
        return False
    except Exception as e:
        print(f"[ERRO] Erro geral: {e}")
        return False

def testar_conexao_sem_banco():
    """Testa conexão sem especificar banco (para ver se banco existe)"""
    print("\n" + "="*50)
    print("TESTE 2: CONEXAO SEM ESPECIFICAR BANCO")
    print("="*50)
    
    config = {
        'host': '34.63.141.69',
        'port': 5432,
        'user': 'postgres',
        'password': '22092021Dd$',
        'database': 'postgres'  # Banco padrão
    }
    
    try:
        conn = psycopg2.connect(**config)
        print("[OK] Conectado ao PostgreSQL (banco padrao)")
        
        # Verificar se banco launcher_db existe
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 1 FROM pg_database WHERE datname = 'launcher_db'
        """)
        
        result = cursor.fetchone()
        if result:
            print("[OK] Banco 'launcher_db' existe!")
        else:
            print("[PROBLEMA] Banco 'launcher_db' NAO existe!")
            print("[SOLUCAO] Vou tentar criar o banco...")
            
            # Tentar criar banco
            conn.autocommit = True
            cursor.execute("CREATE DATABASE launcher_db")
            print("[OK] Banco 'launcher_db' criado com sucesso!")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        print(f"[ERRO] Nao consegue conectar ao PostgreSQL: {e}")
        return False
    except Exception as e:
        print(f"[ERRO] Erro ao verificar/criar banco: {e}")
        return False

def verificar_servico_postgres():
    """Verifica se serviço PostgreSQL está rodando"""
    print("\n" + "="*50)
    print("TESTE 3: VERIFICANDO SERVICO POSTGRESQL")
    print("="*50)
    
    try:
        # Verificar serviços do Windows
        resultado = subprocess.run(
            'powershell "Get-Service -Name *postgres* | Select-Object Name, Status"',
            shell=True, capture_output=True, text=True
        )
        
        if resultado.returncode == 0 and resultado.stdout.strip():
            print("[INFO] Servicos PostgreSQL encontrados:")
            print(resultado.stdout)
            
            # Verificar se algum está Running
            if "Running" in resultado.stdout:
                print("[OK] PostgreSQL esta rodando!")
                return True
            else:
                print("[PROBLEMA] PostgreSQL NAO esta rodando!")
                return False
        else:
            print("[INFO] Nenhum servico PostgreSQL encontrado via PowerShell")
            return False
            
    except Exception as e:
        print(f"[ERRO] Erro ao verificar servicos: {e}")
        return False

def testar_com_flask_app():
    """Testa conexão através da Flask app"""
    print("\n" + "="*50)
    print("TESTE 4: CONEXAO VIA FLASK APP")
    print("="*50)
    
    try:
        # Adicionar diretório atual ao path
        sys.path.insert(0, '.')
        
        from app import create_app, db
        print("[OK] Imports da app funcionaram")
        
        app = create_app()
        print("[OK] App Flask criada")
        
        with app.app_context():
            print("[INFO] Tentando conectar via SQLAlchemy...")
            
            # Tentar executar uma query
            result = db.engine.execute("SELECT 1 as test")
            row = result.fetchone()
            print(f"[OK] Query executada! Resultado: {row}")
            
            return True
            
    except Exception as e:
        print(f"[ERRO] Erro na Flask app: {e}")
        print(f"[ERRO] Tipo do erro: {type(e).__name__}")
        
        # Mostrar traceback completo para debug
        import traceback
        print("\n[DEBUG] Traceback completo:")
        traceback.print_exc()
        
        return False

def mostrar_string_conexao():
    """Mostra a string de conexão atual"""
    print("\n" + "="*50)
    print("VERIFICANDO STRING DE CONEXAO")
    print("="*50)
    
    try:
        sys.path.insert(0, '.')
        from app import create_app
        
        app = create_app()
        uri = app.config.get('SQLALCHEMY_DATABASE_URI')
        
        print(f"[INFO] String de conexao atual:")
        print(f"  {uri}")
        
        # Parsear componentes
        if uri and uri.startswith('postgresql://postgres:22092021Dd$@34.63.141.69:5432/plataforma'):
            # Formato: postgresql://user:password@host:port/database
            parts = uri.replace('postgresql://postgres:22092021Dd$@34.63.141.69:5432/plataforma', '').split('@')
            if len(parts) == 2:
                user_pass = parts[0]
                host_port_db = parts[1]
                
                user_parts = user_pass.split(':')
                host_parts = host_port_db.split('/')
                
                print(f"\n[INFO] Componentes:")
                print(f"  Usuario: {user_parts[0] if len(user_parts) > 0 else 'N/A'}")
                print(f"  Senha: {'*' * len(user_parts[1]) if len(user_parts) > 1 else 'N/A'}")
                print(f"  Host: {host_parts[0].split(':')[0] if len(host_parts) > 0 else 'N/A'}")
                print(f"  Porta: {host_parts[0].split(':')[1] if ':' in host_parts[0] else '5432'}")
                print(f"  Banco: {host_parts[1] if len(host_parts) > 1 else 'N/A'}")
        
    except Exception as e:
        print(f"[ERRO] Nao conseguiu ler string de conexao: {e}")

def main():
    print("DIAGNOSTICO COMPLETO DA CONEXAO COM BANCO")
    print("="*60)
    
    # Mostrar string de conexão
    mostrar_string_conexao()
    
    # Teste 1: Verificar serviço
    servico_ok = verificar_servico_postgres()
    
    # Teste 2: Conexão sem banco específico
    postgres_ok = testar_conexao_sem_banco()
    
    # Teste 3: Conexão direta
    conexao_direta_ok = testar_conexao_direta()
    
    # Teste 4: Conexão via Flask
    flask_ok = testar_com_flask_app()
    
    # Resumo final
    print("\n" + "="*60)
    print("RESUMO DO DIAGNOSTICO")
    print("="*60)
    
    print(f"Servico PostgreSQL: {'OK' if servico_ok else 'PROBLEMA'}")
    print(f"Conexao PostgreSQL: {'OK' if postgres_ok else 'PROBLEMA'}")
    print(f"Conexao direta psycopg2: {'OK' if conexao_direta_ok else 'PROBLEMA'}")
    print(f"Conexao via Flask: {'OK' if flask_ok else 'PROBLEMA'}")
    
    if flask_ok:
        print("\n[SUCESSO] Tudo funcionando! Pode executar o setup.")
    else:
        print("\n[NEXT STEPS] Proximos passos baseados no diagnostico:")
        
        if not servico_ok:
            print("1. Iniciar servico PostgreSQL")
            print("   - Abrir 'Servicos' do Windows")
            print("   - Procurar por 'postgresql' e iniciar")
        
        if not postgres_ok:
            print("2. Verificar credenciais PostgreSQL")
            print("   - Usuario: postgres")
            print("   - Senha: 1469")
            print("   - Tentar: psql -U postgres -h localhost")
        
        if postgres_ok and not conexao_direta_ok:
            print("3. Banco 'launcher_db' pode nao existir")
            print("   - Sera criado automaticamente no proximo teste")
        
        if conexao_direta_ok and not flask_ok:
            print("4. Problema na configuracao da Flask app")
            print("   - Verificar imports em app/__init__.py")
            print("   - Verificar string de conexao")

if __name__ == "__main__":
    main()