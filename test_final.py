# test_final.py
import os
os.environ['FLASK_DEBUG'] = 'False'  # Desabilitar debug para teste limpo

from app import create_app, db
from app.models.user import User
from app.models.estudo import Materia

app = create_app()

print("🧪 TESTANDO CORREÇÃO DO ERRO 'db is undefined'\n")

with app.app_context():
    # Verificar se há matérias
    materias = Materia.query.all()
    print(f"Total de matérias: {len(materias)}")
    
    if len(materias) == 0:
        print("⚠️  Nenhuma matéria encontrada. Crie pelo menos uma matéria com módulo e aula.")
    else:
        with app.test_client() as client:
            # Fazer login
            admin = User.query.filter_by(is_admin=True).first()
            if admin:
                # Teste sem login primeiro
                print("\n1. Testando sem login...")
                r = client.get('/estudo/')
                print(f"   /estudo/: {r.status_code} (esperado: 302 redirect)")
                
                # Login
                print("\n2. Fazendo login...")
                # Ajuste a senha conforme seu usuário admin
                login_data = {'email': admin.email, 'password': 'admin'}  # <-- AJUSTE A SENHA AQUI
                r = client.post('/login', data=login_data, follow_redirects=True)
                
                # Testar rotas
                print("\n3. Testando rotas com login...")
                
                # Página principal
                r = client.get('/estudo/')
                print(f"   /estudo/: {r.status_code}")
                if b'db' in r.data and b'undefined' in r.data:
                    print("   ❌ ERRO 'db is undefined' ainda presente!")
                else:
                    print("   ✅ Sem erro 'db is undefined'")
                
                # Testar cada matéria
                for materia in materias:
                    r = client.get(f'/estudo/materia/{materia.id}')
                    print(f"   /estudo/materia/{materia.id}: {r.status_code}")
                    
                    if b'db' in r.data and b'undefined' in r.data:
                        print(f"   ❌ ERRO em matéria {materia.id}!")
                        # Mostrar trecho do erro
                        error_pos = r.data.find(b'db')
                        if error_pos > -1:
                            snippet = r.data[max(0, error_pos-50):error_pos+50]
                            print(f"      Contexto: ...{snippet}...")
                    else:
                        print("   ✅ OK")
            else:
                print("❌ Nenhum usuário admin encontrado!")

print("\n✅ Teste concluído!")
