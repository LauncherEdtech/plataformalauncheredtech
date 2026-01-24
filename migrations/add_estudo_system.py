# migrations/versions/add_estudo_system.py
"""Add study system tables and user total_moedas field

Revision ID: add_estudo_system
Revises: [previous_revision]
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers
revision = 'add_estudo_system'
down_revision = None  # Replace with your last migration
branch_labels = None
depends_on = None

def upgrade():
    # Add total_moedas field to User table
    op.add_column('user', sa.Column('total_moedas', sa.Integer(), default=0))
    
    # Create Materia table
    op.create_table('materia',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=100), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('icone', sa.String(length=50), nullable=True),
        sa.Column('cor', sa.String(length=7), nullable=True),
        sa.Column('ordem', sa.Integer(), default=0),
        sa.Column('ativa', sa.Boolean(), default=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create Modulo table
    op.create_table('modulo',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('titulo', sa.String(length=200), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('materia_id', sa.Integer(), nullable=False),
        sa.Column('ordem', sa.Integer(), default=0),
        sa.Column('duracao_estimada', sa.Integer(), nullable=True),
        sa.Column('dificuldade', sa.String(length=20), nullable=True),
        sa.Column('ativo', sa.Boolean(), default=True),
        sa.ForeignKeyConstraint(['materia_id'], ['materia.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create Aula table
    op.create_table('aula',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('titulo', sa.String(length=200), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('conteudo', sa.Text(), nullable=True),
        sa.Column('modulo_id', sa.Integer(), nullable=False),
        sa.Column('ordem', sa.Integer(), default=0),
        sa.Column('duracao_estimada', sa.Integer(), nullable=True),
        sa.Column('tipo', sa.String(length=20), default='texto'),
        sa.Column('url_video', sa.String(length=500), nullable=True),
        sa.Column('ativa', sa.Boolean(), default=True),
        sa.ForeignKeyConstraint(['modulo_id'], ['modulo.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create MaterialAula table
    op.create_table('material_aula',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=200), nullable=False),
        sa.Column('arquivo', sa.String(length=500), nullable=False),
        sa.Column('tipo', sa.String(length=10), nullable=True),
        sa.Column('tamanho', sa.Integer(), nullable=True),
        sa.Column('aula_id', sa.Integer(), nullable=False),
        sa.Column('data_upload', sa.DateTime(), default=datetime.utcnow),
        sa.ForeignKeyConstraint(['aula_id'], ['aula.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create ProgressoAula table
    op.create_table('progresso_aula',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('aula_id', sa.Integer(), nullable=False),
        sa.Column('tempo_assistido', sa.Integer(), default=0),
        sa.Column('concluida', sa.Boolean(), default=False),
        sa.Column('data_inicio', sa.DateTime(), default=datetime.utcnow),
        sa.Column('data_conclusao', sa.DateTime(), nullable=True),
        sa.Column('ultima_atividade', sa.DateTime(), default=datetime.utcnow),
        sa.ForeignKeyConstraint(['aula_id'], ['aula.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'aula_id')
    )
    
    # Create SessaoEstudo table
    op.create_table('sessao_estudo',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('aula_id', sa.Integer(), nullable=False),
        sa.Column('inicio', sa.DateTime(), default=datetime.utcnow),
        sa.Column('fim', sa.DateTime(), nullable=True),
        sa.Column('tempo_ativo', sa.Integer(), default=0),
        sa.Column('moedas_ganhas', sa.Integer(), default=0),
        sa.Column('ativa', sa.Boolean(), default=True),
        sa.ForeignKeyConstraint(['aula_id'], ['aula.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create Moeda table
    op.create_table('moeda',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('quantidade', sa.Integer(), nullable=False),
        sa.Column('tipo', sa.String(length=50), nullable=True),
        sa.Column('descricao', sa.String(length=200), nullable=True),
        sa.Column('data', sa.DateTime(), default=datetime.utcnow),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better performance
    op.create_index('idx_materia_ordem', 'materia', ['ordem'])
    op.create_index('idx_materia_ativa', 'materia', ['ativa'])
    op.create_index('idx_modulo_materia_ordem', 'modulo', ['materia_id', 'ordem'])
    op.create_index('idx_aula_modulo_ordem', 'aula', ['modulo_id', 'ordem'])
    op.create_index('idx_progresso_user_aula', 'progresso_aula', ['user_id', 'aula_id'])
    op.create_index('idx_progresso_concluida', 'progresso_aula', ['concluida'])
    op.create_index('idx_sessao_user_data', 'sessao_estudo', ['user_id', 'inicio'])
    op.create_index('idx_moeda_user_data', 'moeda', ['user_id', 'data'])


def downgrade():
    # Drop tables in reverse order (due to foreign keys)
    op.drop_table('moeda')
    op.drop_table('sessao_estudo')
    op.drop_table('progresso_aula')
    op.drop_table('material_aula')
    op.drop_table('aula')
    op.drop_table('modulo')
    op.drop_table('materia')
    
    # Remove total_moedas field from User table
    op.drop_column('user', 'total_moedas')

# Script para popular dados iniciais (opcional)
def create_sample_data():
    """
    Função para criar dados de exemplo.
    Execute após a migração se desejar dados de teste.
    """
    from app.models.estudo import Materia, Modulo, Aula
    from app import db
    
    # Criar matérias de exemplo
    materias_exemplo = [
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
        },
        {
            'nome': 'Química',
            'descricao': 'Ciências da natureza e suas tecnologias',
            'icone': '🧪',
            'cor': '#96CEB4',
            'ordem': 4
        }
    ]
    
    for materia_data in materias_exemplo:
        materia = Materia(**materia_data)
        db.session.add(materia)
    
    db.session.commit()
    
    # Criar módulos de exemplo para Matemática
    matematica = Materia.query.filter_by(nome='Matemática').first()
    if matematica:
        modulos_matematica = [
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
        
        for modulo_data in modulos_matematica:
            modulo = Modulo(**modulo_data)
            db.session.add(modulo)
    
    db.session.commit()
    
    print("✅ Dados de exemplo criados com sucesso!")

if __name__ == '__main__':
    # Para executar apenas a criação de dados de exemplo
    create_sample_data()