# setup_study_system.py
"""
Script de configuração completa do Sistema de Estudos
Execute este script após copiar todos os arquivos para configurar automaticamente o sistema.

Uso: python setup_study_system.py
"""

import os
import sys
from datetime import datetime

def print_step(step, message):
    """Imprime passo da configuração com formatação"""
    print(f"\n{'='*60}")
    print(f"PASSO {step}: {message}")
    print(f"{'='*60}")

def check_file_exists(file_path):
    """Verifica se arquivo existe"""
    if os.path.exists(file_path):
        print(f"✅ {file_path} - OK")
        return True
    else:
        print(f"❌ {file_path} - FALTANDO")
        return False

def create_directory(dir_path):
    """Cria diretório se não existir"""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"✅ Diretório criado: {dir_path}")
    else:
        print(f"✅ Diretório já existe: {dir_path}")

def setup_study_system():
    """Configuração principal do sistema de estudos"""
    
    print("🚀 CONFIGURAÇÃO DO SISTEMA DE ESTUDOS - PLATAFORMA LAUNCHER")
    print("=" * 70)
    
    # PASSO 1: Verificar arquivos essenciais
    print_step(1, "VERIFICANDO ARQUIVOS ESSENCIAIS")
    
    required_files = [
        'app/models/estudo.py',
        'app/models/user.py',
        'app/routes/estudo.py',
        'app/routes/dashboard.py',
        'app/templates/dashboard.html',
        'app/__init__.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not check_file_exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ ERRO: {len(missing_files)} arquivo(s) obrigatório(s) não encontrado(s)!")
        print("Por favor, copie os arquivos listados acima antes de continuar.")
        return False
    
    # PASSO 2: Criar diretórios necessários
    print_step(2, "CRIANDO DIRETÓRIOS")
    
    directories = [
        'app/static/uploads',
        'app/static/uploads/materiais',
        'app/static/uploads/temp',
        'app/templates/estudo',
        'app/templates/estudo/admin',
        'app/templates/errors'
    ]
    
    for directory in directories:
        create_directory(directory)
    
    # PASSO 3: Configurar permissões
    print_step(3, "CONFIGURANDO PERMISSÕES")
    
    try:
        os.chmod('app/static/uploads', 0o755)
        os.chmod('app/static/uploads/materiais', 0o755)
        print("✅ Permissões configuradas")
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível configurar permissões automaticamente: {e}")
        print("Configure manualmente: chmod -R 755 app/static/uploads/")
    
    # PASSO 4: Verificar dependências Python
    print_step(4, "VERIFICANDO DEPENDÊNCIAS")
    
    try:
        import flask
        import flask_sqlalchemy
        import flask_login
        import werkzeug
        print("✅ Dependências principais encontradas")
    except ImportError as e:
        print(f"❌ Dependência faltando: {e}")
        print("Execute: pip install flask flask-sqlalchemy flask-login flask-migrate werkzeug")
        return False
    
    # PASSO 5: Gerar arquivo de migração
    print_step(5, "PREPARANDO MIGRAÇÃO DO BANCO")
    
    migration_content = '''"""Add study system tables

Revision ID: add_study_system
Revises: 
Create Date: ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

revision = 'add_study_system'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add total_moedas to user table
    try:
        op.add_column('user', sa.Column('total_moedas', sa.Integer(), default=0))
    except:
        pass  # Column may already exist
    
    # Create study system tables
    op.create_table('materia',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=100), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('icone', sa.String(length=50), nullable=True),
        sa.Column('cor', sa.String(length=7), nullable=True),
        sa.Column('ordem', sa.Integer(), default=0),
        sa.Column('ativa', sa.Boolean(), default=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # ... (rest of the migration code)

def downgrade():
    # Drop tables
    op.drop_table('moeda')
    op.drop_table('sessao_estudo')
    op.drop_table('progresso_aula')
    op.drop_table('material_aula')
    op.drop_table('aula')
    op.drop_table('modulo')
    op.drop_table('materia')
'''
    
    # Criar diretório de migrações se não existir
    if not os.path.exists('migrations'):
        print("📁 Criando diretório de migrações...")
        os.makedirs('migrations/versions', exist_ok=True)
    
    print("✅ Arquivo de migração preparado")
    
    # PASSO 6: Gerar dados de exemplo
    print_step(6, "PREPARANDO DADOS DE EXEMPLO")
    
    sample_data_script = '''
# Dados de exemplo para o sistema de estudos
from app.models.estudo import Materia, Modulo, Aula
from app.models.notificacao import inicializar_conquistas
from app import db

def criar_dados_exemplo():
    """Cria dados de exemplo para teste"""
    
    # Matérias
    materias = [
        {
            'nome': 'Matemática',
            'descricao': 'Matemática e suas tecnologias para o ENEM',
            'icone': '🔢',
            'cor': '#FF6B6B',
            'ordem': 1
        },
        {
            'nome': 'Português',
            'descricao': 'Linguagens, códigos e suas tecnologias',
            'icone': '📚',
            'cor': '#4ECDC4',
            'ordem': 2
        },
        {
            'nome': 'História',
            'descricao': 'Ciências humanas e suas tecnologias',
            'icone': '🏛️',
            'cor': '#45B7D1',
            'ordem': 3
        }
    ]
    
    for mat_data in materias:
        if not Materia.query.filter_by(nome=mat_data['nome']).first():
            materia = Materia(**mat_data)
            db.session.add(materia)
    
    db.session.commit()
    
    # Módulos para Matemática
    matematica = Materia.query.filter_by(nome='Matemática').first()
    if matematica and not matematica.modulos.first():
        modulos_mat = [
            {
                'titulo': 'Funções',
                'descricao': 'Estudo completo de funções matemáticas',
                'materia_id': matematica.id,
                'ordem': 1,
                'duracao_estimada': 120,
                'dificuldade': 'medio'
            },
            {
                'titulo': 'Geometria',
                'descricao': 'Geometria plana e espacial',
                'materia_id': matematica.id,
                'ordem': 2,
                'duracao_estimada': 90,
                'dificuldade': 'dificil'
            }
        ]
        
        for mod_data in modulos_mat:
            modulo = Modulo(**mod_data)
            db.session.add(modulo)
    
    db.session.commit()
    
    # Inicializar conquistas
    inicializar_conquistas()
    
    print("✅ Dados de exemplo criados!")

if __name__ == '__main__':
    criar_dados_exemplo()
'''
    
    with open('create_sample_data.py', 'w', encoding='utf-8') as f:
        f.write(sample_data_script)
    
    print("✅ Script de dados de exemplo criado: create_sample_data.py")
    
    # PASSO 7: Instruções finais
    print_step(7, "PRÓXIMOS PASSOS")
    
    print("""
📋 INSTRUÇÕES PARA FINALIZAR A INSTALAÇÃO:

1. Execute a migração do banco de dados:
   flask db migrate -m "Add study system"
   flask db upgrade

2. (Opcional) Crie dados de exemplo:
   python create_sample_data.py

3. Torne um usuário administrador:
   flask shell
   >>> from app.models.user import User
   >>> from app import db
   >>> user = User.query.filter_by(email='SEU_EMAIL').first()
   >>> user.is_admin = True
   >>> db.session.commit()
   >>> exit()

4. Reinicie a aplicação:
   flask run

5. Acesse o painel administrativo:
   http://localhost:5000/estudo/admin

6. Crie suas primeiras matérias e módulos!

🎉 CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!
""")
    
    return True

def verify_installation():
    """Verifica se a instalação foi bem-sucedida"""
    print_step("VERIFICAÇÃO", "TESTANDO INSTALAÇÃO")
    
    try:
        # Tentar importar modelos
        from app.models.estudo import Materia, Modulo, Aula
        from app.routes.estudo import estudo_bp
        from app.routes.dashboard import dashboard_bp
        print("✅ Importações dos modelos: OK")
        
        # Verificar se diretórios existem
        required_dirs = [
            'app/static/uploads/materiais',
            'app/templates/estudo/admin'
        ]
        
        for dir_path in required_dirs:
            if os.path.exists(dir_path):
                print(f"✅ Diretório {dir_path}: OK")
            else:
                print(f"❌ Diretório {dir_path}: FALTANDO")
                return False
        
        print("\n🎉 VERIFICAÇÃO CONCLUÍDA: Sistema pronto para uso!")
        return True
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("Verifique se todos os arquivos foram copiados corretamente.")
        return False

if __name__ == '__main__':
    print("🚀 LAUNCHER ENEM 2025 - CONFIGURAÇÃO DO SISTEMA DE ESTUDOS")
    print("=" * 65)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--verify':
        verify_installation()
    else:
        success = setup_study_system()
        
        if success:
            print("\n" + "="*65)
            print("✅ CONFIGURAÇÃO COMPLETA!")
            print("Execute 'python setup_study_system.py --verify' para testar")
            print("="*65)
        else:
            print("\n" + "="*65)
            print("❌ CONFIGURAÇÃO INCOMPLETA!")
            print("Corrija os erros acima e execute novamente")
            print("="*65)