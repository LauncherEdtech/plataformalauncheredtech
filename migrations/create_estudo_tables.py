# migrations/create_estudo_tables.py
# Script para criar as tabelas do sistema de estudos manualmente

from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("🔧 Criando tabelas do sistema de estudos...")
    
    # SQL para criar as tabelas
    sql_commands = [
        # Tabela Materia
        """
        CREATE TABLE IF NOT EXISTS materia (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            descricao TEXT,
            icone VARCHAR(10) DEFAULT '📖',
            cor VARCHAR(7) DEFAULT '#00b4d8',
            ordem INTEGER DEFAULT 0,
            ativa BOOLEAN DEFAULT TRUE,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # Tabela Modulo
        """
        CREATE TABLE IF NOT EXISTS modulo (
            id SERIAL PRIMARY KEY,
            titulo VARCHAR(200) NOT NULL,
            descricao TEXT,
            materia_id INTEGER NOT NULL REFERENCES materia(id) ON DELETE CASCADE,
            ordem INTEGER DEFAULT 0,
            duracao_estimada INTEGER,
            dificuldade VARCHAR(20) DEFAULT 'medio',
            ativo BOOLEAN DEFAULT TRUE,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # Tabela Aula
        """
        CREATE TABLE IF NOT EXISTS aula (
            id SERIAL PRIMARY KEY,
            titulo VARCHAR(200) NOT NULL,
            descricao TEXT,
            conteudo TEXT,
            modulo_id INTEGER NOT NULL REFERENCES modulo(id) ON DELETE CASCADE,
            ordem INTEGER DEFAULT 0,
            duracao_estimada INTEGER,
            tipo VARCHAR(20) DEFAULT 'texto',
            url_video VARCHAR(500),
            ativa BOOLEAN DEFAULT TRUE,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # Tabela MaterialAula
        """
        CREATE TABLE IF NOT EXISTS material_aula (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(200) NOT NULL,
            arquivo VARCHAR(500),
            tipo VARCHAR(10),
            aula_id INTEGER NOT NULL REFERENCES aula(id) ON DELETE CASCADE,
            data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # Tabela ProgressoAula
        """
        CREATE TABLE IF NOT EXISTS progresso_aula (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
            aula_id INTEGER NOT NULL REFERENCES aula(id) ON DELETE CASCADE,
            tempo_assistido INTEGER DEFAULT 0,
            concluida BOOLEAN DEFAULT FALSE,
            data_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_conclusao TIMESTAMP,
            ultima_atividade TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            anotacoes TEXT,
            UNIQUE(user_id, aula_id)
        );
        """,
        
        # Tabela SessaoEstudo
        """
        CREATE TABLE IF NOT EXISTS sessao_estudo (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
            aula_id INTEGER NOT NULL REFERENCES aula(id) ON DELETE CASCADE,
            inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fim TIMESTAMP,
            tempo_ativo INTEGER DEFAULT 0,
            ativa BOOLEAN DEFAULT TRUE,
            moedas_ganhas INTEGER DEFAULT 0
        );
        """,
        
        # Tabela Moeda (se não existir)
        """
        CREATE TABLE IF NOT EXISTS moeda (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
            quantidade INTEGER NOT NULL,
            tipo VARCHAR(50),
            descricao VARCHAR(200),
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # Criar índices para melhor performance
        """
        CREATE INDEX IF NOT EXISTS idx_modulo_materia ON modulo(materia_id);
        CREATE INDEX IF NOT EXISTS idx_aula_modulo ON aula(modulo_id);
        CREATE INDEX IF NOT EXISTS idx_progresso_user ON progresso_aula(user_id);
        CREATE INDEX IF NOT EXISTS idx_progresso_aula ON progresso_aula(aula_id);
        CREATE INDEX IF NOT EXISTS idx_sessao_user ON sessao_estudo(user_id);
        CREATE INDEX IF NOT EXISTS idx_sessao_aula ON sessao_estudo(aula_id);
        CREATE INDEX IF NOT EXISTS idx_moeda_user ON moeda(user_id);
        """
    ]
    
    # Executar comandos
    for i, sql in enumerate(sql_commands, 1):
        try:
            db.session.execute(text(sql))
            db.session.commit()
            print(f"✅ Comando {i} executado com sucesso")
        except Exception as e:
            print(f"❌ Erro no comando {i}: {e}")
            db.session.rollback()
    
    # Verificar tabelas criadas
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()
    
    print("\n📊 Tabelas no banco após migração:")
    estudo_tables = ['materia', 'modulo', 'aula', 'material_aula', 'progresso_aula', 'sessao_estudo', 'moeda']
    for table in estudo_tables:
        if table in tables:
            print(f"✅ {table}")
        else:
            print(f"❌ {table} - NÃO CRIADA")
    
    print("\n✅ Migração concluída!")
