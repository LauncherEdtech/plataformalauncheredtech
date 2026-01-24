# app/services/gerador_questoes.py
"""
Gerador de questões CORRIGIDO - Remove erro de atributo
"""

import psycopg2
import random
from typing import List, Dict
from collections import defaultdict

class GeradorQuestoes:
    """Gerador inteligente de questões do banco PostgreSQL - CORRIGIDO"""
    
    AREAS_DISCIPLINAS = {
        'Linguagens': ['Português', 'Literatura', 'Inglês', 'Espanhol', 'Artes'],
        'Matemática': ['Matemática'],
        'Humanas': ['História', 'Geografia', 'Filosofia', 'Sociologia'],
        'Natureza': ['Física', 'Química', 'Biologia'],
        'Física': ['Física'],
        'Química': ['Química'],
        'Biologia': ['Biologia'],
        'História': ['História'],
        'Geografia': ['Geografia']
    }
    
    def __init__(self):
        self.conn_params = {
            'host': '34.63.141.69',
            'port': '5432',
            'database': 'plataforma',
            'user': 'postgres',
            'password': '22092021Dd$'
        }
    
    def _get_connection(self):
        """Cria conexão direta com PostgreSQL"""
        return psycopg2.connect(**self.conn_params)
    
    def obter_questoes_disponiveis(self, materias: List[str] = None) -> Dict[str, int]:
        """MÉTODO CORRIGIDO: Retorna quantidade de questões disponíveis por matéria"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if materias:
                placeholders = ','.join(['%s'] * len(materias))
                query = f"""
                    SELECT materia, COUNT(*) 
                    FROM questoes_base 
                    WHERE ativa = true AND materia IN ({placeholders})
                    GROUP BY materia
                """
                cursor.execute(query, materias)
            else:
                cursor.execute("""
                    SELECT materia, COUNT(*) 
                    FROM questoes_base 
                    WHERE ativa = true 
                    GROUP BY materia
                """)
            
            return dict(cursor.fetchall())
        
        finally:
            cursor.close()
            conn.close()
    
    def gerar_questoes_por_areas(self, areas_selecionadas: List[str], 
                                total_questoes: int, 
                                estrategia: str = 'equilibrada') -> List[Dict]:
        """Gera questões baseadas nas áreas selecionadas - CORRIGIDO"""
        
        # Mapear áreas para disciplinas
        disciplinas_finais = []
        for area in areas_selecionadas:
            if area in self.AREAS_DISCIPLINAS:
                disciplinas_finais.extend(self.AREAS_DISCIPLINAS[area])
            else:
                disciplinas_finais.append(area)
        
        # Remover duplicatas
        disciplinas_finais = list(dict.fromkeys(disciplinas_finais))
        
        # Verificar disponibilidade
        disponibilidade = self.obter_questoes_disponiveis(disciplinas_finais)
        disciplinas_com_questoes = [d for d in disciplinas_finais if disponibilidade.get(d, 0) > 0]
        
        if not disciplinas_com_questoes:
            print(f"❌ Nenhuma questão encontrada para: {disciplinas_finais}")
            print(f"📊 Disponível: {disponibilidade}")
            return []
        
        # Distribuir questões entre disciplinas
        questoes_por_disciplina = max(1, total_questoes // len(disciplinas_com_questoes))
        questoes_extras = total_questoes % len(disciplinas_com_questoes)
        
        questoes_selecionadas = []
        
        for i, disciplina in enumerate(disciplinas_com_questoes):
            quantidade = questoes_por_disciplina
            if i < questoes_extras:
                quantidade += 1
            
            # Não exceder disponibilidade
            quantidade = min(quantidade, disponibilidade.get(disciplina, 0))
            
            if quantidade > 0:
                questoes = self._selecionar_questoes_disciplina(disciplina, quantidade, estrategia)
                questoes_selecionadas.extend(questoes)
        
        # Embaralhar questões finais
        random.shuffle(questoes_selecionadas)
        
        return questoes_selecionadas[:total_questoes]
    
    def _selecionar_questoes_disciplina(self, disciplina: str, quantidade: int, 
                                       estrategia: str) -> List[Dict]:
        """Seleciona questões específicas de uma disciplina"""
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, texto, opcao_a, opcao_b, opcao_c, opcao_d, opcao_e,
                       resposta_correta, explicacao, materia, topico, dificuldade
                FROM questoes_base
                WHERE materia = %s AND ativa = true
                ORDER BY RANDOM()
                LIMIT %s
            """, (disciplina, quantidade))
            
            questoes = cursor.fetchall()
            
            # Converter para dicionários
            questoes_dict = []
            for q in questoes:
                questoes_dict.append({
                    'id': q[0],
                    'texto': q[1] or f'Questão de {disciplina}',
                    'opcao_a': q[2] or 'Alternativa A',
                    'opcao_b': q[3] or 'Alternativa B', 
                    'opcao_c': q[4] or 'Alternativa C',
                    'opcao_d': q[5] or 'Alternativa D',
                    'opcao_e': q[6] or 'Alternativa E',
                    'resposta_correta': q[7] or 'A',
                    'explicacao': q[8] or 'Explicação não disponível',
                    'materia': q[9] or disciplina,
                    'topico': q[10] or '',
                    'dificuldade': float(q[11]) if q[11] else 0.5
                })
            
            return questoes_dict
        
        finally:
            cursor.close()
            conn.close()

# Função de conveniência para usar na aplicação
def gerar_questoes_simulado(areas: List[str], quantidade: int, 
                           estrategia: str = 'equilibrada') -> List[Dict]:
    """Função principal para gerar questões para simulados - CORRIGIDA"""
    gerador = GeradorQuestoes()
    return gerador.gerar_questoes_por_areas(areas, quantidade, estrategia)

def obter_relatorio_disponibilidade() -> Dict[str, int]:
    """Retorna relatório de questões disponíveis por matéria - CORRIGIDO"""
    gerador = GeradorQuestoes()
    return gerador.obter_questoes_disponiveis()

# Função de teste
def testar_gerador_corrigido():
    """Testa o gerador corrigido"""
    print("🧪 Testando gerador corrigido...")
    
    try:
        # Teste disponibilidade
        disp = obter_relatorio_disponibilidade()
        print(f"Disponibilidade: {disp}")
        
        if not disp:
            print("❌ Nenhuma questão disponível!")
            return False
        
        # Teste geração com matéria que existe
        materias_disponiveis = list(disp.keys())
        materia_teste = materias_disponiveis[0]
        
        questoes = gerar_questoes_simulado([materia_teste], 2)
        
        if questoes:
            print(f"✅ {len(questoes)} questões geradas de {materia_teste}!")
            return True
        else:
            print("❌ Nenhuma questão gerada!")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

if __name__ == "__main__":
    testar_gerador_corrigido()
