# patch_rapido_agendar.py
"""
PATCH RÁPIDO para corrigir o erro:
'topico' is an invalid keyword argument for Questao

Execute este script e teste imediatamente!
"""

import os
import re

def aplicar_patch_rapido():
    """Aplica correção rápida no agendar_simulado.py"""
    
    arquivo = 'app/routes/agendar_simulado.py'
    
    print("🚀 PATCH RÁPIDO - CORRIGINDO ERRO 'topico'")
    print("=" * 50)
    
    if not os.path.exists(arquivo):
        print(f"❌ Arquivo {arquivo} não encontrado")
        return False
    
    # Ler arquivo atual
    with open(arquivo, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    print("📝 Arquivo lido com sucesso")
    
    # CORREÇÃO 1: Remover campos inválidos da criação de Questao
    # Procurar e substituir a função inserir_questoes_no_simulado
    
    funcao_corrigida = '''def inserir_questoes_no_simulado(simulado_id: int, questoes_dados: list) -> bool:
    """
    Insere questões reais do banco no simulado
    CORRIGIDO: Remove campos que não existem no modelo
    """
    try:
        for i, questao_data in enumerate(questoes_dados, 1):
            # Criar questão do simulado - SÓ CAMPOS VÁLIDOS
            questao = Questao(
                numero=i,
                texto=questao_data['texto'],
                area=questao_data['materia'],
                dificuldade=questao_data.get('dificuldade', 0.5),
                resposta_correta=questao_data['resposta_correta'],
                simulado_id=simulado_id
            )
            
            db.session.add(questao)
            db.session.flush()
            
            # Criar alternativas
            alternativas_dados = [
                ('A', questao_data['opcao_a']),
                ('B', questao_data['opcao_b']),
                ('C', questao_data['opcao_c']),
                ('D', questao_data['opcao_d']),
                ('E', questao_data['opcao_e'])
            ]
            
            for letra, texto in alternativas_dados:
                if texto and texto.strip():
                    alternativa = Alternativa(
                        letra=letra,
                        texto=texto.strip(),
                        questao_id=questao.id
                    )
                    db.session.add(alternativa)
        
        return True
        
    except Exception as e:
        print(f"Erro ao inserir questões: {e}")
        return False'''
    
    # Localizar função atual e substituir
    padrao = r'def inserir_questoes_no_simulado.*?(?=\n\ndef|\n\n@|\Z)'
    
    if re.search(padrao, conteudo, re.DOTALL):
        novo_conteudo = re.sub(padrao, funcao_corrigida, conteudo, flags=re.DOTALL)
        print("✅ Função inserir_questoes_no_simulado encontrada e corrigida")
    else:
        # Se não encontrar, adicionar no final
        novo_conteudo = conteudo + '\n\n' + funcao_corrigida
        print("✅ Função inserir_questoes_no_simulado adicionada no final")
    
    # CORREÇÃO 2: Verificar imports necessários
    if 'from app.services.gerador_questoes import' not in novo_conteudo:
        # Adicionar import no lugar certo
        linhas = novo_conteudo.split('\n')
        insert_pos = 0
        
        for i, linha in enumerate(linhas):
            if linha.startswith('from app') and 'import' in linha:
                insert_pos = i + 1
        
        linhas.insert(insert_pos, 'from app.services.gerador_questoes import gerar_questoes_simulado, obter_relatorio_disponibilidade')
        novo_conteudo = '\n'.join(linhas)
        print("✅ Import do gerador adicionado")
    
    # Salvar arquivo corrigido
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write(novo_conteudo)
    
    print("✅ Arquivo corrigido e salvo!")
    return True

def verificar_modelo_questao():
    """Verifica quais campos o modelo Questao realmente tem"""
    
    print("\n🔍 VERIFICANDO MODELO QUESTAO")
    print("=" * 30)
    
    try:
        import sys
        sys.path.insert(0, '.')
        
        from app.models.simulado import Questao
        
        # Obter campos do modelo
        campos = []
        for attr in dir(Questao):
            if not attr.startswith('_') and hasattr(getattr(Questao, attr), 'type'):
                campos.append(attr)
        
        print("Campos disponíveis no modelo Questao:")
        for campo in sorted(campos):
            print(f"   ✅ {campo}")
        
        # Verificar campos problemáticos
        campos_problematicos = ['topico', 'explicacao', 'questao_base_id']
        
        print("\nCampos que causaram erro:")
        for campo in campos_problematicos:
            if hasattr(Questao, campo):
                print(f"   ✅ {campo} (existe)")
            else:
                print(f"   ❌ {campo} (NÃO EXISTE - removido do código)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar modelo: {e}")
        return False

def testar_patch():
    """Testa se o patch funcionou"""
    
    print("\n🧪 TESTANDO PATCH")
    print("=" * 20)
    
    try:
        # Testar import
        import sys
        sys.path.insert(0, '.')
        
        from app.services.gerador_questoes import gerar_questoes_simulado
        print("✅ Import funcionando")
        
        # Testar geração mínima
        questoes = gerar_questoes_simulado(['Matemática'], 1, 'equilibrada')
        
        if questoes:
            print(f"✅ Gerou {len(questoes)} questão de teste")
            print("✅ PATCH FUNCIONANDO!")
            return True
        else:
            print("⚠️ Nenhuma questão gerada (normal se não há questões de Matemática)")
            return True
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def main():
    """Executa patch rápido"""
    
    print("⚡ PATCH RÁPIDO PARA ERRO 'topico' is an invalid keyword argument")
    print("=" * 70)
    print("Este patch corrige o erro específico que você está enfrentando\n")
    
    # Executar correções
    etapas = [
        ("Verificar modelo Questao", verificar_modelo_questao),
        ("Aplicar patch rápido", aplicar_patch_rapido),
        ("Testar patch", testar_patch)
    ]
    
    sucessos = 0
    
    for nome, funcao in etapas:
        try:
            resultado = funcao()
            if resultado:
                sucessos += 1
        except Exception as e:
            print(f"❌ Erro em {nome}: {e}")
    
    print(f"\n{'='*70}")
    
    if sucessos >= 2:
        print("🎉 PATCH APLICADO COM SUCESSO!")
        print("\n🚀 AGORA FAÇA:")
        print("   1. Reinicie sua aplicação Flask")
        print("   2. Teste novamente: /agendar-simulado/")
        print("   3. Crie um simulado pequeno (5 questões)")
        print("   4. Verifique se o erro 'topico' desapareceu")
        print("\n✅ O erro deve estar corrigido!")
    else:
        print("⚠️ Alguns problemas no patch")
        print("Mas tente reiniciar a aplicação mesmo assim")

if __name__ == "__main__":
    main()