# setup_automatico.py
"""
Script para configuração automática do banco de questões
Execute: python setup_automatico.py
"""

import os
import sys
import subprocess
from pathlib import Path

def executar_comando(comando, descricao):
    """Executa um comando e mostra o resultado"""
    print(f"\n🔄 {descricao}...")
    print(f"Executando: {comando}")
    
    try:
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True)
        
        if resultado.returncode == 0:
            print(f"✅ {descricao} - Sucesso!")
            if resultado.stdout:
                print(f"Saída: {resultado.stdout}")
        else:
            print(f"❌ {descricao} - Erro!")
            print(f"Erro: {resultado.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao executar {comando}: {e}")
        return False
    
    return True

def verificar_postgres():
    """Verifica se PostgreSQL está rodando"""
    print("\n🔍 Verificando PostgreSQL...")
    
    try:
        resultado = subprocess.run("psql --version", shell=True, capture_output=True, text=True)
        if resultado.returncode == 0:
            print("✅ PostgreSQL encontrado!")
            print(f"Versão: {resultado.stdout.strip()}")
            return True
        else:
            print("❌ PostgreSQL não encontrado!")
            return False
    except:
        print("❌ Erro ao verificar PostgreSQL!")
        return False

def verificar_arquivos_dados(diretorio='.'):
    """Verifica se existem arquivos de dados"""
    print(f"\n🔍 Procurando arquivos de dados em {diretorio}...")
    
    padroes = ['*Data.txt', '*data.txt', '*DATA.txt']
    arquivos_encontrados = []
    
    for padrao in padroes:
        arquivos = list(Path(diretorio).glob(padrao))
        arquivos_encontrados.extend(arquivos)
    
    if arquivos_encontrados:
        print(f"✅ Encontrados {len(arquivos_encontrados)} arquivos:")
        for arquivo in arquivos_encontrados:
            print(f"  - {arquivo}")
        return True
    else:
        print("❌ Nenhum arquivo de dados encontrado!")
        print("Procure por arquivos como: ArtesData.txt, MatematicaData.txt, etc.")
        return False

def criar_diretorios():
    """Cria diretórios necessários"""
    print("\n📁 Criando diretórios...")
    
    diretorios = ['scripts', 'migrations']
    
    for diretorio in diretorios:
        os.makedirs(diretorio, exist_ok=True)
        print(f"✅ Diretório {diretorio} criado/verificado")

def main():
    print("=" * 60)
    print("🚀 CONFIGURAÇÃO AUTOMÁTICA DO BANCO DE QUESTÕES")
    print("=" * 60)
    
    # 1. Verificar pré-requisitos
    print("\n📋 VERIFICANDO PRÉ-REQUISITOS")
    
    if not verificar_postgres():
        print("\n❌ Configure o PostgreSQL antes de continuar!")
        sys.exit(1)
    
    if not verificar_arquivos_dados():
        print("\n❌ Coloque seus arquivos de dados no diretório atual!")
        sys.exit(1)
    
    # 2. Criar diretórios
    criar_diretorios()
    
    # 3. Configurar Flask-Migrate (se necessário)
    print("\n🔧 CONFIGURANDO MIGRATIONS")
    
    if not os.path.exists('migrations'):
        if not executar_comando("flask db init", "Inicializando Flask-Migrate"):
            print("⚠️ Erro ao inicializar migrations, mas continuando...")
    
    # 4. Criar migration
    if executar_comando("flask db migrate -m 'Criar tabela questoes_base'", 
                       "Criando migration"):
        # 5. Aplicar migration
        executar_comando("flask db upgrade", "Aplicando migration")
    
    # 6. Migrar questões
    print("\n📊 MIGRANDO QUESTÕES")
    executar_comando("python scripts/migrar_questoes.py", "Migrando questões para o banco")
    
    # 7. Verificar migração
    print("\n📈 VERIFICANDO MIGRAÇÃO")
    executar_comando("python scripts/admin_questoes.py stats", "Estatísticas do banco")
    executar_comando("python scripts/admin_questoes.py validate", "Validando questões")
    
    # 8. Criar simulado de teste
    print("\n🎯 CRIANDO SIMULADO DE TESTE")
    
    # Primeiro, vamos verificar se existe usuário ID 1
    resultado_teste = subprocess.run(
        "python -c \"from app import create_app, db; from app.models.user import User; app=create_app(); app.app_context().push(); print('Usuários:', User.query.count())\"",
        shell=True, capture_output=True, text=True
    )
    
    if resultado_teste.returncode == 0 and "Usuários: 0" not in resultado_teste.stdout:
        executar_comando(
            "python scripts/gerador_simulados.py materia 1 'Matemática' --quantidade 5",
            "Criando simulado de teste"
        )
    else:
        print("⚠️ Nenhum usuário encontrado. Crie um usuário primeiro para testar simulados.")
    
    # 9. Resumo final
    print("\n" + "=" * 60)
    print("✅ CONFIGURAÇÃO CONCLUÍDA!")
    print("=" * 60)
    
    print("""
📚 PRÓXIMOS PASSOS:

1. Verificar dados migrados:
   python scripts/admin_questoes.py stats

2. Listar questões por matéria:
   python scripts/admin_questoes.py list --materia "Matemática"

3. Criar simulado para usuário:
   python scripts/gerador_simulados.py enem USER_ID

4. Ver detalhes de uma questão:
   python scripts/admin_questoes.py show QUESTAO_ID

📁 ARQUIVOS CRIADOS:
   - app/models/questao.py (modelos atualizados)
   - scripts/migrar_questoes.py (migração)
   - scripts/admin_questoes.py (administração)
   - scripts/gerador_simulados.py (gerador de simulados)

🎯 INTEGRAÇÃO:
   - Suas questões estão no PostgreSQL
   - Explicações das respostas incluídas
   - Sistema pronto para gerar simulados
   - Interface administrativa disponível

💡 DICAS:
   - Backup regular: pg_dump -t questoes_base
   - Monitorar desempenho das questões
   - Usar admin_questoes.py para gerenciar
   - Personalizar dificuldade conforme uso

🚀 Seu banco de questões está pronto para uso!
""")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Configuração interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro durante configuração: {e}")
        sys.exit(1)