# scripts/migrar_questoes.py
import os
import sys
import json
import re
from pathlib import Path

# Adicionar o diretório raiz ao path para importar a aplicação
sys.path.append(str(Path(__file__).parent.parent))

from app import create_app, db
from app.models.questao import QuestaoBase

def limpar_texto_json(texto):
    """Remove caracteres de formatação JSON desnecessários"""
    if not texto:
        return ""
    
    # Remove aspas extras e caracteres de escape
    texto = texto.strip()
    if texto.startswith('"') and texto.endswith('"'):
        texto = texto[1:-1]
    
    # Substitui caracteres de escape
    texto = texto.replace('\\"', '"')
    texto = texto.replace('\\n', '\n')
    texto = texto.replace('\\t', '\t')
    
    return texto.strip()

def processar_arquivo_questoes(caminho_arquivo):
    """Processa um arquivo de questões e retorna lista de questões"""
    questoes = []
    
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
            conteudo = arquivo.read()
        
        print(f"Processando arquivo: {caminho_arquivo}")
        
        # Tenta parsear como JSON array primeiro
        try:
            dados = json.loads(conteudo)
            if isinstance(dados, list):
                questoes = dados
            else:
                questoes = [dados]
        except json.JSONDecodeError:
            # Se falhar, tenta extrair objetos JSON individuais
            questoes = extrair_objetos_json(conteudo)
    
    except FileNotFoundError:
        print(f"Arquivo não encontrado: {caminho_arquivo}")
        return []
    except Exception as e:
        print(f"Erro ao processar arquivo {caminho_arquivo}: {e}")
        return []
    
    return questoes

def extrair_objetos_json(conteudo):
    """Extrai objetos JSON individuais de um arquivo"""
    questoes = []
    
    # Remove quebras de linha desnecessárias e limpa o conteudo
    conteudo = re.sub(r'\n\s*\n', '\n', conteudo)
    
    # Procura por padrões de objetos JSON
    padrao = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(padrao, conteudo, re.DOTALL)
    
    for match in matches:
        try:
            # Tenta limpar e parsear cada match
            match_limpo = match.strip()
            if match_limpo.startswith('{') and match_limpo.endswith('}'):
                questao = json.loads(match_limpo)
                questoes.append(questao)
        except json.JSONDecodeError:
            continue
    
    return questoes

def mapear_materia(nome_arquivo):
    """Mapeia o nome do arquivo para a matéria correspondente"""
    mapeamento = {
        'artesdata.txt': 'Artes',
        'matematicadata.txt': 'Matemática', 
        'geografiadata.txt': 'Geografia',
        'fisicadata.txt': 'Física',
        'espanholdata.txt': 'Espanhol',
        'portuguesdata.txt': 'Português',
        'historiadata.txt': 'História',
        'educacaofisicadata.txt': 'Educação Física',
        'inglesddata.txt': 'Inglês'
    }
    
    nome_limpo = nome_arquivo.lower()
    return mapeamento.get(nome_limpo, 'Outras')

