# scripts/gerador_enem_oficial.py
"""
Gerador de simulados com as áreas oficiais do ENEM e diferentes estratégias de seleção
"""

import sys
from pathlib import Path
import random
from datetime import datetime
from collections import defaultdict

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from app import create_app, db
from app.models.questao import QuestaoBase, Questao, Alternativa
from app.models.simulado import Simulado
from app.models.user import User

class GeradorENEMOficial:
    """Gerador de simulados seguindo exatamente o padrão oficial do ENEM"""
    
    def __init__(self):
        self.app = create_app()
        
        # Áreas OFICIAIS do ENEM com suas disciplinas
        self.areas_enem_oficiais = {
            'Ciências Humanas e suas Tecnologias': {
                'disciplinas': ['História', 'Geografia', 'Filosofia', 'Sociologia'],
                'questoes_enem': 45,
                'codigo': 'CH'
            },
            'Ciências da Natureza e suas Tecnologias': {
                'disciplinas': ['Biologia', 'Física', 'Química'],
                'questoes_enem': 45,
                'codigo': 'CN'
            },
            'Linguagens, Códigos e suas Tecnologias': {
                'disciplinas': ['Português', 'Literatura', 'Inglês', 'Espanhol', 'Artes', 'Educação Física', 'TIC'],
                'questoes_enem': 45,
                'codigo': 'LC'
            },
            'Matemática e suas Tecnologias': {
                'disciplinas': ['Matemática'],
                'questoes_enem': 45,
                'codigo': 'MT'
            }
        }
    
    def mapear_disciplina_para_area_oficial(self, disciplina):
        """Mapeia disciplina específica para área oficial do ENEM"""
        mapeamento = {
            # Ciências Humanas e suas Tecnologias
            'História': 'Ciências Humanas e suas Tecnologias',
            'Geografia': 'Ciências Humanas e suas Tecnologias', 
            'Filosofia': 'Ciências Humanas e suas Tecnologias',
            'Sociologia': 'Ciências Humanas e suas Tecnologias',
            
            # Ciências da Natureza e suas Tecnologias
            'Biologia': 'Ciências da Natureza e suas Tecnologias',
            'Física': 'Ciências da Natureza e suas Tecnologias',
            'Química': 'Ciências da Natureza e suas Tecnologias',
            
            # Linguagens, Códigos e suas Tecnologias
            'Português': 'Linguagens, Códigos e suas Tecnologias',
            'Literatura': 'Linguagens, Códigos e suas Tecnologias',
            'Inglês': 'Linguagens, Códigos e suas Tecnologias',
            'Espanhol': 'Linguagens, Códigos e suas Tecnologias',
            'Artes': 'Linguagens, Códigos e suas Tecnologias',
            'Educação Física': 'Linguagens, Códigos e suas Tecnologias',
            'TIC': 'Linguagens, Códigos e suas Tecnologias',
            
            # Matemática e suas Tecnologias
            'Matemática': 'Matemática e suas Tecnologias'
        }
        
        return mapeamento.get(disciplina, 'Área não identificada')
    
    def estrategia_aleatoria_simples(self, area_oficial, quantidade):
        """Estratégia 1: Seleção completamente aleatória dentro da área"""
        with self.app.app_context():
            disciplinas_area = self.areas_enem_oficiais[area_oficial]['disciplinas']
            
            questoes = QuestaoBase.query.filter(
                QuestaoBase.ativa == True,
                QuestaoBase.materia.in_(disciplinas_area)
            ).all()
            
            if len(questoes) < quantidade:
                print(f"⚠️ Apenas {len(questoes)} questões disponíveis para {area_oficial}")
                return questoes
            
            return random.sample(questoes, quantidade)
    
    def estrategia_distribuicao_equilibrada(self, area_oficial, quantidade):
        """Estratégia 2: Distribui questões equilibradamente entre disciplinas da área"""
        with self.app.app_context():
            disciplinas_area = self.areas_enem_oficiais[area_oficial]['disciplinas']
            questoes_selecionadas = []
            
            questoes_por_disciplina = quantidade // len(disciplinas_area)
            resto = quantidade % len(disciplinas_area)
            
            for i, disciplina in enumerate(disciplinas_area):
                # Distribuir resto entre as primeiras disciplinas
                qtd_disciplina = questoes_por_disciplina + (1 if i < resto else 0)
                
                questoes_disciplina = QuestaoBase.query.filter(
                    QuestaoBase.ativa == True,
                    QuestaoBase.materia == disciplina
                ).all()
                
                if len(questoes_disciplina) < qtd_disciplina:
                    print(f"⚠️ {disciplina}: apenas {len(questoes_disciplina)} questões disponíveis de {qtd_disciplina} solicitadas")
                    questoes_selecionadas.extend(questoes_disciplina)
                else:
                    questoes_selecionadas.extend(random.sample(questoes_disciplina, qtd_disciplina))
                
                print(f"📚 {disciplina}: {len(questoes_selecionadas[-qtd_disciplina:]) if len(questoes_selecionadas) >= qtd_disciplina else len(questoes_disciplina)} questões")
            
            return questoes_selecionadas
    
    def estrategia_dificuldade_progressiva(self, area_oficial, quantidade):
        """Estratégia 3: Mistura questões fáceis, médias e difíceis"""
        with self.app.app_context():
            disciplinas_area = self.areas_enem_oficiais[area_oficial]['disciplinas']
            
            # Distribuição por dificuldade (similar ao ENEM real)
            faceis = int(quantidade * 0.30)      # 30% fáceis (0.0-0.4)
            medias = int(quantidade * 0.50)      # 50% médias (0.4-0.7)
            dificeis = quantidade - faceis - medias  # 20% difíceis (0.7-1.0)
            
            questoes_selecionadas = []
            
            # Questões fáceis
            questoes_faceis = QuestaoBase.query.filter(
                QuestaoBase.ativa == True,
                QuestaoBase.materia.in_(disciplinas_area),
                QuestaoBase.dificuldade <= 0.4
            ).all()
            
            if len(questoes_faceis) >= faceis:
                questoes_selecionadas.extend(random.sample(questoes_faceis, faceis))
            else:
                questoes_selecionadas.extend(questoes_faceis)
            
            # Questões médias
            questoes_medias = QuestaoBase.query.filter(
                QuestaoBase.ativa == True,
                QuestaoBase.materia.in_(disciplinas_area),
                QuestaoBase.dificuldade > 0.4,
                QuestaoBase.dificuldade <= 0.7
            ).all()
            
            if len(questoes_medias) >= medias:
                questoes_selecionadas.extend(random.sample(questoes_medias, medias))
            else:
                questoes_selecionadas.extend(questoes_medias)
            
            # Questões difíceis
            questoes_dificeis = QuestaoBase.query.filter(
                QuestaoBase.ativa == True,
                QuestaoBase.materia.in_(disciplinas_area),
                QuestaoBase.dificuldade > 0.7
            ).all()
            
            if len(questoes_dificeis) >= dificeis:
                questoes_selecionadas.extend(random.sample(questoes_dificeis, dificeis))
            else:
                questoes_selecionadas.extend(questoes_dificeis)
            
            print(f"📊 {area_oficial}: {len(questoes_selecionadas)} questões")
            print(f"   🟢 Fáceis: {min(len(questoes_faceis), faceis)}")
            print(f"   🟡 Médias: {min(len(questoes_medias), medias)}")
            print(f"   🔴 Difíceis: {min(len(questoes_dificeis), dificeis)}")
            
            return questoes_selecionadas
    
    def estrategia_baseada_historico_usuario(self, area_oficial, quantidade, user_id):
        """Estratégia 4: Prioriza questões de tópicos onde o usuário tem mais dificuldade"""
        with self.app.app_context():
            disciplinas_area = self.areas_enem_oficiais[area_oficial]['disciplinas']
            
            # Analisar desempenho histórico do usuário por tópico
            from sqlalchemy import func
            
            desempenho_topicos = db.session.query(
                QuestaoBase.topico,
                func.count(Questao.id).label('total'),
                func.sum(
                    db.case(
                        (Questao.resposta_usuario == Questao.resposta_correta, 1),
                        else_=0
                    )
                ).label('acertos')
            ).join(
                Questao, QuestaoBase.id == Questao.questao_base_id
            ).join(
                Simulado, Questao.simulado_id == Simulado.id
            ).filter(
                Simulado.user_id == user_id,
                Simulado.status == 'Concluído',
                QuestaoBase.materia.in_(disciplinas_area)
            ).group_by(QuestaoBase.topico).all()
            
            # Calcular percentual de acerto por tópico
            topicos_dificeis = []
            for topico, total, acertos in desempenho_topicos:
                if total >= 3:  # Só considerar tópicos com pelo menos 3 questões
                    percentual = (acertos / total) * 100 if total > 0 else 0
                    if percentual < 60:  # Tópicos com menos de 60% de acerto
                        topicos_dificeis.append(topico)
            
            questoes_selecionadas = []
            
            # 70% das questões de tópicos difíceis para o usuário
            qtd_topicos_dificeis = int(quantidade * 0.7)
            if topicos_dificeis:
                questoes_dificeis_usuario = QuestaoBase.query.filter(
                    QuestaoBase.ativa == True,
                    QuestaoBase.materia.in_(disciplinas_area),
                    QuestaoBase.topico.in_(topicos_dificeis)
                ).all()
                
                if len(questoes_dificeis_usuario) >= qtd_topicos_dificeis:
                    questoes_selecionadas.extend(random.sample(questoes_dificeis_usuario, qtd_topicos_dificeis))
                else:
                    questoes_selecionadas.extend(questoes_dificeis_usuario)
            
            # 30% questões gerais da área para completar
            qtd_restante = quantidade - len(questoes_selecionadas)
            if qtd_restante > 0:
                questoes_gerais = QuestaoBase.query.filter(
                    QuestaoBase.ativa == True,
                    QuestaoBase.materia.in_(disciplinas_area),
                    ~QuestaoBase.id.in_([q.id for q in questoes_selecionadas])
                ).all()
                
                if len(questoes_gerais) >= qtd_restante:
                    questoes_selecionadas.extend(random.sample(questoes_gerais, qtd_restante))
                else:
                    questoes_selecionadas.extend(questoes_gerais)
            
            print(f"🎯 {area_oficial}: Priorizando {len(topicos_dificeis)} tópicos difíceis para o usuário")
            
            return questoes_selecionadas
    
    def gerar_simulado_enem_completo(self, user_id, estrategia='equilibrada', titulo_base="ENEM"):
        """
        Gera simulado ENEM completo (180 questões) usando estratégia especificada
        
        Estratégias disponíveis:
        - 'aleatoria': Seleção completamente aleatória
        - 'equilibrada': Distribui questões entre disciplinas  
        - 'dificuldade': Mistura fáceis, médias e difíceis
        - 'personalizada': Baseada no histórico do usuário
        """
        
        with self.app.app_context():
            print(f"🎯 Gerando simulado ENEM com estratégia: {estrategia}")
            print("=" * 60)
            
            todas_questoes = []
            
            for area_oficial, config in self.areas_enem_oficiais.items():
                quantidade = config['questoes_enem']
                
                print(f"\n📚 {area_oficial} ({config['codigo']}) - {quantidade} questões")
                print("-" * 50)
                
                if estrategia == 'aleatoria':
                    questoes_area = self.estrategia_aleatoria_simples(area_oficial, quantidade)
                elif estrategia == 'equilibrada':
                    questoes_area = self.estrategia_distribuicao_equilibrada(area_oficial, quantidade)
                elif estrategia == 'dificuldade':
                    questoes_area = self.estrategia_dificuldade_progressiva(area_oficial, quantidade)
                elif estrategia == 'personalizada':
                    questoes_area = self.estrategia_baseada_historico_usuario(area_oficial, quantidade, user_id)
                else:
                    print(f"❌ Estratégia '{estrategia}' não reconhecida. Usando 'equilibrada'")
                    questoes_area = self.estrategia_distribuicao_equilibrada(area_oficial, quantidade)
                
                # Adicionar área oficial às questões
                for questao in questoes_area:
                    questao.area_enem_oficial = area_oficial
                
                todas_questoes.extend(questoes_area)
            
            # Embaralhar questões para simular ordem aleatória do ENEM
            random.shuffle(todas_questoes)
            
            print(f"\n✅ Total de questões selecionadas: {len(todas_questoes)}")
            
            # Criar simulado
            titulo = f"{titulo_base} {estrategia.title()} - {datetime.now().strftime('%d/%m/%Y')}"
            
            return self.criar_simulado_oficial(user_id, titulo, todas_questoes)
    
    def criar_simulado_oficial(self, user_id, titulo, questoes_base):
        """Cria simulado com áreas oficiais do ENEM"""
        with self.app.app_context():
            # Verificar usuário
            usuario = User.query.get(user_id)
            if not usuario:
                print(f"❌ Usuário {user_id} não encontrado!")
                return None
            
            # Criar simulado
            simulado = Simulado(
                titulo=titulo,
                areas="ENEM Completo - 4 Áreas",
                duracao_minutos=300,  # 5 horas como no ENEM real
                user_id=user_id,
                status='Pendente'
            )
            
            db.session.add(simulado)
            db.session.flush()
            
            # Criar questões do simulado
            for i, questao_base in enumerate(questoes_base, 1):
                area_oficial = getattr(questao_base, 'area_enem_oficial', 
                                     self.mapear_disciplina_para_area_oficial(questao_base.materia))
                
                # Usar código da área para compatibilidade com sistema existente
                area_codigo = self.areas_enem_oficiais[area_oficial]['codigo']
                
                questao_simulado = Questao(
                    numero=i,
                    texto=questao_base.texto,
                    area=area_codigo,  # CH, CN, LC, MT
                    dificuldade=questao_base.dificuldade,
                    resposta_correta=questao_base.resposta_correta,
                    simulado_id=simulado.id,
                    questao_base_id=questao_base.id
                )
                
                db.session.add(questao_simulado)
                db.session.flush()
                
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
            
            print(f"✅ Simulado '{titulo}' criado com sucesso!")
            print(f"🆔 ID do simulado: {simulado.id}")
            
            return simulado
    
    def relatorio_disponibilidade_questoes(self):
        """Gera relatório de quantas questões estão disponíveis por área"""
        with self.app.app_context():
            print("📊 RELATÓRIO DE DISPONIBILIDADE DE QUESTÕES")
            print("=" * 60)
            
            total_geral = 0
            
            for area_oficial, config in self.areas_enem_oficiais.items():
                disciplinas = config['disciplinas']
                necessarias = config['questoes_enem']
                
                print(f"\n🎯 {area_oficial}")
                print(f"Questões necessárias para ENEM: {necessarias}")
                print("-" * 40)
                
                total_area = 0
                for disciplina in disciplinas:
                    count = QuestaoBase.query.filter(
                        QuestaoBase.ativa == True,
                        QuestaoBase.materia == disciplina
                    ).count()
                    
                    total_area += count
                    print(f"  📚 {disciplina}: {count} questões")
                
                print(f"  📊 Total na área: {total_area}")
                
                if total_area >= necessarias:
                    print(f"  ✅ Suficiente para ENEM ({total_area - necessarias} extras)")
                else:
                    print(f"  ❌ Insuficiente ({necessarias - total_area} faltando)")
                
                total_geral += total_area
            
            print(f"\n🎯 RESUMO GERAL")
            print(f"Total de questões: {total_geral}")
            print(f"Necessárias para ENEM: 180")
            
            if total_geral >= 180:
                print(f"✅ Suficiente para ENEM completo ({total_geral - 180} extras)")
            else:
                print(f"❌ Insuficiente ({180 - total_geral} questões faltando)")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Gerador ENEM com áreas oficiais')
    
    subparsers = parser.add_subparsers(dest='comando', help='Comandos disponíveis')
    
    # Relatório de disponibilidade
    subparsers.add_parser('relatorio', help='Relatório de questões disponíveis')
    
    # Simulado ENEM com estratégias
    enem_parser = subparsers.add_parser('gerar', help='Gera simulado ENEM')
    enem_parser.add_argument('user_id', type=int, help='ID do usuário')
    enem_parser.add_argument('--estrategia', choices=['aleatoria', 'equilibrada', 'dificuldade', 'personalizada'],
                            default='equilibrada', help='Estratégia de seleção')
    enem_parser.add_argument('--titulo', default='ENEM', help='Título base do simulado')
    
    args = parser.parse_args()
    
    if not args.comando:
        parser.print_help()
        return
    
    gerador = GeradorENEMOficial()
    
    if args.comando == 'relatorio':
        gerador.relatorio_disponibilidade_questoes()
        
    elif args.comando == 'gerar':
        try:
            simulado = gerador.gerar_simulado_enem_completo(
                user_id=args.user_id,
                estrategia=args.estrategia,
                titulo_base=args.titulo
            )
            
            if simulado:
                print(f"\n🎉 Simulado criado com sucesso!")
                print(f"📝 Título: {simulado.titulo}")
                print(f"🆔 ID: {simulado.id}")
                print(f"⏱️ Duração: {simulado.duracao_minutos} minutos")
            else:
                print("❌ Falha ao criar simulado")
                
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()