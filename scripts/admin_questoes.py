# scripts/admin_questoes.py
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from app import create_app, db
from app.models.questao import QuestaoBase
from sqlalchemy import func
import argparse

def listar_estatisticas():
    """Lista estatísticas gerais do banco de questões"""
    app = create_app()
    
    with app.app_context():
        total_questoes = QuestaoBase.query.count()
        questoes_ativas = QuestaoBase.query.filter_by(ativa=True).count()
        
        print("=== ESTATÍSTICAS GERAIS ===")
        print(f"Total de questões: {total_questoes}")
        print(f"Questões ativas: {questoes_ativas}")
        print(f"Questões inativas: {total_questoes - questoes_ativas}")
        print()
        
        # Estatísticas por matéria
        print("=== POR MATÉRIA ===")
        materias = db.session.query(
            QuestaoBase.materia,
            func.count(QuestaoBase.id).label('total')
        ).group_by(QuestaoBase.materia).all()
        
        for materia, total in materias:
            print(f"{materia}: {total} questões")
        print()
        
        # Estatísticas por tópico
        print("=== TOP 10 TÓPICOS ===")
        topicos = db.session.query(
            QuestaoBase.topico,
            QuestaoBase.materia,
            func.count(QuestaoBase.id).label('total')
        ).group_by(QuestaoBase.topico, QuestaoBase.materia)\
         .order_by(func.count(QuestaoBase.id).desc())\
         .limit(10).all()
        
        for topico, materia, total in topicos:
            print(f"{materia} - {topico}: {total} questões")

def listar_questoes(materia=None, topico=None, limite=10):
    """Lista questões com filtros opcionais"""
    app = create_app()
    
    with app.app_context():
        query = QuestaoBase.query
        
        if materia:
            query = query.filter(QuestaoBase.materia.ilike(f'%{materia}%'))
        
        if topico:
            query = query.filter(QuestaoBase.topico.ilike(f'%{topico}%'))
        
        questoes = query.limit(limite).all()
        
        print(f"=== QUESTÕES (Mostrando {len(questoes)} de {query.count()}) ===")
        
        for q in questoes:
            print(f"\nID: {q.id}")
            print(f"Matéria: {q.materia}")
            print(f"Tópico: {q.topico}")
            if q.subtopico:
                print(f"Subtópico: {q.subtopico}")
            print(f"Texto: {q.texto[:100]}...")
            print(f"Resposta: {q.resposta_correta}")
            print(f"Ativa: {'Sim' if q.ativa else 'Não'}")
            print(f"Uso: {q.vezes_utilizada} vezes ({q.percentual_acerto:.1f}% acerto)")
            print("-" * 50)

def buscar_questao(id_questao):
    """Mostra detalhes completos de uma questão"""
    app = create_app()
    
    with app.app_context():
        questao = QuestaoBase.query.get(id_questao)
        
        if not questao:
            print(f"Questão {id_questao} não encontrada!")
            return
        
        print("=== DETALHES DA QUESTÃO ===")
        print(f"ID: {questao.id}")
        print(f"Matéria: {questao.materia}")
        print(f"Tópico: {questao.topico}")
        if questao.subtopico:
            print(f"Subtópico: {questao.subtopico}")
        print()
        print("TEXTO:")
        print(questao.texto)
        print()
        print("ALTERNATIVAS:")
        print(f"A) {questao.opcao_a}")
        print(f"B) {questao.opcao_b}")
        print(f"C) {questao.opcao_c}")
        print(f"D) {questao.opcao_d}")
        print(f"E) {questao.opcao_e}")
        print()
        print(f"RESPOSTA CORRETA: {questao.resposta_correta}")
        print()
        print("EXPLICAÇÃO:")
        print(questao.explicacao)
        print()
        if questao.imagem_url:
            print(f"IMAGEM: {questao.imagem_url}")
        print(f"DIFICULDADE: {questao.dificuldade}")
        print(f"CRIADA EM: {questao.data_criacao}")
        print(f"ATIVA: {'Sim' if questao.ativa else 'Não'}")
        print(f"ESTATÍSTICAS: {questao.vezes_utilizada} usos, {questao.percentual_acerto:.1f}% acerto")

