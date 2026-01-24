# setup_database.py
# Execute este script para configurar completamente o banco de dados

from app import create_app, db
from app.models.user import User
from app.models.estudo import Materia, Modulo, Aula, Moeda
from sqlalchemy import text
import sys

def setup_complete_database():
    """Configura completamente o banco de dados"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🚀 Iniciando configuração do banco de dados...")
            
            # 1. Verificar e adicionar coluna total_moedas
            print("\n📝 Verificando coluna total_moedas...")
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='user' AND column_name='total_moedas'
            """))
            
            if not result.fetchone():
                print("➕ Adicionando coluna total_moedas...")
                db.session.execute(text("""
                    ALTER TABLE "user" 
                    ADD COLUMN total_moedas INTEGER DEFAULT 0
                """))
            else:
                print("✅ Coluna total_moedas já existe!")
            
            # 2. Inicializar total_moedas para usuários existentes
            print("\n🔄 Inicializando moedas para usuários...")
            db.session.execute(text("""
                UPDATE "user" 
                SET total_moedas = 0 
                WHERE total_moedas IS NULL
            """))
            
            # 3. Verificar se as tabelas do sistema de estudos existem
            print("\n📚 Verificando tabelas do sistema de estudos...")
            
            tables_to_check = ['materia', 'modulo', 'aula', 'moeda', 'progresso_aula', 'sessao_estudo']
            
            for table in tables_to_check:
                result = db.session.execute(text(f"""
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE tablename = '{table}'
                """))
                
                if result.fetchone():
                    print(f"✅ Tabela {table} existe")
                else:
                    print(f"⚠️ Tabela {table} não encontrada - será criada automaticamente")
            
            # 4. Criar todas as tabelas se não existirem
            print("\n🏗️ Criando tabelas se necessário...")
            db.create_all()
            
            # 5. Criar dados de exemplo se não existirem
            print("\n📖 Verificando dados de exemplo...")
            
            if Materia.query.count() == 0:
                print("➕ Criando matérias de exemplo...")
                create_sample_data()
            else:
                print("✅ Dados já existem!")
            
            db.session.commit()
            print("\n🎉 Configuração do banco concluída com sucesso!")
            
        except Exception as e:
            print(f"\n❌ Erro na configuração: {e}")
            db.session.rollback()
            sys.exit(1)

def create_sample_data():
    """Cria dados de exemplo para o sistema de estudos"""
    
    # Matéria de Matemática
    matematica = Materia(
        nome="Matemática",
        descricao="Conteúdo completo de matemática para o ENEM",
        icone="🔢",
        cor="#FF6B6B",
        ordem=1,
        ativa=True
    )
    db.session.add(matematica)
    db.session.flush()  # Para obter o ID
    
    # Módulo de Funções
    modulo_funcoes = Modulo(
        titulo="Funções",
        descricao="Estudo completo de funções matemáticas",
        materia_id=matematica.id,
        ordem=1,
        duracao_estimada=180,
        dificuldade="medio",
        ativo=True
    )
    db.session.add(modulo_funcoes)
    db.session.flush()
    
    # Aula sobre funções
    aula_intro = Aula(
        titulo="Introdução às Funções",
        descricao="Conceitos básicos sobre funções matemáticas",
        conteudo="""
        <h2>O que são Funções?</h2>
        <p>Uma função é uma relação entre dois conjuntos onde cada elemento do primeiro conjunto está associado a exatamente um elemento do segundo conjunto.</p>
        
        <h3>Definição Formal</h3>
        <p>Uma função f: A → B é uma regra que associa a cada elemento x ∈ A um único elemento f(x) ∈ B.</p>
        
        <h3>Exemplos</h3>
        <ul>
        <li>f(x) = 2x + 1</li>
        <li>g(x) = x²</li>
        <li>h(x) = √x</li>
        </ul>
        """,
        modulo_id=modulo_funcoes.id,
        ordem=1,
        duracao_estimada=45,
        tipo="texto",
        ativa=True
    )
    db.session.add(aula_intro)
    
    # Matéria de Português
    portugues = Materia(
        nome="Português",
        descricao="Gramática, literatura e interpretação de textos",
        icone="📝",
        cor="#4ECDC4",
        ordem=2,
        ativa=True
    )
    db.session.add(portugues)
    db.session.flush()
    
    # Módulo de Gramática
    modulo_gramatica = Modulo(
        titulo="Gramática",
        descricao="Conceitos fundamentais da gramática portuguesa",
        materia_id=portugues.id,
        ordem=1,
        duracao_estimada=200,
        dificuldade="medio",
        ativo=True
    )
    db.session.add(modulo_gramatica)
    db.session.flush()
    
    # Aula de gramática
    aula_classes = Aula(
        titulo="Classes Gramaticais",
        descricao="Estudo das principais classes de palavras",
        conteudo="""
        <h2>Classes Gramaticais</h2>
        <p>As classes gramaticais são grupos de palavras que têm características semelhantes.</p>
        
        <h3>Classes Variáveis</h3>
        <ul>
        <li><strong>Substantivo:</strong> nomeia seres, objetos, sentimentos</li>
        <li><strong>Adjetivo:</strong> qualifica ou caracteriza o substantivo</li>
        <li><strong>Artigo:</strong> determina o substantivo</li>
        <li><strong>Pronome:</strong> substitui ou acompanha o substantivo</li>
        <li><strong>Numeral:</strong> indica quantidade ou ordem</li>
        <li><strong>Verbo:</strong> indica ação, estado ou fenômeno</li>
        </ul>
        
        <h3>Classes Invariáveis</h3>
        <ul>
        <li><strong>Advérbio:</strong> modifica verbo, adjetivo ou outro advérbio</li>
        <li><strong>Preposição:</strong> liga palavras</li>
        <li><strong>Conjunção:</strong> liga orações ou termos</li>
        <li><strong>Interjeição:</strong> exprime emoções</li>
        </ul>
        """,
        modulo_id=modulo_gramatica.id,
        ordem=1,
        duracao_estimada=50,
        tipo="texto",
        ativa=True
    )
    db.session.add(aula_classes)
    
    print("📚 Dados de exemplo criados!")

if __name__ == "__main__":
    setup_complete_database()