def inserir_questao_no_banco(questao_data, materia):
    """Insere uma questão no banco de dados"""
    try:
        # Validar campos obrigatórios
        if not questao_data.get('question'):
            print("Questão sem texto - ignorando")
            return False
            
        if not questao_data.get('correctAnswer'):
            print("Questão sem resposta correta - ignorando")
            return False
        
        # Verificar se a questão já existe (evitar duplicatas)
        questao_existente = QuestaoBase.query.filter_by(
            texto=limpar_texto_json(questao_data['question']),
            materia=materia
        ).first()
        
        if questao_existente:
            print(f"Questão já existe no banco - ignorando")
            return False
        
        # Criar nova questão
        nova_questao = QuestaoBase(
            texto=limpar_texto_json(questao_data['question']),
            materia=materia,
            topico=limpar_texto_json(questao_data.get('topico', 'Não especificado')),
            subtopico=limpar_texto_json(questao_data.get('subtopico', '')),
            
            opcao_a=limpar_texto_json(questao_data.get('answerA', '')),
            opcao_b=limpar_texto_json(questao_data.get('answerB', '')),
            opcao_c=limpar_texto_json(questao_data.get('answerC', '')),
            opcao_d=limpar_texto_json(questao_data.get('answerD', '')),
            opcao_e=limpar_texto_json(questao_data.get('answerE', '')),
            
            resposta_correta=questao_data['correctAnswer'].upper(),
            explicacao=limpar_texto_json(
                questao_data.get('correctAnswermessage', 
                questao_data.get('correctAnswerMessage', ''))
            ),
            
            imagem_url=limpar_texto_json(questao_data.get('image', '')),
        )
        
        db.session.add(nova_questao)
        return True
        
    except Exception as e:
        print(f"Erro ao inserir questão: {e}")
        return False

def migrar_todas_questoes(diretorio_dados='data'):
    """Migra todas as questões dos arquivos para o banco de dados"""
    app = create_app()
    
    with app.app_context():
        # Criar tabelas se não existirem
        db.create_all()
        
        total_inseridas = 0
        total_processadas = 0
        
        # Procurar arquivos de dados
        if not os.path.exists(diretorio_dados):
            print(f"Diretório {diretorio_dados} não encontrado!")
            print("Procurando arquivos na raiz do projeto...")
            diretorio_dados = '.'
        
        arquivos_dados = []
        for arquivo in os.listdir(diretorio_dados):
            if arquivo.lower().endswith('data.txt'):
                arquivos_dados.append(os.path.join(diretorio_dados, arquivo))
        
        if not arquivos_dados:
            print("Nenhum arquivo de dados encontrado!")
            print("Procure por arquivos com padrão '*Data.txt'")
            return
        
        print(f"Encontrados {len(arquivos_dados)} arquivos de dados:")
        for arquivo in arquivos_dados:
            print(f"  - {arquivo}")
        
        # Processar cada arquivo
        for caminho_arquivo in arquivos_dados:
            nome_arquivo = os.path.basename(caminho_arquivo)
            materia = mapear_materia(nome_arquivo)
            
            print(f"\n=== Processando {nome_arquivo} ({materia}) ===")
            
            questoes = processar_arquivo_questoes(caminho_arquivo)
            
            if not questoes:
                print(f"Nenhuma questão encontrada em {nome_arquivo}")
                continue
            
            questoes_inseridas = 0
            
            for questao in questoes:
                total_processadas += 1
                
                if inserir_questao_no_banco(questao, materia):
                    questoes_inseridas += 1
                    total_inseridas += 1
                    
                    # Commit a cada 10 questões para evitar problemas de memória
                    if questoes_inseridas % 10 == 0:
                        try:
                            db.session.commit()
                            print(f"  Salvas {questoes_inseridas} questões...")
                        except Exception as e:
                            print(f"  Erro ao salvar: {e}")
                            db.session.rollback()
            
            # Commit final para o arquivo
            try:
                db.session.commit()
                print(f"  ✓ {questoes_inseridas} questões inseridas de {len(questoes)} processadas")
            except Exception as e:
                print(f"  ✗ Erro ao salvar questões: {e}")
                db.session.rollback()
        
        print(f"\n=== RESUMO ===")
        print(f"Total de questões processadas: {total_processadas}")
        print(f"Total de questões inseridas: {total_inseridas}")
        print(f"Questões no banco: {QuestaoBase.query.count()}")

if __name__ == "__main__":
    print("=== MIGRAÇÃO DE QUESTÕES ===")
    print("Este script migra questões dos arquivos JSON para PostgreSQL")
    print()
    
    # Permitir especificar diretório como argumento
    diretorio = sys.argv[1] if len(sys.argv) > 1 else 'data'
    
    migrar_todas_questoes(diretorio)