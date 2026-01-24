import os
import sys
from app import create_app, db

app = create_app()

print("🔧 Aplicando todas as correções...")

# 1. Remover FLASK_ENV
os.environ.pop('FLASK_ENV', None)
os.environ['FLASK_DEBUG'] = 'True'

# 2. Verificar e criar diretórios
os.makedirs('app/templates/estudo/admin', exist_ok=True)
os.makedirs('app/static/uploads/materiais', exist_ok=True)

# 3. Testar aplicação
with app.app_context():
    try:
        from app.models.estudo import Materia
        print("✅ Modelos carregados com sucesso")
        
        # Verificar se há matérias
        count = Materia.query.count()
        print(f"📊 Total de matérias: {count}")
        
        if count == 0:
            print("💡 Acesse /estudo/admin para criar conteúdo")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

print("\n✅ Correções aplicadas!")
print("🚀 Execute: python run.py")
