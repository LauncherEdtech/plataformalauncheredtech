
# Dados de exemplo para o sistema de estudos
from app.models.estudo import Materia, Modulo, Aula
from app.models.notificacao import inicializar_conquistas
from app import db

def criar_dados_exemplo():
    """Cria dados de exemplo para teste"""
    
    # Matérias
    materias = [
        {
            'nome': 'Matemática',
            'descricao': 'Matemática e suas tecnologias para o ENEM',
            'icone': '🔢',
            'cor': '#FF6B6B',
            'ordem': 1
        },
        {
            'nome': 'Português',
            'descricao': 'Linguagens, códigos e suas tecnologias',
            'icone': '📚',
            'cor': '#4ECDC4',
            'ordem': 2
        },
        {
            'nome': 'História',
            'descricao': 'Ciências humanas e suas tecnologias',
            'icone': '🏛️',
            'cor': '#45B7D1',
            'ordem': 3
        }
    ]
    
    for mat_data in materias:
        if not Materia.query.filter_by(nome=mat_data['nome']).first():
            materia = Materia(**mat_data)
            db.session.add(materia)
    
    db.session.commit()
    
    # Módulos para Matemática
    matematica = Materia.query.filter_by(nome='Matemática').first()
    if matematica and not matematica.modulos.first():
        modulos_mat = [
            {
                'titulo': 'Funções',
                'descricao': 'Estudo completo de funções matemáticas',
                'materia_id': matematica.id,
                'ordem': 1,
                'duracao_estimada': 120,
                'dificuldade': 'medio'
            },
            {
                'titulo': 'Geometria',
                'descricao': 'Geometria plana e espacial',
                'materia_id': matematica.id,
                'ordem': 2,
                'duracao_estimada': 90,
                'dificuldade': 'dificil'
            }
        ]
        
        for mod_data in modulos_mat:
            modulo = Modulo(**mod_data)
            db.session.add(modulo)
    
    db.session.commit()
    
    # Inicializar conquistas
    inicializar_conquistas()
    
    print("✅ Dados de exemplo criados!")

if __name__ == '__main__':
    criar_dados_exemplo()
