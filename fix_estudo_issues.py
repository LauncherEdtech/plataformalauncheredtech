# fix_estudo_issues.py
# Script para diagnosticar e corrigir problemas no sistema de estudos

import os
from app import create_app, db
from app.models.user import User

app = create_app()

def check_templates():
    """Verifica se os templates existem"""
    print("📁 Verificando templates...")
    
    template_paths = [
        'app/templates/estudo/index.html',
        'app/templates/estudo/materia.html',
        'app/templates/estudo/modulo.html',
        'app/templates/estudo/aula.html',
        'app/templates/estudo/admin/index.html',
        'app/templates/estudo/admin/materia_form.html',
        'app/templates/estudo/admin/modulo_form.html',
        'app/templates/estudo/admin/aula_form.html'
    ]
    
    missing = []
    for path in template_paths:
        if os.path.exists(path):
            print(f"✅ {path}")
        else:
            print(f"❌ {path} - FALTANDO")
            missing.append(path)
    
    if missing:
        print(f"\n⚠️  Templates faltando: {len(missing)}")
        # Criar diretórios se necessário
        os.makedirs('app/templates/estudo/admin', exist_ok=True)
    
    return missing

def fix_user_methods():
    """Adiciona métodos ao modelo User se necessário"""
    print("\n🔧 Verificando métodos do User...")
    
    with app.app_context():
        # Verificar se os métodos existem
        test_user = User.query.first()
        if test_user:
            methods_to_check = ['tempo_estudo_hoje', 'aulas_concluidas_count', 'sequencia_estudo']
            
            for method in methods_to_check:
                if hasattr(test_user, method):
                    print(f"✅ Método {method} existe")
                else:
                    print(f"❌ Método {method} não existe - será necessário adicionar ao modelo User")

def check_database_fields():
    """Verifica campos necessários no banco"""
    print("\n🗄️ Verificando campos do banco...")
    
    with app.app_context():
        try:
            # Verificar se xp_total existe
            result = db.session.execute(db.text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='user' AND column_name='xp_total'"
            ))
            
            if result.rowcount == 0:
                print("❌ Campo xp_total não existe - criando...")
                db.session.execute(db.text(
                    "ALTER TABLE \"user\" ADD COLUMN xp_total INTEGER DEFAULT 0"
                ))
                db.session.commit()
                print("✅ Campo xp_total criado")
            else:
                print("✅ Campo xp_total existe")
                
        except Exception as e:
            print(f"❌ Erro ao verificar campos: {e}")

def create_test_data():
    """Cria dados de teste se necessário"""
    print("\n📝 Verificando dados de teste...")
    
    with app.app_context():
        try:
            from app.models.estudo import Materia, Modulo, Aula
            
            if Materia.query.count() == 0:
                print("Criando matérias de teste...")
                
                # Matérias do ENEM
                materias_data = [
                    {
                        'nome': 'Matemática',
                        'descricao': 'Conteúdo completo de Matemática para o ENEM',
                        'icone': '🔢',
                        'cor': '#FF6B6B',
                        'ordem': 1
                    },
                    {
                        'nome': 'Linguagens',
                        'descricao': 'Português, Literatura, Língua Estrangeira e Artes',
                        'icone': '📝',
                        'cor': '#4ECDC4',
                        'ordem': 2
                    },
                    {
                        'nome': 'Ciências Humanas',
                        'descricao': 'História, Geografia, Filosofia e Sociologia',
                        'icone': '🌍',
                        'cor': '#45B7D1',
                        'ordem': 3
                    },
                    {
                        'nome': 'Ciências da Natureza',
                        'descricao': 'Física, Química e Biologia',
                        'icone': '🧪',
                        'cor': '#96CEB4',
                        'ordem': 4
                    }
                ]
                
                for mat_data in materias_data:
                    materia = Materia(**mat_data, ativa=True)
                    db.session.add(materia)
                
                db.session.commit()
                print("✅ Matérias de teste criadas")
                
                # Criar um módulo de exemplo
                mat_matematica = Materia.query.filter_by(nome='Matemática').first()
                if mat_matematica:
                    modulo = Modulo(
                        titulo='Álgebra Básica',
                        descricao='Fundamentos de álgebra para o ENEM',
                        materia_id=mat_matematica.id,
                        ordem=1,
                        duracao_estimada=180,
                        dificuldade='facil',
                        ativo=True
                    )
                    db.session.add(modulo)
                    db.session.commit()
                    
                    # Criar uma aula de exemplo
                    aula = Aula(
                        titulo='Introdução às Equações',
                        descricao='Aprenda os conceitos básicos de equações',
                        conteudo='<h2>O que são equações?</h2><p>Equações são expressões matemáticas que contêm uma igualdade...</p>',
                        modulo_id=modulo.id,
                        ordem=1,
                        duracao_estimada=30,
                        tipo='texto',
                        ativa=True
                    )
                    db.session.add(aula)
                    db.session.commit()
                    
                    print("✅ Módulo e aula de exemplo criados")
            else:
                print("✅ Já existem matérias no banco")
                
        except Exception as e:
            print(f"❌ Erro ao criar dados de teste: {e}")
            db.session.rollback()

def main():
    print("🔧 DIAGNÓSTICO DO SISTEMA DE ESTUDOS\n")
    
    # 1. Verificar templates
    missing_templates = check_templates()
    
    # 2. Verificar métodos do User
    fix_user_methods()
    
    # 3. Verificar campos do banco
    check_database_fields()
    
    # 4. Criar dados de teste
    create_test_data()
    
    print("\n📊 RESUMO:")
    print("=" * 50)
    
    if missing_templates:
        print(f"⚠️  {len(missing_templates)} templates faltando")
        print("   Execute: python create_missing_templates.py")
    else:
        print("✅ Todos os templates presentes")
    
    print("\n🚀 Para iniciar o servidor:")
    print("   1. chmod +x start_server.sh")
    print("   2. ./start_server.sh")
    print("\n   Ou simplesmente: python run.py")

if __name__ == "__main__":
    main()
