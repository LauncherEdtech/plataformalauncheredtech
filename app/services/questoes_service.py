# app/services/questoes_service.py
"""
Serviço de questões - Sistema centralizado para busca, filtragem e
rastreamento de desempenho nas questões individuais.
"""

import psycopg2
import psycopg2.extras
from typing import List, Dict, Optional
from datetime import datetime
from app import db

# ============================================================
#  CONEXÃO
# ============================================================
DB_PARAMS = {
    'host': '34.63.141.69',
    'port': '5432',
    'database': 'plataforma',
    'user': 'postgres',
    'password': '22092021Dd$'
}


def _conn():
    conn = psycopg2.connect(**DB_PARAMS)
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn


# ============================================================
#  DISCOVERY  (Explorar)
# ============================================================

def listar_provas() -> List[str]:
    """Retorna lista de vestibulares/provas distintos no banco."""
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT COALESCE(NULLIF(prova,''), 'ENEM') AS prova
        FROM questoes_base
        WHERE ativa = true
        ORDER BY 1
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return [r['prova'] for r in rows if r['prova']]


def listar_materias_com_contagens(provas: List[str] = None) -> List[Dict]:
    """
    Retorna matérias com total de questões e número de tópicos.
    Filtrado opcionalmente por lista de provas.
    """
    conn = _conn()
    cur = conn.cursor()

    where = "WHERE ativa = true"
    params = []
    if provas:
        placeholders = ','.join(['%s'] * len(provas))
        where += f" AND COALESCE(NULLIF(prova,''), 'ENEM') IN ({placeholders})"
        params = provas

    cur.execute(f"""
        SELECT 
            materia,
            COUNT(*) AS total_questoes,
            COUNT(DISTINCT topico) AS total_topicos,
            COUNT(DISTINCT subtopico) AS total_subtopicos
        FROM questoes_base
        {where}
        GROUP BY materia
        ORDER BY materia
    """, params)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return [dict(r) for r in rows]


def listar_topicos_por_materia(materia: str, provas: List[str] = None) -> List[Dict]:
    """
    Retorna tópicos de uma matéria com contagens.
    Cada tópico contém seus subtópicos.
    """
    conn = _conn()
    cur = conn.cursor()

    where = "WHERE ativa = true AND materia = %s"
    params = [materia]
    if provas:
        placeholders = ','.join(['%s'] * len(provas))
        where += f" AND COALESCE(NULLIF(prova,''), 'ENEM') IN ({placeholders})"
        params += provas

    cur.execute(f"""
        SELECT 
            topico,
            subtopico,
            COUNT(*) AS total_questoes
        FROM questoes_base
        {where}
        AND topico IS NOT NULL AND topico != ''
        GROUP BY topico, subtopico
        ORDER BY topico, subtopico
    """, params)
    rows = cur.fetchall()
    cur.close(); conn.close()

    # Agrupar subtópicos dentro de cada tópico
    topicos: Dict[str, Dict] = {}
    for r in rows:
        t = r['topico']
        if t not in topicos:
            topicos[t] = {'topico': t, 'total_questoes': 0, 'subtopicos': []}
        topicos[t]['total_questoes'] += r['total_questoes']
        if r['subtopico']:
            topicos[t]['subtopicos'].append({
                'nome': r['subtopico'],
                'total_questoes': r['total_questoes']
            })

    return list(topicos.values())


def listar_todas_materias_topicos(provas: List[str] = None) -> Dict[str, List[Dict]]:
    """
    Retorna estrutura completa: { materia: [{ topico, subtopicos, total_questoes }] }
    Usada para montar a tela Netflix.
    """
    materias = listar_materias_com_contagens(provas)
    resultado = {}
    for m in materias:
        topicos = listar_topicos_por_materia(m['materia'], provas)
        resultado[m['materia']] = topicos
    return resultado


# ============================================================
#  BUSCA DE QUESTÕES  (Praticar)
# ============================================================

def buscar_questoes(
    materia: str = None,
    topico: str = None,
    subtopico: str = None,
    provas: List[str] = None,
    quantidade: int = 20,
    excluir_ids: List[int] = None,
    dificuldade_min: float = None,
    dificuldade_max: float = None
) -> List[Dict]:
    """
    Busca questões com múltiplos filtros.
    Retorna lista de questões em formato dict completo.
    """
    conn = _conn()
    cur = conn.cursor()

    clauses = ["ativa = true"]
    params = []

    if materia:
        clauses.append("materia = %s"); params.append(materia)
    if topico:
        clauses.append("topico = %s"); params.append(topico)
    if subtopico:
        clauses.append("subtopico = %s"); params.append(subtopico)
    if provas:
        ph = ','.join(['%s'] * len(provas))
        clauses.append(f"COALESCE(NULLIF(prova,''), 'ENEM') IN ({ph})")
        params += provas
    if excluir_ids:
        ph = ','.join(['%s'] * len(excluir_ids))
        clauses.append(f"id NOT IN ({ph})")
        params += excluir_ids
    if dificuldade_min is not None:
        clauses.append("dificuldade >= %s"); params.append(dificuldade_min)
    if dificuldade_max is not None:
        clauses.append("dificuldade <= %s"); params.append(dificuldade_max)

    where = "WHERE " + " AND ".join(clauses)

    cur.execute(f"""
        SELECT 
            id, texto, materia, topico, subtopico,
            opcao_a, opcao_b, opcao_c, opcao_d, opcao_e,
            resposta_correta, explicacao, explicacao_distratores,
            imagem_url, dificuldade, citacao, fonte, ano, prova,
            dica, tags, pre_requisitos, classificacao, colecao
        FROM questoes_base
        {where}
        ORDER BY RANDOM()
        LIMIT %s
    """, params + [quantidade])

    rows = cur.fetchall()
    cur.close(); conn.close()
    return [_normalizar_questao(dict(r)) for r in rows]


