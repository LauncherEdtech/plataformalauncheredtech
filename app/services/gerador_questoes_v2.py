# app/services/gerador_questoes.py - VERSÃO 2.0 COM MATÉRIAS INDIVIDUAIS
"""
Gerador de questões com suporte a:
1. Áreas do ENEM (Linguagens, Matemática, Humanas, Natureza)
2. Matérias Individuais (Português, Matemática, Filosofia, etc.)
"""

import psycopg2
import random
from typing import List, Dict, Tuple
from collections import defaultdict

class GeradorQuestoes:
    """Gerador inteligente de questões do banco PostgreSQL - V2"""
    
    # Mapeamento de áreas para disciplinas (mantém compatibilidade)
    AREAS_DISCIPLINAS = {
        'Linguagens': ['Português', 'Literatura', 'Inglês', 'Espanhol', 'Artes'],
        'Matemática': ['Matemática'],
        'Humanas': ['História', 'Geografia', 'Filosofia', 'Sociologia'],
        'Natureza': ['Física', 'Química', 'Biologia'],
    }
    
    # ✨ NOVO: Lista de todas as matérias individuais disponíveis
    MATERIAS_INDIVIDUAIS = [
        'Português', 'Literatura', 'Inglês', 'Espanhol', 'Artes',
        'Matemática',
        'História', 'Geografia', 'Filosofia', 'Sociologia',
        'Física', 'Química', 'Biologia'
    ]
    def __init__(self):
        # ✅ Única fonte de verdade do banco
        self.database_url = os.environ.get("DATABASE_URL")
        if not self.database_url:
            raise RuntimeError(
                "DATABASE_URL não definido. Configure em /etc/launcher.env (produção) ou .env (dev)."
            )

    def _get_connection(self):
        """Cria conexão direta com PostgreSQL usando DATABASE_URL"""
        # sslmode=require é o padrão recomendado no RDS
        return psycopg2.connect(self.database_url, sslmode="require", connect_timeout=10)
            
        
    
    # ==================== MÉTODOS EXISTENTES (mantidos) ====================
    
    def obter_questoes_disponiveis(self, materias: List[str] = None) -> Dict[str, int]:
        """Retorna quantidade de questões disponíveis por matéria"""
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
        """Gera questões baseadas nas áreas selecionadas (ENEM)"""
        
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
            return []
        
        # Distribuir questões entre disciplinas
        questoes_por_disciplina = max(1, total_questoes // len(disciplinas_com_questoes))
        questoes_extras = total_questoes % len(disciplinas_com_questoes)
        
        questoes_selecionadas = []
        
        for i, disciplina in enumerate(disciplinas_com_questoes):
            quantidade = questoes_por_disciplina
            if i < questoes_extras:
                quantidade += 1
            
            quantidade = min(quantidade, disponibilidade.get(disciplina, 0))
            
            if quantidade > 0:
                questoes = self._selecionar_questoes_disciplina(disciplina, quantidade, estrategia)
                questoes_selecionadas.extend(questoes)
        
        random.shuffle(questoes_selecionadas)
        return questoes_selecionadas[:total_questoes]
    
    # ==================== NOVOS MÉTODOS PARA MATÉRIAS INDIVIDUAIS ====================
    
    def obter_topicos_materia(self, materia: str) -> List[Tuple[str, int]]:
        """
        ✨ NOVO: Retorna lista de tópicos disponíveis para uma matéria
        
        Args:
            materia: Nome da matéria (ex: 'Filosofia', 'Matemática')
            
        Returns:
            Lista de tuplas (topico, quantidade_questoes)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT topico, COUNT(*) as quantidade
                FROM questoes_base 
                WHERE ativa = true 
                AND materia = %s
                AND topico IS NOT NULL 
                AND topico != ''
                GROUP BY topico
                ORDER BY topico
            """, (materia,))
            
            resultados = cursor.fetchall()
            
            print(f"✅ {len(resultados)} tópicos encontrados para {materia}")
            return resultados
        
        except Exception as e:
            print(f"❌ Erro ao buscar tópicos: {e}")
            return []
        
        finally:
            cursor.close()
            conn.close()
    
    def gerar_questoes_por_materia_topico(self, materia: str, topico: str, 
                                          quantidade: int) -> List[Dict]:
        """
        ✨ NOVO: Gera questões de uma matéria específica e tópico (IGNORA subtópico)
        
        Args:
            materia: Matéria específica (ex: 'Filosofia')
            topico: Tópico específico (ex: 'Ética')
            quantidade: Número de questões desejadas
            
        Returns:
            Lista de questões em formato dict
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Buscar questões da matéria + tópico (ignorando subtópico)
            cursor.execute("""
                SELECT id, texto, opcao_a, opcao_b, opcao_c, opcao_d, opcao_e,
                       resposta_correta, explicacao, materia, topico, dificuldade
                FROM questoes_base
                WHERE materia = %s 
                AND topico = %s 
                AND ativa = true
                ORDER BY RANDOM()
                LIMIT %s
            """, (materia, topico, quantidade))
            
            questoes = cursor.fetchall()
            
            # Converter para dicionários
            questoes_dict = []
            for q in questoes:
                questoes_dict.append({
                    'id': q[0],
                    'texto': q[1] or f'Questão de {materia} - {topico}',
                    'opcao_a': q[2] or 'Alternativa A',
                    'opcao_b': q[3] or 'Alternativa B', 
                    'opcao_c': q[4] or 'Alternativa C',
                    'opcao_d': q[5] or 'Alternativa D',
                    'opcao_e': q[6] or 'Alternativa E',
                    'resposta_correta': q[7] or 'A',
                    'explicacao': q[8] or 'Explicação não disponível',
                    'materia': q[9] or materia,
                    'topico': q[10] or topico,
                    'dificuldade': float(q[11]) if q[11] else 0.5
                })
            
            print(f"✅ {len(questoes_dict)} questões geradas para {materia} - {topico}")
            return questoes_dict
        
        except Exception as e:
            print(f"❌ Erro ao gerar questões: {e}")
            return []
        
        finally:
            cursor.close()
            conn.close()
    
    def obter_estatisticas_materia(self, materia: str) -> Dict:
        """
        ✨ NOVO: Retorna estatísticas de uma matéria
        
        Returns:
            {
                'total_questoes': int,
                'topicos_disponiveis': int,
                'dificuldade_media': float
            }
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(DISTINCT topico) as topicos,
                    AVG(dificuldade) as dificuldade_media
                FROM questoes_base
                WHERE materia = %s AND ativa = true
            """, (materia,))
            
            resultado = cursor.fetchone()
            
            return {
                'total_questoes': resultado[0] or 0,
                'topicos_disponiveis': resultado[1] or 0,
                'dificuldade_media': float(resultado[2]) if resultado[2] else 0.5
            }
        
        except Exception as e:
            print(f"❌ Erro ao buscar estatísticas: {e}")
            return {'total_questoes': 0, 'topicos_disponiveis': 0, 'dificuldade_media': 0.5}
        
        finally:
            cursor.close()
            conn.close()
    
    # ==================== MÉTODO AUXILIAR (mantido) ====================
    
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


# ==================== FUNÇÕES DE CONVENIÊNCIA ====================

def gerar_questoes_simulado(areas: List[str], quantidade: int, 
                           estrategia: str = 'equilibrada') -> List[Dict]:
    """Função para gerar questões por áreas ENEM (mantém compatibilidade)"""
    gerador = GeradorQuestoes()
    return gerador.gerar_questoes_por_areas(areas, quantidade, estrategia)

def gerar_questoes_materia_topico(materia: str, topico: str, quantidade: int) -> List[Dict]:
    """✨ NOVA: Função para gerar questões por matéria + tópico"""
    gerador = GeradorQuestoes()
    return gerador.gerar_questoes_por_materia_topico(materia, topico, quantidade)

def obter_topicos_disponiveis(materia: str) -> List[Tuple[str, int]]:
    """✨ NOVA: Função para obter tópicos de uma matéria"""
    gerador = GeradorQuestoes()
    return gerador.obter_topicos_materia(materia)

def obter_relatorio_disponibilidade() -> Dict[str, int]:
    """Retorna relatório de questões disponíveis por matéria"""
    gerador = GeradorQuestoes()
    return gerador.obter_questoes_disponiveis()


# ==================== TESTE ====================

def testar_materias_individuais():
    """Testa o novo sistema de matérias individuais"""
    print("\n🧪 Testando sistema de matérias individuais...")
    print("=" * 60)
    
    gerador = GeradorQuestoes()
    
    # Testar disponibilidade geral
    print("\n1️⃣ Testando disponibilidade geral:")
    disponibilidade = gerador.obter_questoes_disponiveis()
    print(f"   Matérias disponíveis: {list(disponibilidade.keys())}")
    
    # Testar matéria específica
    materia_teste = 'Filosofia' if 'Filosofia' in disponibilidade else list(disponibilidade.keys())[0]
    print(f"\n2️⃣ Testando matéria: {materia_teste}")
    
    # Buscar tópicos
    topicos = gerador.obter_topicos_materia(materia_teste)
    print(f"   Tópicos encontrados: {len(topicos)}")
    for topico, qtd in topicos[:5]:  # Mostrar apenas 5 primeiros
        print(f"   - {topico}: {qtd} questões")
    
    # Testar geração de questões
    if topicos:
        topico_teste = topicos[0][0]
        print(f"\n3️⃣ Gerando 2 questões de {materia_teste} - {topico_teste}:")
        questoes = gerador.gerar_questoes_por_materia_topico(materia_teste, topico_teste, 2)
        
        if questoes:
            print(f"   ✅ {len(questoes)} questões geradas com sucesso!")
            for i, q in enumerate(questoes, 1):
                print(f"   Questão {i}: {q['texto'][:80]}...")
        else:
            print("   ❌ Nenhuma questão gerada")
    
    # Testar estatísticas
    print(f"\n4️⃣ Estatísticas de {materia_teste}:")
    stats = gerador.obter_estatisticas_materia(materia_teste)
    print(f"   Total de questões: {stats['total_questoes']}")
    print(f"   Tópicos disponíveis: {stats['topicos_disponiveis']}")
    print(f"   Dificuldade média: {stats['dificuldade_media']:.2f}")
    
    print("\n" + "=" * 60)
    print("✅ Teste concluído!\n")


if __name__ == "__main__":
    testar_materias_individuais()
