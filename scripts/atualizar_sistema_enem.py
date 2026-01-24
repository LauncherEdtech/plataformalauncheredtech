# scripts/atualizar_sistema_enem.py
"""
Script para atualizar o sistema existente para usar as áreas oficiais do ENEM
e implementar as estratégias de seleção de questões
"""

import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from app import create_app, db
from app.models.questao import QuestaoBase, Questao
from app.models.simulado import Simulado
from sqlalchemy import func, text

def atualizar_areas_questoes_existentes():
    """Atualiza questões existentes para usar áreas oficiais do ENEM"""
    app = create_app()
    
    with app.app_context():
        print("🔄 Atualizando questões existentes para áreas oficiais do ENEM...")
        
        # Mapeamento de área atual para área oficial
        mapeamento_areas = {
            'Linguagens': 'LC',  # Linguagens, Códigos e suas Tecnologias
            'Matemática': 'MT',  # Matemática e suas Tecnologias
            'Humanas': 'CH',     # Ciências Humanas e suas Tecnologias
            'Natureza': 'CN'     # Ciências da Natureza e suas Tecnologias
        }
        
        questoes_atualizadas = 0
        
        for area_antiga, area_nova in mapeamento_areas.items():
            # Atualizar questões em simulados
            questoes = Questao.query.filter_by(area=area_antiga).all()
            
            for questao in questoes:
                questao.area = area_nova
                questoes_atualizadas += 1
            
            print(f"✅ {len(questoes)} questões atualizadas: {area_antiga} → {area_nova}")
        
        db.session.commit()
        
        print(f"✅ Total de questões atualizadas: {questoes_atualizadas}")

def adicionar_areas_oficiais_ao_modelo():
    """Adiciona campos para áreas oficiais do ENEM ao modelo"""
    app = create_app()
    
    with app.app_context():
        print("🔧 Adicionando campos para áreas oficiais...")
        
        try:
            # Adicionar coluna area_oficial se não existir
            db.session.execute(text("""
                ALTER TABLE questoes_base 
                ADD COLUMN IF NOT EXISTS area_oficial VARCHAR(100);
            """))
            
            db.session.execute(text("""
                ALTER TABLE questoes_base 
                ADD COLUMN IF NOT EXISTS codigo_area VARCHAR(2);
            """))
            
            db.session.commit()
            print("✅ Colunas adicionadas com sucesso")
            
        except Exception as e:
            print(f"ℹ️ Colunas já existem ou erro: {e}")
            db.session.rollback()

def mapear_questoes_para_areas_oficiais():
    """Mapeia questões existentes para áreas oficiais do ENEM"""
    app = create_app()
    
    with app.app_context():
        print("🗺️ Mapeando questões para áreas oficiais do ENEM...")
        
        # Mapeamento completo
        mapeamento_completo = {
            # Ciências Humanas e suas Tecnologias
            'História': ('Ciências Humanas e suas Tecnologias', 'CH'),
            'Geografia': ('Ciências Humanas e suas Tecnologias', 'CH'),
            'Filosofia': ('Ciências Humanas e suas Tecnologias', 'CH'),
            'Sociologia': ('Ciências Humanas e suas Tecnologias', 'CH'),
            
            # Ciências da Natureza e suas Tecnologias
            'Biologia': ('Ciências da Natureza e suas Tecnologias', 'CN'),
            'Física': ('Ciências da Natureza e suas Tecnologias', 'CN'),
            'Química': ('Ciências da Natureza e suas Tecnologias', 'CN'),
            
            # Linguagens, Códigos e suas Tecnologias
            'Português': ('Linguagens, Códigos e suas Tecnologias', 'LC'),
            'Literatura': ('Linguagens, Códigos e suas Tecnologias', 'LC'),
            'Inglês': ('Linguagens, Códigos e suas Tecnologias', 'LC'),
            'Espanhol': ('Linguagens, Códigos e suas Tecnologias', 'LC'),
            'Artes': ('Linguagens, Códigos e suas Tecnologias', 'LC'),
            'Educação Física': ('Linguagens, Códigos e suas Tecnologias', 'LC'),
            
            # Matemática e suas Tecnologias
            'Matemática': ('Matemática e suas Tecnologias', 'MT')
        }
        
        questoes_mapeadas = 0
        
        for materia, (area_oficial, codigo) in mapeamento_completo.items():
            questoes = QuestaoBase.query.filter_by(materia=materia).all()
            
            for questao in questoes:
                questao.area_oficial = area_oficial
                questao.codigo_area = codigo
                questoes_mapeadas += 1
            
            if questoes:
                print(f"📚 {materia}: {len(questoes)} questões → {area_oficial} ({codigo})")
        
        db.session.commit()
        print(f"✅ {questoes_mapeadas} questões mapeadas para áreas oficiais")

