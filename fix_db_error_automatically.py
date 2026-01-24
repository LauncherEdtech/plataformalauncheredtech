# fix_db_error_automatically.py
# Script que corrige automaticamente o erro 'db is undefined'

import os
import re

print("🔧 CORRIGINDO AUTOMATICAMENTE O ERRO 'db is undefined'\n")

# Template materia.html limpo
materia_template_fixed = '''<!-- app/templates/estudo/materia.html -->
{% extends "layout.html" %}

{% block title %}{{ materia.nome }} - Plataforma Launcher{% endblock %}

{% block content %}
<style>
    .materia-container { max-width: 1200px; margin: 0 auto; padding: 20px; }
    .materia-header { background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; margin-bottom: 30px; }
    .modulo-card { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; margin-bottom: 15px; }
    .modulo-card:hover { background: rgba(255,255,255,0.15); }
    .progress-bar { height: 8px; background: rgba(255,255,255,0.2); border-radius: 4px; overflow: hidden; }
    .progress-fill { height: 100%; background: linear-gradient(90deg, #00b4d8, #0084ff); }
</style>

<div class="materia-container">
    <div class="materia-header">
        <h1>{{ materia.icone }} {{ materia.nome }}</h1>
        <p>{{ materia.descricao }}</p>
        
        <div style="margin-top: 20px;">
            <strong>Progresso Geral:</strong> {{ "%.0f"|format(materia.progresso_calculado) }}%
            <div class="progress-bar" style="margin-top: 10px;">
                <div class="progress-fill" style="width: {{ materia.progresso_calculado }}%;"></div>
            </div>
            <small>{{ materia.aulas_concluidas }} de {{ materia.total_aulas }} aulas concluídas</small>
        </div>
    </div>

    <h2>Módulos</h2>
    {% for modulo in modulos %}
    <a href="{{ url_for('estudo.modulo', modulo_id=modulo.id) }}" class="modulo-card" style="display: block; text-decoration: none; color: white;">
        <h3>{{ modulo.titulo }}</h3>
        <p>{{ modulo.descricao }}</p>
        
        <div style="margin-top: 15px;">
            <strong>Progresso:</strong> {{ "%.0f"|format(modulo.progresso_calculado) }}%
            <div class="progress-bar" style="margin-top: 5px;">
                <div class="progress-fill" style="width: {{ modulo.progresso_calculado }}%;"></div>
            </div>
            <small>{{ modulo.aulas_concluidas }} de {{ modulo.total_aulas }} aulas | {{ modulo.dificuldade|title }}</small>
        </div>
    </a>
    {% endfor %}
    
    <div style="margin-top: 30px;">
        <a href="{{ url_for('estudo.index') }}" class="btn btn-secondary">← Voltar</a>
    </div>
</div>
{% endblock %}'''

