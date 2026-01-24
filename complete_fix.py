# complete_fix.py - Script de correção completa para todos os erros

from app import create_app, db
from sqlalchemy import text, inspect
from app.models.user import User
import sys

def complete_fix():
    """Correção completa de todos os problemas encontrados"""
    
    app = create_app()
    
    with app.app_context():
        print("🔧 INICIANDO CORREÇÃO COMPLETA...")
        print("=" * 60)
        
        try:
            # 1. Corrigir problema do ranking (total_moedas como property vs int)
            print("1. 💰 Corrigindo problema do ranking...")
            
            # Verificar se usuários têm total_moedas como None
            usuarios_sem_moedas = User.query.filter(
                (User.total_moedas.is_(None)) | (User.total_moedas < 0)
            ).all()
            
            for usuario in usuarios_sem_moedas:
                print(f"   Corrigindo usuário {usuario.username}...")
                usuario.total_moedas = 0
            
            # Calcular moedas baseado no histórico se existir tabela Moeda
            try:
                from app.models.estudo import Moeda
                from sqlalchemy import func
                
                usuarios_com_historico = db.session.query(
                    User.id,
                    func.sum(Moeda.quantidade).label('total_moedas_calc')
                ).join(Moeda, User.id == Moeda.user_id).group_by(User.id).all()
                
                for user_id, total_calc in usuarios_com_historico:
                    usuario = User.query.get(user_id)
                    if usuario and (usuario.total_moedas == 0 or usuario.total_moedas is None):
                        usuario.total_moedas = max(0, total_calc or 0)
                        print(f"   Calculado {total_calc} moedas para {usuario.username}")
                        
            except ImportError:
                print("   Tabela Moeda não existe ainda, pulando cálculo de histórico")
            
            db.session.commit()
            print("   ✅ Problema do ranking corrigido")
            
            # 2. Verificar e corrigir estrutura das tabelas
            print("\n2. 📋 Verificando estrutura das tabelas...")
            
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            # Remover coluna problemática se existir
            if 'materia' in existing_tables:
                materia_columns = [col['name'] for col in inspector.get_columns('materia')]
                if 'data_criacao' in materia_columns:
                    print("   🗑️ Removendo coluna problemática 'data_criacao'...")
                    db.session.execute(text("ALTER TABLE materia DROP COLUMN data_criacao"))
                    db.session.commit()
            
            # Criar tabelas que não existem
            required_tables = {
                'materia': """
                    CREATE TABLE materia (
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
                """,
                'aula': """
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
                """,
                'material_aula': """
                    CREATE TABLE material_aula (
                        id SERIAL PRIMARY KEY,
                        nome VARCHAR(200) NOT NULL,
                        arquivo VARCHAR(500) NOT NULL,
                        tipo VARCHAR(10),
                        tamanho INTEGER,
                        aula_id INTEGER REFERENCES aula(id) ON DELETE CASCADE
                    )
                """,
                'progresso_aula': """
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
                """,
                'sessao_estudo': """
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
                """,
                'moeda': """
                    CREATE TABLE moeda (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
                        quantidade INTEGER NOT NULL,
                        tipo VARCHAR(50),
                        descricao VARCHAR(200),
                        data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
            }
            
            for table_name, create_sql in required_tables.items():
                if table_name not in existing_tables:
                    print(f"   📊 Criando tabela '{table_name}'...")
                    db.session.execute(text(create_sql))
                else:
                    print(f"   ✅ Tabela '{table_name}' já existe")
            
            # Verificar se user tem total_moedas
            if 'user' in existing_tables:
                user_columns = [col['name'] for col in inspector.get_columns('user')]
                if 'total_moedas' not in user_columns:
                    print("   💰 Adicionando campo 'total_moedas' à tabela user...")
                    db.session.execute(text('ALTER TABLE "user" ADD COLUMN total_moedas INTEGER DEFAULT 0'))
            
            db.session.commit()
            print("   ✅ Estrutura das tabelas corrigida")
            
            # 3. Inserir dados de exemplo se necessário
            print("\n3. 📚 Verificando dados de exemplo...")
            
            if 'materia' in inspect(db.engine).get_table_names():
                materia_count = db.session.execute(text("SELECT COUNT(*) FROM materia")).scalar()
                
                if materia_count == 0:
                    print("   📖 Inserindo matérias de exemplo...")
                    
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
                    
                    db.session.commit()
                    print(f"   ✅ {len(materias_exemplo)} matérias de exemplo inseridas")
                else:
                    print(f"   ✅ Já existem {materia_count} matérias no banco")
            
            # 4. Testar imports dos modelos
            print("\n4. 📦 Testando imports dos modelos...")
            
            try:
                from app.models.estudo import Materia, Modulo, Aula, ProgressoAula, SessaoEstudo, Moeda
                print("   ✅ Todos os modelos de estudo importados com sucesso")
                
                # Testar query que causava erro
                materias = Materia.query.filter_by(ativa=True).order_by(Materia.ordem).all()
                print(f"   ✅ Query de matérias funcionou. Total: {len(materias)}")
                
            except Exception as e:
                print(f"   ❌ Erro ao importar ou testar modelos: {e}")
                return False
            
            # 5. Verificar usuários
            print("\n5. 👤 Verificando usuários...")
            
            total_users = User.query.count()
            print(f"   Total de usuários: {total_users}")
            
            if total_users > 0:
                first_user = User.query.first()
                print(f"   Primeiro usuário: {first_user.username}")
                print(f"   Total moedas: {getattr(first_user, 'total_moedas', 'N/A')}")
            
            # 6. Limpar sessions ativas antigas
            print("\n6. 🧹 Limpando sessões ativas antigas...")
            
            try:
                from app.models.estudo import SessaoEstudo
                from datetime import datetime, timedelta
                
                # Marcar como inativas sessões com mais de 6 horas
                limite = datetime.utcnow() - timedelta(hours=6)
                sessoes_antigas = SessaoEstudo.query.filter(
                    SessaoEstudo.ativa == True,
                    SessaoEstudo.inicio < limite
                ).all()
                
                for sessao in sessoes_antigas:
                    sessao.ativa = False
                    if not sessao.fim:
                        sessao.fim = sessao.inicio + timedelta(minutes=30)  # Assumir 30 min
                    if not sessao.tempo_ativo:
                        sessao.tempo_ativo = 1800  # 30 minutos em segundos
                
                db.session.commit()
                print(f"   ✅ {len(sessoes_antigas)} sessões antigas finalizadas")
                
            except Exception as e:
                print(f"   ⚠️ Erro ao limpar sessões: {e}")
            
            print("\n" + "=" * 60)
            print("🎉 CORREÇÃO COMPLETA FINALIZADA COM SUCESSO!")
            print("=" * 60)
            
            print("\n📊 RESUMO FINAL:")
            final_tables = inspect(db.engine).get_table_names()
            for table in ['materia', 'modulo', 'aula', 'progresso_aula', 'sessao_estudo', 'moeda']:
                status = "✅" if table in final_tables else "❌"
                print(f"   {status} {table}")
            
            print(f"\n👥 Usuários com total_moedas: {User.query.filter(User.total_moedas.isnot(None)).count()}/{total_users}")
            
            print("\n🚀 PRÓXIMOS PASSOS:")
            print("   1. Reinicie a aplicação: python run.py")
            print("   2. Acesse: http://localhost:8080/dashboard")
            print("   3. Verifique se não há mais erros nos logs")
            
            return True
            
        except Exception as e:
            print(f"❌ ERRO DURANTE A CORREÇÃO: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = complete_fix()
    print(f"\n{'✅ CORREÇÃO BEM-SUCEDIDA' if success else '❌ CORREÇÃO FALHADA'}")
    sys.exit(0 if success else 1)