def criar_funcoes_auxiliares():
    """Cria funções SQL auxiliares para consultas"""
    app = create_app()
    
    with app.app_context():
        print("⚙️ Criando funções auxiliares...")
        
        try:
            # Função para obter questões por área oficial
            db.session.execute(text("""
                CREATE OR REPLACE FUNCTION obter_questoes_area_oficial(
                    codigo_area_param VARCHAR(2),
                    quantidade_param INTEGER DEFAULT 45
                ) RETURNS TABLE (
                    id INTEGER,
                    texto TEXT,
                    materia VARCHAR(50),
                    topico VARCHAR(100),
                    dificuldade FLOAT
                ) AS $$
                BEGIN
                    RETURN QUERY
                    SELECT q.id, q.texto, q.materia, q.topico, q.dificuldade
                    FROM questoes_base q
                    WHERE q.codigo_area = codigo_area_param
                      AND q.ativa = true
                    ORDER BY RANDOM()
                    LIMIT quantidade_param;
                END;
                $$ LANGUAGE plpgsql;
            """))
            
            # Função para estatísticas por área
            db.session.execute(text("""
                CREATE OR REPLACE FUNCTION estatisticas_area_oficial(
                    codigo_area_param VARCHAR(2)
                ) RETURNS TABLE (
                    codigo_area VARCHAR(2),
                    area_oficial VARCHAR(100),
                    total_questoes BIGINT,
                    questoes_ativas BIGINT,
                    dificuldade_media FLOAT
                ) AS $$
                BEGIN
                    RETURN QUERY
                    SELECT 
                        q.codigo_area,
                        q.area_oficial,
                        COUNT(*) as total_questoes,
                        COUNT(*) FILTER (WHERE q.ativa = true) as questoes_ativas,
                        AVG(q.dificuldade) as dificuldade_media
                    FROM questoes_base q
                    WHERE q.codigo_area = codigo_area_param
                    GROUP BY q.codigo_area, q.area_oficial;
                END;
                $$ LANGUAGE plpgsql;
            """))
            
            db.session.commit()
            print("✅ Funções auxiliares criadas")
            
        except Exception as e:
            print(f"ℹ️ Erro ao criar funções: {e}")
            db.session.rollback()

def atualizar_interface_dashboard():
    """Cria script para atualizar dashboard com áreas oficiais"""
    script_dashboard = '''
# app/routes/dashboard.py - Adicionar estas funções

from app.models.questao import QuestaoBase
from sqlalchemy import func

def obter_estatisticas_areas_oficiais(user_id):
    """Obtém estatísticas por área oficial do ENEM"""
    
    areas_oficiais = {
        'CH': 'Ciências Humanas',
        'CN': 'Ciências da Natureza', 
        'LC': 'Linguagens e Códigos',
        'MT': 'Matemática'
    }
    
    estatisticas = {}
    
    for codigo, nome in areas_oficiais.items():
        # Questões respondidas pelo usuário nesta área
        questoes_respondidas = db.session.query(
            func.count(Questao.id).label('total'),
            func.sum(
                db.case(
                    (Questao.resposta_usuario == Questao.resposta_correta, 1),
                    else_=0
                )
            ).label('acertos')
        ).join(Simulado).filter(
            Simulado.user_id == user_id,
            Simulado.status == 'Concluído',
            Questao.area == codigo
        ).first()
        
        total = questoes_respondidas.total or 0
        acertos = questoes_respondidas.acertos or 0
        percentual = (acertos / total * 100) if total > 0 else 0
        
        estatisticas[codigo] = {
            'nome': nome,
            'total': total,
            'acertos': acertos,
            'percentual': round(percentual, 1)
        }
    
    return estatisticas

def obter_topicos_fracos_por_area(user_id, codigo_area, limite=5):
    """Obtém tópicos com pior desempenho em uma área"""
    
    topicos = db.session.query(
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
        QuestaoBase.codigo_area == codigo_area
    ).group_by(
        QuestaoBase.topico
    ).having(
        func.count(Questao.id) >= 3  # Pelo menos 3 questões
    ).all()
    
    # Calcular percentuais e ordenar
    topicos_com_percentual = []
    for topico, total, acertos in topicos:
        percentual = (acertos / total * 100) if total > 0 else 0
        topicos_com_percentual.append({
            'topico': topico,
            'total': total,
            'acertos': acertos,
            'percentual': round(percentual, 1)
        })
    
    # Ordenar por percentual (menor primeiro)
    topicos_com_percentual.sort(key=lambda x: x['percentual'])
    
    return topicos_com_percentual[:limite]
'''
    
    with open('scripts/atualizar_dashboard.py', 'w', encoding='utf-8') as f:
        f.write(script_dashboard)
    
    print("📊 Script de atualização do dashboard criado: scripts/atualizar_dashboard.py")

