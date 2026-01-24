# fix_database.py - Script para corrigir problemas no banco de dados

from app import create_app, db
from sqlalchemy import text

def fix_database():
    """Corrige problemas de estrutura do banco de dados"""
    
    app = create_app()
    
    with app.app_context():
        print("🔧 Iniciando correção do banco de dados...")
        
        try:
            # 1. Verificar se as tabelas existem
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            print(f"📋 Tabelas existentes: {existing_tables}")
            
            # 2. Criar tabelas que não existem
            if 'materia' not in existing_tables:
                print("📚 Criando tabela 'materia'...")
                db.session.execute(text("""
                    CREATE TABLE materia (
                        id SERIAL PRIMARY KEY,
                        nome VARCHAR(100) NOT NULL,
                        descricao TEXT,
                        icone VARCHAR(10) DEFAULT '📖',
                        cor VARCHAR(7) DEFAULT '#00b4d8',
                        ordem INTEGER DEFAULT 0,
                        ativa BOOLEAN DEFAULT true
                    )
                """))
                
            if 'modulo' not in existing_tables:
                print("📖 Criando tabela 'modulo'...")
                db.session.execute(text("""
                    CREATE TABLE modulo (
                        id SERIAL PRIMARY KEY,
                        titulo VARCHAR(200) NOT NULL,
                        descricao TEXT,
                        ordem INTEGER DEFAULT 1,
                        duracao_estimada INTEGER,
                        dificuldade VARCHAR(20) DEFAULT 'medio',
                        ativo BOOLEAN DEFAULT true,
                        materia_id INTEGER REFERENCES materia(id) ON DELETE CASCADE
                    )
                """))
                
            if 'aula' not in existing_tables:
                print("🎓 Criando tabela 'aula'...")
                db.session.execute(text("""
                    CREATE TABLE aula (
                        id SERIAL PRIMARY KEY,
                        titulo VARCHAR(200) NOT NULL,
                        descricao TEXT,
                        conteudo TEXT,
                        ordem INTEGER DEFAULT 1,
                        duracao_estimada INTEGER,
                        tipo VARCHAR(20) DEFAULT 'texto',
                        url_video VARCHAR(500),
                        ativa BOOLEAN DEFAULT true,
                        modulo_id INTEGER REFERENCES modulo(id) ON DELETE CASCADE
                    )
                """))
                
            if 'material_aula' not in existing_tables:
                print("📎 Criando tabela 'material_aula'...")
                db.session.execute(text("""
                    CREATE TABLE material_aula (
                        id SERIAL PRIMARY KEY,
                        nome VARCHAR(200) NOT NULL,
                        arquivo VARCHAR(500) NOT NULL,
                        tipo VARCHAR(10),
                        tamanho INTEGER,
                        aula_id INTEGER REFERENCES aula(id) ON DELETE CASCADE
                    )
                """))
                
            if 'progresso_aula' not in existing_tables:
                print("📈 Criando tabela 'progresso_aula'...")
                db.session.execute(text("""
                    CREATE TABLE progresso_aula (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
                        aula_id INTEGER REFERENCES aula(id) ON DELETE CASCADE,
                        tempo_assistido INTEGER DEFAULT 0,
                        concluida BOOLEAN DEFAULT false,
                        data_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        data_conclusao TIMESTAMP,
                        ultima_atividade TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, aula_id)
                    )
                """))
                
            if 'sessao_estudo' not in existing_tables:
                print("⏱️ Criando tabela 'sessao_estudo'...")
                db.session.execute(text("""
                    CREATE TABLE sessao_estudo (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
                        aula_id INTEGER REFERENCES aula(id) ON DELETE CASCADE,
                        inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        fim TIMESTAMP,
                        tempo_ativo INTEGER DEFAULT 0,
                        ativa BOOLEAN DEFAULT true,
                        moedas_ganhas INTEGER DEFAULT 0
                    )
                """))
                
            if 'moeda' not in existing_tables:
                print("💰 Criando tabela 'moeda'...")
                db.session.execute(text("""
                    CREATE TABLE moeda (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
                        quantidade INTEGER NOT NULL,
                        tipo VARCHAR(50),
                        descricao VARCHAR(200),
                        data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
            
            # 3. Remover colunas que não devem existir
            if 'materia' in existing_tables:
                try:
                    # Verificar se a coluna data_criacao existe e removê-la se necessário
                    columns = [col['name'] for col in inspector.get_columns('materia')]
                    if 'data_criacao' in columns:
                        print("🗑️ Removendo coluna 'data_criacao' da tabela 'materia'...")
                        db.session.execute(text("ALTER TABLE materia DROP COLUMN IF EXISTS data_criacao"))
                except Exception as e:
                    print(f"⚠️ Aviso ao verificar colunas: {e}")
            
            # 4. Adicionar campos faltantes no modelo User se necessário
            try:
                user_columns = [col['name'] for col in inspector.get_columns('user')]
                if 'total_moedas' not in user_columns:
                    print("💰 Adicionando campo 'total_moedas' ao usuário...")
                    db.session.execute(text("ALTER TABLE \"user\" ADD COLUMN total_moedas INTEGER DEFAULT 0"))
            except Exception as e:
                print(f"⚠️ Aviso ao adicionar campo total_moedas: {e}")
            
            # 5. Inserir dados de exemplo se as tabelas estão vazias
            materia_count = db.session.execute(text("SELECT COUNT(*) FROM materia")).scalar()
            if materia_count == 0:
                print("📚 Inserindo matérias de exemplo...")
                
                materias_exemplo = [
                    ("Matemática", "Matemática e suas Tecnologias", "🔢", "#FF6B6B", 1),
                    ("Português", "Linguagens, Códigos e suas Tecnologias", "📝", "#4ECDC4", 2),
                    ("História", "Ciências Humanas e suas Tecnologias", "🏛️", "#45B7D1", 3),
                    ("Geografia", "Ciências Humanas e suas Tecnologias", "🗺️", "#96CEB4", 4),
                    ("Física", "Ciências da Natureza e suas Tecnologias", "⚗️", "#FFEAA7", 5),
                    ("Química", "Ciências da Natureza e suas Tecnologias", "🧪", "#DDA0DD", 6),
                    ("Biologia", "Ciências da Natureza e suas Tecnologias", "🌱", "#98D8C8", 7)
                ]
                
                for nome, desc, icone, cor, ordem in materias_exemplo:
                    db.session.execute(text("""
                        INSERT INTO materia (nome, descricao, icone, cor, ordem, ativa)
                        VALUES (:nome, :desc, :icone, :cor, :ordem, true)
                    """), {"nome": nome, "desc": desc, "icone": icone, "cor": cor, "ordem": ordem})
            
            # 6. Commit das mudanças
            db.session.commit()
            print("✅ Correção do banco de dados concluída com sucesso!")
            
            # 7. Verificar estrutura final
            print("\n📋 Estrutura final das tabelas:")
            for table in ['materia', 'modulo', 'aula', 'progresso_aula', 'sessao_estudo', 'moeda']:
                if table in inspector.get_table_names():
                    columns = [col['name'] for col in inspector.get_columns(table)]
                    print(f"  {table}: {columns}")
            
        except Exception as e:
            print(f"❌ Erro durante a correção: {e}")
            db.session.rollback()
            raise
            
if __name__ == '__main__':
    fix_database()