def desativar_questao(id_questao):
    """Desativa uma questão"""
    app = create_app()
    
    with app.app_context():
        questao = QuestaoBase.query.get(id_questao)
        
        if not questao:
            print(f"Questão {id_questao} não encontrada!")
            return
        
        questao.ativa = False
        db.session.commit()
        print(f"Questão {id_questao} desativada com sucesso!")

def ativar_questao(id_questao):
    """Ativa uma questão"""
    app = create_app()
    
    with app.app_context():
        questao = QuestaoBase.query.get(id_questao)
        
        if not questao:
            print(f"Questão {id_questao} não encontrada!")
            return
        
        questao.ativa = True
        db.session.commit()
        print(f"Questão {id_questao} ativada com sucesso!")

def validar_questoes():
    """Valida a integridade das questões no banco"""
    app = create_app()
    
    with app.app_context():
        print("=== VALIDAÇÃO DAS QUESTÕES ===")
        
        total = QuestaoBase.query.count()
        problemas = 0
        
        print(f"Validando {total} questões...")
        
        for questao in QuestaoBase.query.all():
            erros = []
            
            # Validar campos obrigatórios
            if not questao.texto.strip():
                erros.append("Texto vazio")
            
            if not questao.resposta_correta or questao.resposta_correta not in 'ABCDE':
                erros.append("Resposta correta inválida")
            
            # Validar alternativas
            alternativas = [questao.opcao_a, questao.opcao_b, questao.opcao_c, 
                          questao.opcao_d, questao.opcao_e]
            
            for i, alt in enumerate(alternativas):
                if not alt or not alt.strip():
                    erros.append(f"Alternativa {'ABCDE'[i]} vazia")
            
            if not questao.explicacao.strip():
                erros.append("Explicação vazia")
            
            if erros:
                problemas += 1
                print(f"\nQuestão {questao.id} ({questao.materia}):")
                for erro in erros:
                    print(f"  ⚠️  {erro}")
        
        print(f"\n=== RESULTADO ===")
        print(f"Questões válidas: {total - problemas}")
        print(f"Questões com problemas: {problemas}")
        
        if problemas == 0:
            print("✅ Todas as questões estão válidas!")

def main():
    parser = argparse.ArgumentParser(description='Administração do banco de questões')
    
    subparsers = parser.add_subparsers(dest='comando', help='Comandos disponíveis')
    
    # Comando de estatísticas
    subparsers.add_parser('stats', help='Mostra estatísticas gerais')
    
    # Comando de listagem
    list_parser = subparsers.add_parser('list', help='Lista questões')
    list_parser.add_argument('--materia', help='Filtrar por matéria')
    list_parser.add_argument('--topico', help='Filtrar por tópico')
    list_parser.add_argument('--limite', type=int, default=10, help='Número máximo de questões')
    
    # Comando de busca
    show_parser = subparsers.add_parser('show', help='Mostra detalhes de uma questão')
    show_parser.add_argument('id', type=int, help='ID da questão')
    
    # Comando de desativar
    disable_parser = subparsers.add_parser('disable', help='Desativa uma questão')
    disable_parser.add_argument('id', type=int, help='ID da questão')
    
    # Comando de ativar
    enable_parser = subparsers.add_parser('enable', help='Ativa uma questão')
    enable_parser.add_argument('id', type=int, help='ID da questão')
    
    # Comando de validação
    subparsers.add_parser('validate', help='Valida integridade das questões')
    
    args = parser.parse_args()
    
    if not args.comando:
        parser.print_help()
        return
    
    if args.comando == 'stats':
        listar_estatisticas()
    elif args.comando == 'list':
        listar_questoes(args.materia, args.topico, args.limite)
    elif args.comando == 'show':
        buscar_questao(args.id)
    elif args.comando == 'disable':
        desativar_questao(args.id)
    elif args.comando == 'enable':
        ativar_questao(args.id)
    elif args.comando == 'validate':
        validar_questoes()

if __name__ == "__main__":
    main()