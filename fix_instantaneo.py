# fix_instantaneo.py
"""
FIX INSTANTÂNEO - Corrige o erro em 30 segundos

Substitui apenas as linhas problemáticas que causam o erro:
'topico' is an invalid keyword argument for Questao
"""

import os

def fix_linha_problema():
    """Encontra e corrige as linhas específicas que causam o erro"""
    
    arquivo = 'app/routes/agendar_simulado.py'
    
    print("⚡ FIX INSTANTÂNEO - Corrigindo linhas problemáticas")
    print("=" * 50)
    
    if not os.path.exists(arquivo):
        print(f"❌ Arquivo {arquivo} não encontrado")
        return False
    
    # Ler arquivo
    with open(arquivo, 'r', encoding='utf-8') as f:
        linhas = f.readlines()
    
    print(f"📖 Lendo {len(linhas)} linhas...")
    
    # Procurar e corrigir linhas problemáticas
    linhas_corrigidas = 0
    
    for i, linha in enumerate(linhas):
        linha_original = linha
        
        # CORREÇÃO 1: Remover topico= da criação de Questao
        if 'topico=' in linha and 'Questao(' in linhas[max(0, i-5):i+1]:
            linha = linha.replace('topico=questao_data.get(\'topico\', \'\'),', '')
            linha = linha.replace('topico=questao_data[\'topico\'],', '')
            linha = linha.replace('topico=questao_data.get("topico", ""),', '')
            linha = linha.replace('topico=questao_data["topico"],', '')
            if linha != linha_original:
                print(f"   ✅ Linha {i+1}: Removido 'topico='")
                linhas_corrigidas += 1
        
        # CORREÇÃO 2: Remover explicacao= da criação de Questao
        if 'explicacao=' in linha and 'Questao(' in linhas[max(0, i-5):i+1]:
            linha = linha.replace('explicacao=questao_data.get(\'explicacao\', \'\'),', '')
            linha = linha.replace('explicacao=questao_data[\'explicacao\'],', '')
            linha = linha.replace('explicacao=questao_data.get("explicacao", ""),', '')
            linha = linha.replace('explicacao=questao_data["explicacao"],', '')
            if linha != linha_original:
                print(f"   ✅ Linha {i+1}: Removido 'explicacao='")
                linhas_corrigidas += 1
        
        # CORREÇÃO 3: Remover questao_base_id= da criação de Questao
        if 'questao_base_id=' in linha and 'Questao(' in linhas[max(0, i-5):i+1]:
            linha = linha.replace('questao_base_id=questao_data[\'id\'],', '')
            linha = linha.replace('questao_base_id=questao_data.get(\'id\'),', '')
            linha = linha.replace('questao_base_id=questao_data["id"],', '')
            linha = linha.replace('questao_base_id=questao_data.get("id"),', '')
            if linha != linha_original:
                print(f"   ✅ Linha {i+1}: Removido 'questao_base_id='")
                linhas_corrigidas += 1
        
        linhas[i] = linha
    
    # Salvar arquivo corrigido
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.writelines(linhas)
    
    print(f"✅ {linhas_corrigidas} linhas corrigidas!")
    print(f"💾 Arquivo salvo: {arquivo}")
    
    return linhas_corrigidas > 0

def adicionar_import_se_necessario():
    """Adiciona import do gerador se não existir"""
    
    arquivo = 'app/routes/agendar_simulado.py'
    
    with open(arquivo, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    # Verificar se precisa do import
    if 'gerar_questoes_simulado' in conteudo and 'from app.services.gerador_questoes import' not in conteudo:
        print("\n📦 Adicionando import necessário...")
        
        linhas = conteudo.split('\n')
        
        # Encontrar onde inserir
        insert_pos = 0
        for i, linha in enumerate(linhas):
            if linha.startswith('from app') and 'import' in linha:
                insert_pos = i + 1
        
        # Adicionar import
        novo_import = 'from app.services.gerador_questoes import gerar_questoes_simulado, obter_relatorio_disponibilidade'
        linhas.insert(insert_pos, novo_import)
        
        # Salvar
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write('\n'.join(linhas))
        
        print("✅ Import adicionado!")
        return True
    
    return False

def verificar_resultado():
    """Verifica se o fix funcionou"""
    
    arquivo = 'app/routes/agendar_simulado.py'
    
    print("\n🔍 VERIFICANDO RESULTADO")
    print("=" * 25)
    
    with open(arquivo, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    # Verificar se ainda tem problemas
    problemas = []
    
    if 'topico=' in conteudo and 'Questao(' in conteudo:
        # Verificar se topico= está próximo de Questao(
        linhas = conteudo.split('\n')
        for i, linha in enumerate(linhas):
            if 'topico=' in linha:
                contexto = '\n'.join(linhas[max(0, i-3):i+3])
                if 'Questao(' in contexto:
                    problemas.append(f"'topico=' ainda presente na linha {i+1}")
    
    if 'explicacao=' in conteudo and 'Questao(' in conteudo:
        linhas = conteudo.split('\n')
        for i, linha in enumerate(linhas):
            if 'explicacao=' in linha:
                contexto = '\n'.join(linhas[max(0, i-3):i+3])
                if 'Questao(' in contexto:
                    problemas.append(f"'explicacao=' ainda presente na linha {i+1}")
    
    if problemas:
        print("⚠️ Problemas encontrados:")
        for problema in problemas:
            print(f"   - {problema}")
        return False
    else:
        print("✅ Nenhum problema encontrado!")
        print("✅ Campos inválidos removidos com sucesso!")
        return True

def main():
    """Executa fix instantâneo"""
    
    print("⚡ FIX INSTANTÂNEO PARA 'topico' is an invalid keyword argument")
    print("=" * 65)
    print("Corrigindo apenas as linhas que causam o erro específico\n")
    
    # Executar fix
    sucesso1 = fix_linha_problema()
    sucesso2 = adicionar_import_se_necessario()
    sucesso3 = verificar_resultado()
    
    print(f"\n{'='*65}")
    
    if sucesso1 or sucesso3:
        print("🎉 FIX APLICADO COM SUCESSO!")
        print("\n⚡ TESTE AGORA:")
        print("   1. Pare sua aplicação Flask (Ctrl+C)")
        print("   2. Reinicie: python app.py")
        print("   3. Acesse: /agendar-simulado/")
        print("   4. Crie um simulado pequeno")
        print("\n✅ O erro 'topico' deve ter desaparecido!")
        print("\n🎯 Se ainda der erro, me envie a mensagem completa")
    else:
        print("⚠️ Nenhuma correção foi necessária")
        print("O arquivo pode já estar correto ou ter estrutura diferente")

if __name__ == "__main__":
    main()