def _normalizar_questao(q: Dict) -> Dict:
    """
    Normaliza campos que podem vir como arrays do PostgreSQL (TEXT[] ou JSONB[])
    para strings simples antes de passar ao template.
    """
    # Campos de texto simples
    for campo in ('pre_requisitos', 'dica', 'tags', 'classificacao', 'colecao', 'explicacao'):
        val = q.get(campo)
        if isinstance(val, list):
            q[campo] = '\n'.join(str(v) for v in val if v) if val else ''
        elif val is None:
            q[campo] = ''

    # explicacao_distratores: pode ser lista de dicts {letra, explicacao} ou lista de strings
    dist = q.get('explicacao_distratores')
    if dist is None:
        q['explicacao_distratores'] = ''
    elif isinstance(dist, list):
        partes = []
        for item in dist:
            if isinstance(item, dict):
                letra = item.get('letra') or item.get('alternativa') or ''
                texto = item.get('explicacao') or item.get('texto') or item.get('descricao') or str(item)
                if letra:
                    partes.append(f'<strong>{letra})</strong> {texto}')
                else:
                    partes.append(str(texto))
            elif item:
                partes.append(str(item))
        q['explicacao_distratores'] = '<br><br>'.join(partes) if partes else ''
    # Se já for string mantém como está

    return q


def buscar_questao_por_id(questao_id: int) -> Optional[Dict]:
    """Busca questão individual por ID."""
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            id, texto, materia, topico, subtopico,
            opcao_a, opcao_b, opcao_c, opcao_d, opcao_e,
            resposta_correta, explicacao, explicacao_distratores,
            imagem_url, dificuldade, citacao, fonte, ano, prova,
            dica, tags, pre_requisitos, classificacao, colecao
        FROM questoes_base
        WHERE id = %s AND ativa = true
    """, (questao_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return _normalizar_questao(dict(row)) if row else None


# ============================================================
#  PERFORMANCE TRACKING  (Para Machine Learning futuro)
# ============================================================

def garantir_tabela_performance():
    """Cria tabela de rastreamento se não existir."""
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS questao_performance (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            questao_id INTEGER NOT NULL,
            resposta_usuario VARCHAR(1),
            correta BOOLEAN NOT NULL,
            tempo_resposta INTEGER,          -- segundos
            materia VARCHAR(100),
            topico VARCHAR(100),
            subtopico VARCHAR(100),
            prova VARCHAR(100),
            dificuldade FLOAT,
            usou_dica BOOLEAN DEFAULT FALSE,
            usou_pre_requisitos BOOLEAN DEFAULT FALSE,
            sessao_id VARCHAR(100),          -- agrupar questões da mesma sessão
            created_at TIMESTAMP DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_qp_user ON questao_performance(user_id);
        CREATE INDEX IF NOT EXISTS idx_qp_materia ON questao_performance(user_id, materia);
        CREATE INDEX IF NOT EXISTS idx_qp_topico ON questao_performance(user_id, topico);
        CREATE INDEX IF NOT EXISTS idx_qp_questao ON questao_performance(questao_id);
    """)
    conn.commit()
    cur.close(); conn.close()


def registrar_resposta(
    user_id: int,
    questao_id: int,
    resposta_usuario: str,
    correta: bool,
    tempo_resposta: int = None,
    materia: str = None,
    topico: str = None,
    subtopico: str = None,
    prova: str = None,
    dificuldade: float = None,
    usou_dica: bool = False,
    usou_pre_requisitos: bool = False,
    sessao_id: str = None
) -> bool:
    """
    Registra resposta do usuário para tracking de desempenho.
    Retorna True se sucesso.
    """
    try:
        conn = _conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO questao_performance (
                user_id, questao_id, resposta_usuario, correta,
                tempo_resposta, materia, topico, subtopico, prova,
                dificuldade, usou_dica, usou_pre_requisitos, sessao_id
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            user_id, questao_id, resposta_usuario, correta,
            tempo_resposta, materia, topico, subtopico, prova,
            dificuldade, usou_dica, usou_pre_requisitos, sessao_id
        ))
        # Atualizar contadores na questoes_base
        if correta:
            cur.execute("""
                UPDATE questoes_base
                SET vezes_utilizada = COALESCE(vezes_utilizada,0) + 1,
                    vezes_acertada  = COALESCE(vezes_acertada,0) + 1
                WHERE id = %s
            """, (questao_id,))
        else:
            cur.execute("""
                UPDATE questoes_base
                SET vezes_utilizada = COALESCE(vezes_utilizada,0) + 1
                WHERE id = %s
            """, (questao_id,))
        conn.commit()
        cur.close(); conn.close()
        return True
    except Exception as e:
        print(f"Erro ao registrar resposta: {e}")
        return False


