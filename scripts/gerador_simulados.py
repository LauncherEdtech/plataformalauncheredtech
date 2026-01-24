# scripts/gerador_simulados.py
import sys
from pathlib import Path
import random
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from app import create_app, db
from app.models.questao import QuestaoBase, Questao, Alternativa
from app.models.simulado import Simulado
from app.models.user import User

class GeradorSimulado:
    """Classe para gerar simulados a partir do banco de questões"""
    
    def __init__(self):
        self.app = create_app()
    
    def obter_questoes_por_criterio(self, materias=None, topicos=None, 
                                   dificuldade_min=0.0, dificuldade_max=1.0,
                                   quantidade=45):
        """
        Obtém questões do banco baseado em critérios específicos
        
        Args:
            materias: Lista de matérias a incluir
            topicos: Lista de tópicos a incluir  
            dificuldade_min: Dificuldade mínima (0.0 a 1.0)
            dificuldade_max: Dificuldade máxima (0.0 a 1.0)
            quantidade: Número de questões desejadas
        """
        with self.app.app_context():
            query = QuestaoBase.query.filter(QuestaoBase.ativa == True)
            
            if materias:
                query = query.filter(QuestaoBase.materia.in_(materias))
            
            if topicos:
                query = query.filter(QuestaoBase.topico.in_(topicos))
            
            query = query.filter(
                QuestaoBase.dificuldade >= dificuldade_min,
                QuestaoBase.dificuldade <= dificuldade_max
            )
            
            questoes_disponiveis = query.all()
            
            if len(questoes_disponiveis) < quantidade:
                print(f"Aviso: Apenas {len(questoes_disponiveis)} questões disponíveis, "
                      f"mas {quantidade} foram solicitadas")
                return questoes_disponiveis
            
            # Selecionar questões aleatoriamente
            return random.sample(questoes_disponiveis, quantidade)
    
    def distribuir_questoes_enem(self, quantidade_total=45):
        """
        Distribui questões seguindo o padrão do ENEM
        
        Distribuição típica:
        - Linguagens: 45 questões
        - Matemática: 45 questões  
        - Ciências Humanas: 45 questões
        - Ciências da Natureza: 45 questões
        
        Para simulado menor, mantém proporção
        """
        with self.app.app_context():
            # Mapeamento de matérias para áreas do ENEM
            areas_enem = {
                'Linguagens': ['Português', 'Artes', 'Inglês', 'Espanhol'],
                'Matemática': ['Matemática'],
                'Humanas': ['História', 'Geografia', 'Filosofia', 'Sociologia'],
                'Natureza': ['Física', 'Química', 'Biologia']
            }
            
            questoes_selecionadas = []
            questoes_por_area = quantidade_total // 4  # Divide igualmente entre 4 áreas
            resto = quantidade_total % 4
            
            for i, (area, materias) in enumerate(areas_enem.items()):
                # Adiciona questões extras do resto para as primeiras áreas
                qtd_area = questoes_por_area + (1 if i < resto else 0)
                
                questoes_area = self.obter_questoes_por_criterio(
                    materias=materias,
                    quantidade=qtd_area
                )
                
                # Adicionar área ENEM às questões
                for questao in questoes_area:
                    questao.area_enem = area
                
                questoes_selecionadas.extend(questoes_area)
                
                print(f"{area}: {len(questoes_area)} questões")
            
            return questoes_selecionadas
    
    def criar_simulado_usuario(self, user_id, titulo, questoes_base, areas="Todas",
                              duracao_minutos=180):
        """
        Cria um simulado para um usuário específico
        
        Args:
            user_id: ID do usuário
            titulo: Título do simulado
            questoes_base: Lista de objetos QuestaoBase
            areas: String descrevendo as áreas incluídas
            duracao_minutos: Duração em minutos
        """
        with self.app.app_context():
            # Verificar se usuário existe
            usuario = User.query.get(user_id)
            if not usuario:
                print(f"Usuário {user_id} não encontrado!")
                return None
            
            # Criar simulado
            simulado = Simulado(
                titulo=titulo,
                areas=areas,
                duracao_minutos=duracao_minutos,
                user_id=user_id,
                status='Pendente'
            )
            
            db.session.add(simulado)
            db.session.flush()  # Para obter o ID do simulado
            
            # Criar questões do simulado
            for i, questao_base in enumerate(questoes_base, 1):
                # Mapear matéria para área ENEM
                area_enem = getattr(questao_base, 'area_enem', 
                                  self.mapear_materia_para_area(questao_base.materia))
                
                questao_simulado = Questao(
                    numero=i,
                    texto=questao_base.texto,
                    area=area_enem,
                    dificuldade=questao_base.dificuldade,
                    resposta_correta=questao_base.resposta_correta,
                    simulado_id=simulado.id,
                    questao_base_id=questao_base.id
                )
                
                db.session.add(questao_simulado)
                db.session.flush()  # Para obter o ID da questão
                
                # Criar alternativas
                alternativas = [
                    ('A', questao_base.opcao_a),
                    ('B', questao_base.opcao_b),
                    ('C', questao_base.opcao_c),
                    ('D', questao_base.opcao_d),
                    ('E', questao_base.opcao_e)
                ]
                
                for letra, texto_alt in alternativas:
                    alternativa = Alternativa(
                        letra=letra,
                        texto=texto_alt,
                        questao_id=questao_simulado.id
                    )
                    db.session.add(alternativa)
            
            db.session.commit()
            
            print(f"Simulado '{titulo}' criado com {len(questoes_base)} questões")
            print(f"ID do simulado: {simulado.id}")
            
            return simulado
    
    def mapear_materia_para_area(self, materia):
        """Mapeia matéria específica para área do ENEM"""
        mapeamento = {
            'Português': 'Linguagens',
            'Artes': 'Linguagens',
            'Inglês': 'Linguagens',
            'Espanhol': 'Linguagens',
            'Matemática': 'Matemática',
            'História': 'Humanas',
            'Geografia': 'Humanas',
            'Filosofia': 'Humanas',
            'Sociologia': 'Humanas',
            'Física': 'Natureza',
            'Química': 'Natureza',
            'Biologia': 'Natureza',
            'Educação Física': 'Linguagens'
        }
        
        return mapeamento.get(materia, 'Outras')
    
    def gerar_simulado_completo_enem(self, user_id, titulo_base="Simulado ENEM"):
        """Gera um simulado completo no padrão ENEM (180 questões)"""
        questoes = self.distribuir_questoes_enem(180)
        
        if len(questoes) < 180:
            print(f"Atenção: Apenas {len(questoes)} questões disponíveis de 180 solicitadas")
        
        titulo = f"{titulo_base} - {datetime.now().strftime('%d/%m/%Y')}"
        
        return self.criar_simulado_usuario(
            user_id=user_id,
            titulo=titulo,
            questoes_base=questoes,
            areas="Linguagens, Matemática, Humanas, Natureza",
            duracao_minutos=300  # 5 horas como no ENEM real
        )
    
    def gerar_simulado_por_materia(self, user_id, materia, quantidade=20):
        """Gera um simulado focado em uma matéria específica"""
        questoes = self.obter_questoes_por_criterio(
            materias=[materia],
            quantidade=quantidade
        )
        
        titulo = f"Simulado {materia} - {datetime.now().strftime('%d/%m/%Y')}"
        
        return self.criar_simulado_usuario(
            user_id=user_id,
            titulo=titulo,
            questoes_base=questoes,
            areas=materia,
            duracao_minutos=quantidade * 2  # 2 minutos por questão
        )

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Gerador de simulados')
    
    subparsers = parser.add_subparsers(dest='comando', help='Tipo de simulado')
    
    # Simulado ENEM completo
    enem_parser = subparsers.add_parser('enem', help='Gera simulado ENEM completo')
    enem_parser.add_argument('user_id', type=int, help='ID do usuário')
    enem_parser.add_argument('--titulo', default='Simulado ENEM', help='Título base')
    
    # Simulado por matéria
    materia_parser = subparsers.add_parser('materia', help='Gera simulado por matéria')
    materia_parser.add_argument('user_id', type=int, help='ID do usuário')
    materia_parser.add_argument('materia', help='Nome da matéria')
    materia_parser.add_argument('--quantidade', type=int, default=20, help='Número de questões')
    
    # Simulado personalizado
    custom_parser = subparsers.add_parser('custom', help='Gera simulado personalizado')
    custom_parser.add_argument('user_id', type=int, help='ID do usuário')
    custom_parser.add_argument('--materias', nargs='+', help='Lista de matérias')
    custom_parser.add_argument('--quantidade', type=int, default=45, help='Número de questões')
    custom_parser.add_argument('--titulo', default='Simulado Personalizado', help='Título')
    
    args = parser.parse_args()
    
    if not args.comando:
        parser.print_help()
        return
    
    gerador = GeradorSimulado()
    
    try:
        if args.comando == 'enem':
            simulado = gerador.gerar_simulado_completo_enem(args.user_id, args.titulo)
            
        elif args.comando == 'materia':
            simulado = gerador.gerar_simulado_por_materia(
                args.user_id, args.materia, args.quantidade
            )
            
        elif args.comando == 'custom':
            questoes = gerador.obter_questoes_por_criterio(
                materias=args.materias,
                quantidade=args.quantidade
            )
            
            simulado = gerador.criar_simulado_usuario(
                user_id=args.user_id,
                titulo=args.titulo,
                questoes_base=questoes,
                areas=', '.join(args.materias or ['Todas']),
                duracao_minutos=args.quantidade * 2
            )
        
        if simulado:
            print(f"✅ Simulado criado com sucesso! ID: {simulado.id}")
        else:
            print("❌ Falha ao criar simulado")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()