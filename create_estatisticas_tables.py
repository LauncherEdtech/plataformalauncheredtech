"""
Script para criar as tabelas de estatísticas no banco de dados.
Use este script primeiro, antes de tentar migrar dados existentes.
"""

from app import create_app, db
from app.models.estatisticas import TempoEstudo, Exercicio, ExercicioRealizado, XpGanho

def criar_tabelas_estatisticas():
    """
    Cria as tabelas necessárias para o sistema de estatísticas.
    """
    print("[+] Criando tabelas para estatísticas...")
    
    app = create_app()
    with app.app_context():
        # Verifica se as tabelas já existem
        inspector = db.inspect(db.engine)
        tabelas_existentes = inspector.get_table_names()
        
        tabelas_a_criar = []
        
        if 'tempo_estudo' not in tabelas_existentes:
            tabelas_a_criar.append('tempo_estudo')
        
        if 'exercicio' not in tabelas_existentes:
            tabelas_a_criar.append('exercicio')
        
        if 'exercicio_realizado' not in tabelas_existentes:
            tabelas_a_criar.append('exercicio_realizado')
        
        if 'xp_ganho' not in tabelas_existentes:
            tabelas_a_criar.append('xp_ganho')
        
        if not tabelas_a_criar:
            print("[+] Todas as tabelas de estatísticas já existem. Nada a fazer.")
            return
        
        # Criar tabelas
        print(f"[+] Criando as seguintes tabelas: {', '.join(tabelas_a_criar)}")
        
        # Criar as tabelas sem usar create_all (que pode afetar outras tabelas)
        for table in [TempoEstudo.__table__, Exercicio.__table__, 
                     ExercicioRealizado.__table__, XpGanho.__table__]:
            if table.name in tabelas_a_criar:
                table.create(db.engine, checkfirst=True)
        
        print("[+] Tabelas criadas com sucesso!")
        
        # Listar as tabelas criadas
        inspector = db.inspect(db.engine)
        tabelas_atuais = inspector.get_table_names()
        print("[+] Tabelas disponíveis no banco de dados:")
        for tabela in tabelas_atuais:
            print(f"    - {tabela}")

if __name__ == "__main__":
    criar_tabelas_estatisticas()