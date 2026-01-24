# test_estudo_routes.py - Script para testar as rotas do sistema de estudos

from app import create_app, db
from app.models.user import User
from app.models.estudo import Materia, Modulo, Aula

# Criar aplicação
app = create_app()

with app.app_context():
    print("🔧 Testando sistema de estudos...")
    
    # 1. Verificar se as tabelas existem
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"\n📊 Tabelas no banco: {tables}")
    
    required_tables = ['materia', 'modulo', 'aula', 'progresso_aula', 'sessao_estudo', 'moeda']
    missing_tables = [t for t in required_tables if t not in tables]
    
    if missing_tables:
        print(f"⚠️  Tabelas faltando: {missing_tables}")
        print("Execute as migrações: flask db upgrade")
    else:
        print("✅ Todas as tabelas de estudo existem!")
    
    # 2. Criar dados de teste se necessário
    if 'materia' in tables:
        materias_count = Materia.query.count()
        if materias_count == 0:
            print("\n📝 Criando dados de teste...")
            
            # Criar matéria de teste
            materia = Materia(
                nome="Matemática",
                descricao="Conteúdo completo de Matemática para o ENEM",
                icone="🔢",
                cor="#FF6B6B",
                ordem=1,
                ativa=True
            )
            db.session.add(materia)
            db.session.commit()
            
            # Criar módulo de teste
            modulo = Modulo(
                titulo="Álgebra Básica",
                descricao="Fundamentos de álgebra",
                materia_id=materia.id,
                ordem=1,
                duracao_estimada=120,
                dificuldade="facil",
                ativo=True
            )
            db.session.add(modulo)
            db.session.commit()
            
            # Criar aula de teste
            aula = Aula(
                titulo="Introdução às Equações",
                descricao="Aprenda os conceitos básicos de equações",
                conteudo="<h2>O que são equações?</h2><p>Equações são expressões matemáticas...</p>",
                modulo_id=modulo.id,
                ordem=1,
                duracao_estimada=30,
                tipo="texto",
                ativa=True
            )
            db.session.add(aula)
            db.session.commit()
            
            print("✅ Dados de teste criados!")
        else:
            print(f"✅ Já existem {materias_count} matérias no banco")
    
    # 3. Testar rotas com contexto de requisição
    print("\n🌐 Testando rotas...")
    
    with app.test_request_context():
        from flask import url_for
        
        # Testar rotas básicas
        routes_to_test = [
            ('estudo.index', {}),
            ('estudo.materia', {'materia_id': 1}),
            ('estudo.modulo', {'modulo_id': 1}),
            ('estudo.aula', {'aula_id': 1}),
            ('estudo.admin', {})
        ]
        
        for route_name, params in routes_to_test:
            try:
                url = url_for(route_name, **params)
                print(f"✅ Rota {route_name}: {url}")
            except Exception as e:
                print(f"❌ Erro na rota {route_name}: {e}")
    
    # 4. Testar com cliente de teste
    print("\n🧪 Testando requisições HTTP...")
    
    with app.test_client() as client:
        # Criar usuário de teste se não existir
        test_user = User.query.filter_by(email='teste@teste.com').first()
        if not test_user:
            test_user = User(
                username='teste',
                email='teste@teste.com',
                nome_completo='Usuário Teste',
                is_active=True,
                is_admin=True,
                password_changed=True
            )
            test_user.set_password('teste123')
            db.session.add(test_user)
            db.session.commit()
            print("✅ Usuário de teste criado")
        
        # Fazer login
        login_response = client.post('/login', data={
            'email': 'teste@teste.com',
            'password': 'teste123'
        }, follow_redirects=True)
        
        if login_response.status_code == 200:
            print("✅ Login realizado com sucesso")
            
            # Testar página de estudos
            response = client.get('/estudo/')
            print(f"📄 GET /estudo/: Status {response.status_code}")
            
            # Testar API
            response = client.get('/estudo/api/estatisticas_detalhadas')
            print(f"📄 GET /estudo/api/estatisticas_detalhadas: Status {response.status_code}")
            
            # Se houver matérias, testar a primeira
            if Materia.query.count() > 0:
                materia = Materia.query.first()
                response = client.get(f'/estudo/materia/{materia.id}')
                print(f"📄 GET /estudo/materia/{materia.id}: Status {response.status_code}")
        else:
            print("❌ Falha no login")

print("\n✅ Teste concluído!")