def gerar_relatorio_migracao():
    """Gera relatório final da migração"""
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*60)
        print("📊 RELATÓRIO FINAL DA MIGRAÇÃO")
        print("="*60)
        
        # Questões por área oficial
        areas = db.session.query(
            QuestaoBase.codigo_area,
            QuestaoBase.area_oficial,
            func.count(QuestaoBase.id).label('total')
        ).filter(
            QuestaoBase.ativa == True
        ).group_by(
            QuestaoBase.codigo_area,
            QuestaoBase.area_oficial
        ).all()
        
        total_questoes = 0
        
        for codigo, area_oficial, total in areas:
            print(f"\n🎯 {area_oficial} ({codigo})")
            print(f"   📚 Total: {total} questões")
            
            # Questões por disciplina nesta área
            disciplinas = db.session.query(
                QuestaoBase.materia,
                func.count(QuestaoBase.id).label('count')
            ).filter(
                QuestaoBase.codigo_area == codigo,
                QuestaoBase.ativa == True
            ).group_by(QuestaoBase.materia).all()
            
            for disciplina, count in disciplinas:
                print(f"      - {disciplina}: {count}")
            
            total_questoes += total
            
            # Verificar se tem questões suficientes para ENEM
            if total >= 45:
                print(f"   ✅ Suficiente para ENEM ({total - 45} extras)")
            else:
                print(f"   ⚠️ Insuficiente para ENEM ({45 - total} faltando)")
        
        print(f"\n🎯 RESUMO GERAL:")
        print(f"   📊 Total de questões ativas: {total_questoes}")
        print(f"   🎓 Questões necessárias ENEM: 180")
        
        if total_questoes >= 180:
            print(f"   ✅ Sistema pronto para ENEM completo!")
            simulados_possiveis = total_questoes // 180
            print(f"   🔢 Simulados ENEM possíveis: ~{simulados_possiveis}")
        else:
            print(f"   ⚠️ Precisa de mais {180 - total_questoes} questões")
        
        # Simulados existentes
        simulados_count = Simulado.query.count()
        print(f"   📝 Simulados no sistema: {simulados_count}")

def main():
    print("🚀 ATUALIZAÇÃO DO SISTEMA PARA ÁREAS OFICIAIS DO ENEM")
    print("="*60)
    
    print("\n1️⃣ Adicionando campos ao banco de dados...")
    adicionar_areas_oficiais_ao_modelo()
    
    print("\n2️⃣ Mapeando questões para áreas oficiais...")
    mapear_questoes_para_areas_oficiais()
    
    print("\n3️⃣ Atualizando questões de simulados existentes...")
    atualizar_areas_questoes_existentes()
    
    print("\n4️⃣ Criando funções auxiliares...")
    criar_funcoes_auxiliares()
    
    print("\n5️⃣ Gerando scripts de atualização...")
    atualizar_interface_dashboard()
    
    print("\n6️⃣ Gerando relatório final...")
    gerar_relatorio_migracao()
    
    print("\n" + "="*60)
    print("✅ ATUALIZAÇÃO CONCLUÍDA!")
    print("="*60)
    
    print("""
🎯 PRÓXIMOS PASSOS:

1. Testar novo gerador:
   python scripts/gerador_enem_oficial.py relatorio

2. Gerar simulado com áreas oficiais:
   python scripts/gerador_enem_oficial.py gerar USER_ID --estrategia equilibrada

3. Verificar questões:
   python scripts/admin_questoes.py stats

4. Atualizar dashboard (opcional):
   # Usar código em scripts/atualizar_dashboard.py

📊 ÁREAS OFICIAIS IMPLEMENTADAS:
   ✅ CH - Ciências Humanas e suas Tecnologias
   ✅ CN - Ciências da Natureza e suas Tecnologias  
   ✅ LC - Linguagens, Códigos e suas Tecnologias
   ✅ MT - Matemática e suas Tecnologias

🎓 ESTRATÉGIAS DISPONÍVEIS:
   ✅ Aleatória - Seleção completamente aleatória
   ✅ Equilibrada - Distribuição balanceada por disciplinas
   ✅ Dificuldade - Progressão fácil → médio → difícil
   ✅ Personalizada - Baseada no histórico do usuário

🔧 SISTEMA ATUALIZADO:
   ✅ Compatível com nomenclatura oficial ENEM
   ✅ Múltiplas estratégias de seleção
   ✅ Relatórios detalhados
   ✅ Backwards compatible
""")

if __name__ == "__main__":
    main()