# Template modulo.html limpo
modulo_template_fixed = '''<!-- app/templates/estudo/modulo.html -->
{% extends "layout.html" %}

{% block title %}{{ modulo.titulo }} - Plataforma Launcher{% endblock %}

{% block content %}
<style>
    .modulo-container { max-width: 1000px; margin: 0 auto; padding: 20px; }
    .modulo-header { background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; margin-bottom: 30px; }
    .aula-card { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; margin-bottom: 15px; display: flex; align-items: center; gap: 20px; }
    .aula-card:hover { background: rgba(255,255,255,0.15); }
    .aula-card.concluida { background: rgba(40,167,69,0.2); }
    .aula-numero { width: 40px; height: 40px; background: #0084ff; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; }
    .aula-card.concluida .aula-numero { background: #28a745; }
</style>

<div class="modulo-container">
    <div class="modulo-header">
        <div style="font-size: 14px; opacity: 0.8; margin-bottom: 10px;">
            <a href="{{ url_for('estudo.index') }}" style="color: #00b4d8;">Estudos</a> > 
            <a href="{{ url_for('estudo.materia', materia_id=modulo.materia.id) }}" style="color: #00b4d8;">{{ modulo.materia.nome }}</a> > 
            {{ modulo.titulo }}
        </div>
        
        <h1>{{ modulo.titulo }}</h1>
        <p>{{ modulo.descricao }}</p>
        
        <div style="margin-top: 20px;">
            <strong>Progresso:</strong> {{ "%.0f"|format(modulo.progresso_calculado) }}%
            <div class="progress-bar" style="margin-top: 10px; height: 10px; background: rgba(255,255,255,0.2); border-radius: 5px;">
                <div style="height: 100%; width: {{ modulo.progresso_calculado }}%; background: linear-gradient(90deg, #00b4d8, #0084ff); border-radius: 5px;"></div>
            </div>
            <small>{{ modulo.aulas_concluidas }} de {{ modulo.total_aulas }} aulas concluídas</small>
        </div>
    </div>

    <h2>Aulas</h2>
    {% for aula in aulas %}
    <a href="{{ url_for('estudo.aula', aula_id=aula.id) }}" class="aula-card {{ 'concluida' if aula.concluida else '' }}" style="text-decoration: none; color: white;">
        <div class="aula-numero">
            {% if aula.concluida %}✓{% else %}{{ loop.index }}{% endif %}
        </div>
        <div style="flex: 1;">
            <h3 style="margin: 0;">{{ aula.titulo }}</h3>
            <small>
                {{ aula.tipo|title }} 
                {% if aula.duracao_estimada %}• {{ aula.duracao_estimada }} min{% endif %}
                {% if aula.concluida %} • ✅ Concluída{% endif %}
            </small>
            
            {% if aula.progresso and not aula.concluida and aula.progresso_percentual > 0 %}
            <div style="margin-top: 10px;">
                <div style="height: 4px; background: rgba(255,255,255,0.2); border-radius: 2px;">
                    <div style="height: 100%; width: {{ aula.progresso_percentual }}%; background: #ffc107; border-radius: 2px;"></div>
                </div>
                <small>{{ "%.0f"|format(aula.progresso_percentual) }}% assistido</small>
            </div>
            {% endif %}
        </div>
    </a>
    {% endfor %}
    
    <div style="margin-top: 30px;">
        <a href="{{ url_for('estudo.materia', materia_id=modulo.materia.id) }}" class="btn btn-secondary">← Voltar</a>
    </div>
</div>
{% endblock %}'''

# Salvar os templates corrigidos
files_to_fix = {
    'app/templates/estudo/materia.html': materia_template_fixed,
    'app/templates/estudo/modulo.html': modulo_template_fixed
}

print("📝 Salvando templates corrigidos...\n")
for filepath, content in files_to_fix.items():
    try:
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Salvar o arquivo
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ {filepath} - CORRIGIDO")
    except Exception as e:
        print(f"❌ Erro ao salvar {filepath}: {e}")

# Verificar se a rota estudo.py tem as funções de preparação
print("\n🔍 Verificando app/routes/estudo.py...")
estudo_py_path = 'app/routes/estudo.py'

if os.path.exists(estudo_py_path):
    with open(estudo_py_path, 'r', encoding='utf-8') as f:
        estudo_content = f.read()
    
    # Verificar se tem as funções necessárias
    required_functions = ['preparar_dados_materia', 'preparar_dados_modulo']
    missing_functions = []
    
    for func in required_functions:
        if func not in estudo_content:
            missing_functions.append(func)
    
    if missing_functions:
        print(f"⚠️  Funções faltando em estudo.py: {missing_functions}")
        print("   ➡️  Use o arquivo estudo.py fornecido nos artefatos!")
    else:
        print("✅ estudo.py parece estar correto")

# Criar script de teste final
test_script = '''# test_final.py
import os
os.environ['FLASK_DEBUG'] = 'False'  # Desabilitar debug para teste limpo

from app import create_app, db
from app.models.user import User
from app.models.estudo import Materia

app = create_app()

print("🧪 TESTANDO CORREÇÃO DO ERRO 'db is undefined'\\n")

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
                print("\\n1. Testando sem login...")
                r = client.get('/estudo/')
                print(f"   /estudo/: {r.status_code} (esperado: 302 redirect)")
                
                # Login
                print("\\n2. Fazendo login...")
                # Ajuste a senha conforme seu usuário admin
                login_data = {'email': admin.email, 'password': 'admin'}  # <-- AJUSTE A SENHA AQUI
                r = client.post('/login', data=login_data, follow_redirects=True)
                
                # Testar rotas
                print("\\n3. Testando rotas com login...")
                
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

print("\\n✅ Teste concluído!")
'''

with open('test_final.py', 'w', encoding='utf-8') as f:
    f.write(test_script)

print("\n✅ CORREÇÃO APLICADA!")
print("\n🚀 Execute agora:")
print("   python test_final.py")
print("\nSe não houver mais erros 'db is undefined', execute:")
print("   python run.py")
print("\n💡 IMPORTANTE: Se ainda houver erro, verifique se você substituiu")
print("   o arquivo app/routes/estudo.py pelo fornecido nos artefatos!")
