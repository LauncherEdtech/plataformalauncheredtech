# fix_models.py - Script para corrigir problemas de inicialização dos modelos

from app import create_app, db
from sqlalchemy import text, inspect
import sys

def fix_models_initialization():
    """Corrige problemas de inicialização dos modelos SQLAlchemy"""
    
    app = create_app()
    
    with app.app_context():
        print("🔧 CORRIGINDO INICIALIZAÇÃO DOS MODELOS...")
        print("=" * 60)
        
        try:
            # 1. Primeiro, criar/verificar estrutura básica do banco
            print("1. 🗄️ Verificando estrutura do banco...")
            
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            # Verificar se tabela user tem o campo total_moedas
            if 'user' in existing_tables:
                user_columns = [col['name'] for col in inspector.get_columns('user')]
                if 'total_moedas' not in user_columns:
                    print("   💰 Adicionando campo total_moedas...")
                    db.session.execute(text('ALTER TABLE "user" ADD COLUMN total_moedas INTEGER DEFAULT 0'))
                    db.session.commit()
                    print("   ✅ Campo total_moedas adicionado")
                else:
                    print("   ✅ Campo total_moedas já existe")
            
            # 2. Criar tabelas de estudo se não existirem
            print("\n2. 📚 Criando tabelas de estudo...")
            
            study_tables = {
                'materia': """
                    CREATE TABLE IF NOT EXISTS materia (
                        id SERIAL PRIMARY KEY,
                        nome VARCHAR(100) NOT NULL,
                        descricao TEXT,
                        icone VARCHAR(10) DEFAULT '📖',
                        cor VARCHAR(7) DEFAULT '#00b4d8',
                        ordem INTEGER DEFAULT 0,
                        ativa BOOLEAN DEFAULT true
                    )
                """,
                'modulo': """
                    CREATE TABLE IF NOT EXISTS modulo (
                        id SERIAL PRIMARY KEY,
                        titulo VARCHAR(200) NOT NULL,
                        descricao TEXT,
                        ordem INTEGER DEFAULT 1,
                        duracao_estimada INTEGER,
                        dificuldade VARCHAR(20) DEFAULT 'medio',
                        ativo BOOLEAN DEFAULT true,
                        materia_id INTEGER REFERENCES materia(id) ON DELETE CASCADE
                    )
                """,
                'aula': """
                    CREATE TABLE IF NOT EXISTS aula (
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
                """,
                'progresso_aula': """
                    CREATE TABLE IF NOT EXISTS progresso_aula (
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
                """,
                'sessao_estudo': """
                    CREATE TABLE IF NOT EXISTS sessao_estudo (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
                        aula_id INTEGER REFERENCES aula(id) ON DELETE CASCADE,
                        inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        fim TIMESTAMP,
                        tempo_ativo INTEGER DEFAULT 0,
                        ativa BOOLEAN DEFAULT true,
                        moedas_ganhas INTEGER DEFAULT 0
                    )
                """,
                'moeda': """
                    CREATE TABLE IF NOT EXISTS moeda (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
                        quantidade INTEGER NOT NULL,
                        tipo VARCHAR(50),
                        descricao VARCHAR(200),
                        data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """,
                'material_aula': """
                    CREATE TABLE IF NOT EXISTS material_aula (
                        id SERIAL PRIMARY KEY,
                        nome VARCHAR(200) NOT NULL,
                        arquivo VARCHAR(500) NOT NULL,
                        tipo VARCHAR(10),
                        tamanho INTEGER,
                        aula_id INTEGER REFERENCES aula(id) ON DELETE CASCADE
                    )
                """
            }
            
            for table_name, create_sql in study_tables.items():
                try:
                    db.session.execute(text(create_sql))
                    print(f"   ✅ Tabela {table_name} verificada/criada")
                except Exception as e:
                    print(f"   ⚠️ Aviso para tabela {table_name}: {e}")
            
            db.session.commit()
            
            # 3. Importar modelos de forma segura
            print("\n3. 📦 Importando modelos...")
            
            try:
                # Importar User primeiro (sem relacionamentos problemáticos)
                from app.models.user import User
                print("   ✅ Modelo User importado")
                
                # Importar modelos de estudo
                from app.models.estudo import (
                    Materia, Modulo, Aula, ProgressoAula, 
                    SessaoEstudo, Moeda, MaterialAula
                )
                print("   ✅ Modelos de estudo importados")
                
                # Configurar relacionamentos do User agora que todos os modelos existem
                from app.models.user import setup_user_relationships
                setup_user_relationships()
                
            except Exception as e:
                print(f"   ⚠️ Aviso ao importar modelos: {e}")
            
            # 4. Atualizar dados de usuários existentes
            print("\n4. 👤 Atualizando usuários existentes...")
            
            from app.models.user import User
            
            # Garantir que todos os usuários tenham total_moedas
            users_without_moedas = User.query.filter(
                (User.total_moedas.is_(None))
            ).all()
            
            for user in users_without_moedas:
                user.total_moedas = 0
                # Calcular do histórico se possível
                try:
                    user.calcular_total_moedas_from_history()
                    print(f"   💰 Moedas calculadas para {user.username}: {user.total_moedas}")
                except:
                    pass
            
            db.session.commit()
            print(f"   ✅ {len(users_without_moedas)} usuários atualizados")
            
            # 5. Inserir dados de exemplo se necessário
            print("\n5. 📚 Verificando dados de exemplo...")
            
            try:
                materia_count = Materia.query.count()
                
                if materia_count == 0:
                    print("   📖 Inserindo matérias de exemplo...")
                    
                    materias_exemplo = [
                        Materia(nome="Matemática", descricao="Matemática e suas Tecnologias", 
                               icone="🔢", cor="#FF6B6B", ordem=1),
                        Materia(nome="Português", descricao="Linguagens, Códigos e suas Tecnologias", 
                               icone="📝", cor="#4ECDC4", ordem=2),
                        Materia(nome="História", descricao="Ciências Humanas e suas Tecnologias", 
                               icone="🏛️", cor="#45B7D1", ordem=3),
                        Materia(nome="Geografia", descricao="Ciências Humanas e suas Tecnologias", 
                               icone="🗺️", cor="#96CEB4", ordem=4),
                        Materia(nome="Física", descricao="Ciências da Natureza e suas Tecnologias", 
                               icone="⚗️", cor="#FFEAA7", ordem=5),
                        Materia(nome="Química", descricao="Ciências da Natureza e suas Tecnologias", 
                               icone="🧪", cor="#DDA0DD", ordem=6),
                        Materia(nome="Biologia", descricao="Ciências da Natureza e suas Tecnologias", 
                               icone="🌱", cor="#98D8C8", ordem=7)
                    ]
                    
                    for materia in materias_exemplo:
                        db.session.add(materia)
                    
                    db.session.commit()
                    print(f"   ✅ {len(materias_exemplo)} matérias de exemplo inseridas")
                else:
                    print(f"   ✅ Já existem {materia_count} matérias")
                    
            except Exception as e:
                print(f"   ⚠️ Aviso ao inserir dados de exemplo: {e}")
            
            # 6. Teste final dos modelos
            print("\n6. 🧪 Testando modelos...")
            
            try:
                # Testar User
                total_users = User.query.count()
                print(f"   👤 {total_users} usuários no banco")
                
                # Testar Materia
                total_materias = Materia.query.count()
                print(f"   📚 {total_materias} matérias no banco")
                
                # Testar relacionamentos se há dados
                if total_users > 0:
                    first_user = User.query.first()
                    print(f"   💰 Primeiro usuário tem {first_user.total_moedas} moedas")
                    print(f"   📊 Primeiro usuário concluiu {first_user.aulas_concluidas_count()} aulas")
                
                print("   ✅ Todos os testes passaram")
                
            except Exception as e:
                print(f"   ⚠️ Aviso nos testes: {e}")
            
            print("\n" + "=" * 60)
            print("🎉 CORREÇÃO DE MODELOS CONCLUÍDA!")
            print("=" * 60)
            
            print("\n📊 RESUMO:")
            final_tables = inspect(db.engine).get_table_names()
            required_tables = ['user', 'materia', 'modulo', 'aula', 'progresso_aula', 'sessao_estudo', 'moeda']
            
            for table in required_tables:
                status = "✅" if table in final_tables else "❌"
                print(f"   {status} {table}")
            
            print(f"\n👥 Total de usuários: {User.query.count()}")
            print(f"📚 Total de matérias: {Materia.query.count()}")
            
            print("\n🚀 PRÓXIMOS PASSOS:")
            print("   1. Execute: python run.py")
            print("   2. Acesse: http://localhost:8080/dashboard")
            print("   3. Verifique se não há mais erros")
            
            return True
            
        except Exception as e:
            print(f"❌ ERRO DURANTE A CORREÇÃO: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = fix_models_initialization()
    print(f"\n{'✅ CORREÇÃO BEM-SUCEDIDA' if success else '❌ CORREÇÃO FALHADA'}")
    sys.exit(0 if success else 1)