# ============================================================
#  ANÁLISE DE DESEMPENHO  (Base para recomendações futuras)
# ============================================================

def calcular_desempenho_usuario(user_id: int) -> Dict:
    """
    Retorna análise completa de desempenho por matéria/tópico.
    Base para sistema de recomendações futuro.
    """
    try:
        conn = _conn()
        cur = conn.cursor()

        # Desempenho por matéria
        cur.execute("""
            SELECT 
                materia,
                COUNT(*) AS total,
                SUM(CASE WHEN correta THEN 1 ELSE 0 END) AS acertos,
                AVG(CASE WHEN correta THEN 1.0 ELSE 0.0 END) * 100 AS percentual,
                AVG(tempo_resposta) AS tempo_medio
            FROM questao_performance
            WHERE user_id = %s AND materia IS NOT NULL
            GROUP BY materia
            ORDER BY percentual
        """, (user_id,))
        por_materia = [dict(r) for r in cur.fetchall()]

        # Tópicos mais fracos
        cur.execute("""
            SELECT 
                materia, topico,
                COUNT(*) AS total,
                AVG(CASE WHEN correta THEN 1.0 ELSE 0.0 END) * 100 AS percentual
            FROM questao_performance
            WHERE user_id = %s AND topico IS NOT NULL AND materia IS NOT NULL
            GROUP BY materia, topico
            HAVING COUNT(*) >= 3
            ORDER BY percentual
            LIMIT 5
        """, (user_id,))
        topicos_fracos = [dict(r) for r in cur.fetchall()]

        # Streak atual (dias consecutivos)
        cur.execute("""
            SELECT COUNT(DISTINCT DATE(created_at)) AS dias
            FROM questao_performance
            WHERE user_id = %s
            AND created_at >= NOW() - INTERVAL '30 days'
        """, (user_id,))
        row = cur.fetchone()
        dias_ativos = row['dias'] if row else 0

        # Total geral
        cur.execute("""
            SELECT 
                COUNT(*) AS total,
                SUM(CASE WHEN correta THEN 1 ELSE 0 END) AS acertos
            FROM questao_performance
            WHERE user_id = %s
        """, (user_id,))
        totais = dict(cur.fetchone() or {'total': 0, 'acertos': 0})

        cur.close(); conn.close()

        return {
            'por_materia': por_materia,
            'topicos_fracos': topicos_fracos,
            'dias_ativos': dias_ativos,
            'totais': totais
        }
    except Exception as e:
        print(f"Erro ao calcular desempenho: {e}")
        return {'por_materia': [], 'topicos_fracos': [], 'dias_ativos': 0, 'totais': {'total': 0, 'acertos': 0}}



def sugerir_proximas_questoes(user_id: int, limite: int = 10) -> List[Dict]:
    """
    Sugere questões baseadas no desempenho do usuário.
    Prioriza tópicos com menor percentual de acerto.
    Retorna lista de questões recomendadas.
    """
    try:
        conn = _conn()
        cur = conn.cursor()

        # Encontrar tópicos fracos do usuário
        cur.execute("""
            SELECT materia, topico,
                   AVG(CASE WHEN correta THEN 1.0 ELSE 0.0 END) AS percentual,
                   array_agg(questao_id) AS questoes_vistas
            FROM questao_performance
            WHERE user_id = %s AND topico IS NOT NULL
            GROUP BY materia, topico
            HAVING COUNT(*) >= 2
            ORDER BY percentual
            LIMIT 3
        """, (user_id,))
        topicos_fracos = cur.fetchall()

        questoes = []

        for tf in topicos_fracos:
            ids_vistos = list(tf['questoes_vistas'] or [])
            ph_excluir = ','.join(['%s'] * len(ids_vistos)) if ids_vistos else 'NULL'

            cur.execute(f"""
                SELECT id, texto, materia, topico, subtopico, dificuldade
                FROM questoes_base
                WHERE materia = %s AND topico = %s AND ativa = true
                {"AND id NOT IN (" + ph_excluir + ")" if ids_vistos else ""}
                ORDER BY RANDOM()
                LIMIT 3
            """, [tf['materia'], tf['topico']] + ids_vistos)
            questoes += [dict(r) for r in cur.fetchall()]

        cur.close(); conn.close()
        return questoes[:limite]
    except Exception as e:
        print(f"Erro ao sugerir questões: {e}")
        return []


# ============================================================
#  INICIALIZAÇÃO
# ============================================================

def inicializar():
    """Chamado no startup da aplicação para garantir tabelas."""
    try:
        garantir_tabela_performance()
        print("✅ questoes_service: tabela de performance OK")
    except Exception as e:
        print(f"⚠️ questoes_service: {e}")
