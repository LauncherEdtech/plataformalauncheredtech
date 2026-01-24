#!/usr/bin/env python3
"""
Script de diagnóstico para o formulário ENEM
Execute: python diagnostico_forms.py
"""

import os
import sys

print("="*60)
print("🔍 DIAGNÓSTICO DO FORMULÁRIO ENEM")
print("="*60)

# 1. Verificar arquivos
print("\n📁 VERIFICANDO ARQUIVOS...")

arquivos_necessarios = {
    'app/forms_enem.py': 'Blueprint principal',
    'app/templates/forms/inicio.html': 'Template início',
    'app/templates/forms/questao.html': 'Template questão',
    'app/templates/forms/resultado.html': 'Template resultado',
    'app/templates/forms/cadastro.html': 'Template cadastro',
    'app/templates/forms/numero_completo.html': 'Template número completo'
}

arquivos_ok = 0
for arquivo, descricao in arquivos_necessarios.items():
    if os.path.exists(arquivo):
        print(f"   ✅ {descricao}: {arquivo}")
        arquivos_ok += 1
    else:
        print(f"   ❌ {descricao}: {arquivo} - NÃO ENCONTRADO")

print(f"\nArquivos: {arquivos_ok}/{len(arquivos_necessarios)}")

# 2. Verificar se blueprint está registrado
print("\n📋 VERIFICANDO BLUEPRINT...")

try:
    from app import create_app
    app = create_app()
    
    # Verificar blueprints registrados
    blueprints = list(app.blueprints.keys())
    print(f"   Blueprints registrados: {', '.join(blueprints)}")
    
    if 'forms' in blueprints:
        print("   ✅ Blueprint 'forms' está registrado!")
    else:
        print("   ❌ Blueprint 'forms' NÃO está registrado!")
        print("   💡 Solução: Adicione no __init__.py:")
        print("      from app.forms_enem import forms_bp")
        print("      app.register_blueprint(forms_bp)")
        
except Exception as e:
    print(f"   ❌ Erro ao verificar blueprints: {str(e)}")

# 3. Verificar models
print("\n🗄️  VERIFICANDO MODELS...")

try:
    from app.models.forms import FormsQuestao, FormsAlternativa, FormsParticipante
    print("   ✅ Models importados com sucesso!")
    
    # Verificar se tabelas existem
    try:
        from app import db
        with app.app_context():
            questoes = FormsQuestao.query.count()
            alternativas = FormsAlternativa.query.count()
            participantes = FormsParticipante.query.count()
            
            print(f"   ✅ Tabelas existem no banco!")
            print(f"      • Questões: {questoes}")
            print(f"      • Alternativas: {alternativas}")
            print(f"      • Participantes: {participantes}")
            
            if questoes == 0:
                print("   ⚠️  Nenhuma questão cadastrada!")
                print("   💡 Solução: Execute 'python seed_forms_questoes.py'")
            elif questoes < 15:
                print(f"   ⚠️  Apenas {questoes} questões (necessário 15)")
                print("   💡 Solução: Execute 'python seed_forms_questoes.py'")
            else:
                print(f"   ✅ {questoes} questões cadastradas!")
                
    except Exception as e:
        print(f"   ❌ Tabelas não existem: {str(e)}")
        print("   💡 Solução: Execute 'flask db upgrade'")
        
except ImportError as e:
    print(f"   ❌ Models não encontrados: {str(e)}")
    print("   💡 Solução: Verifique se os models estão em app/models/forms.py")

# 4. Verificar rotas
print("\n🌐 VERIFICANDO ROTAS...")

try:
    with app.app_context():
        # Listar todas as rotas relacionadas a forms
        rotas_forms = [rule for rule in app.url_map.iter_rules() if 'forms' in rule.rule]
        
        if rotas_forms:
            print("   ✅ Rotas do formulário encontradas:")
            for rota in rotas_forms:
                print(f"      • {rota.rule}")
        else:
            print("   ❌ Nenhuma rota 'forms' encontrada!")
            
except Exception as e:
    print(f"   ❌ Erro ao verificar rotas: {str(e)}")

# 5. Resumo e próximos passos
print("\n" + "="*60)
print("📊 RESUMO")
print("="*60)

problemas = []

if arquivos_ok < len(arquivos_necessarios):
    problemas.append("❌ Arquivos faltando")

try:
    if 'forms' not in app.blueprints:
        problemas.append("❌ Blueprint não registrado")
except:
    problemas.append("❌ Erro ao verificar blueprint")

try:
    from app.models.forms import FormsQuestao
    with app.app_context():
        if FormsQuestao.query.count() < 15:
            problemas.append("⚠️  Questões não populadas")
except:
    problemas.append("❌ Models ou tabelas não criados")

if not problemas:
    print("\n✅ TUDO PRONTO! O formulário deve funcionar em /forms")
    print("\n🚀 Acesse: https://plataformalauncher.com.br/forms")
else:
    print("\n🔧 PROBLEMAS ENCONTRADOS:")
    for problema in problemas:
        print(f"   {problema}")
    
    print("\n📋 PRÓXIMOS PASSOS:")
    
    if "❌ Blueprint não registrado" in problemas:
        print("\n1️⃣ REGISTRAR BLUEPRINT")
        print("   Edite app/__init__.py e adicione:")
        print("   ```python")
        print("   from app.forms_enem import forms_bp")
        print("   app.register_blueprint(forms_bp)")
        print("   ```")
    
    if "❌ Models ou tabelas não criados" in problemas:
        print("\n2️⃣ CRIAR TABELAS")
        print("   Execute:")
        print("   flask db migrate -m 'Adicionar formulário'")
        print("   flask db upgrade")
    
    if "⚠️  Questões não populadas" in problemas:
        print("\n3️⃣ POPULAR QUESTÕES")
        print("   Execute:")
        print("   python seed_forms_questoes.py")
    
    print("\n4️⃣ REINICIAR SERVIDOR")
    print("   sudo systemctl restart gunicorn")

print("\n" + "="*60)
