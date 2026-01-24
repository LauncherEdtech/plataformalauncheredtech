# migrations/create_questoes_base.py
"""
Migration para criar tabela questoes_base

Para executar:
1. flask db init (se ainda não foi executado)
2. flask db migrate -m "Criar tabela questoes_base"
3. flask db upgrade
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'questoes_base_001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Criar tabela questoes_base
    op.create_table('questoes_base',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('texto', sa.Text(), nullable=False),
        sa.Column('materia', sa.String(length=50), nullable=False),
        sa.Column('topico', sa.String(length=100), nullable=False),
        sa.Column('subtopico', sa.String(length=100), nullable=True),
        sa.Column('opcao_a', sa.Text(), nullable=False),
        sa.Column('opcao_b', sa.Text(), nullable=False),
        sa.Column('opcao_c', sa.Text(), nullable=False),
        sa.Column('opcao_d', sa.Text(), nullable=False),
        sa.Column('opcao_e', sa.Text(), nullable=False),
        sa.Column('resposta_correta', sa.String(length=1), nullable=False),
        sa.Column('explicacao', sa.Text(), nullable=False),
        sa.Column('imagem_url', sa.String(length=255), nullable=True),
        sa.Column('dificuldade', sa.Float(), nullable=True),
        sa.Column('data_criacao', sa.DateTime(), nullable=True),
        sa.Column('ativa', sa.Boolean(), nullable=True),
        sa.Column('vezes_utilizada', sa.Integer(), nullable=True),
        sa.Column('vezes_acertada', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Criar índices para melhor performance
    op.create_index('ix_questoes_base_materia', 'questoes_base', ['materia'])
    op.create_index('ix_questoes_base_topico', 'questoes_base', ['topico'])
    op.create_index('ix_questoes_base_ativa', 'questoes_base', ['ativa'])
    
    # Adicionar coluna questao_base_id na tabela questoes existente (se existir)
    try:
        op.add_column('questoes', sa.Column('questao_base_id', sa.Integer(), nullable=True))
        op.create_foreign_key('fk_questoes_questao_base', 'questoes', 'questoes_base', ['questao_base_id'], ['id'])
    except:
        # Tabela questoes pode não existir ainda
        pass

def downgrade():
    # Remover foreign key e coluna se existir
    try:
        op.drop_constraint('fk_questoes_questao_base', 'questoes', type_='foreignkey')
        op.drop_column('questoes', 'questao_base_id')
    except:
        pass
    
    # Remover índices
    op.drop_index('ix_questoes_base_ativa', table_name='questoes_base')
    op.drop_index('ix_questoes_base_topico', table_name='questoes_base')
    op.drop_index('ix_questoes_base_materia', table_name='questoes_base')
    
    # Remover tabela
    op.drop_table('questoes_base')