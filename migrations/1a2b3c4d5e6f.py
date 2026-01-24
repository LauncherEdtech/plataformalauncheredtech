"""Adição de novos campos ao modelo Simulado

Revision ID: 1a2b3c4d5e6f
Revises: previous_revision_id
Create Date: 2025-05-04 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a2b3c4d5e6f'
down_revision = 'previous_revision_id'  # Substitua pelo ID da revisão anterior
branch_labels = None
depends_on = None


def upgrade():
    # Adicionar novos campos ao modelo Simulado
    op.add_column('simulado', sa.Column('tempo_medio_por_questao', sa.Float(), nullable=True))
    op.add_column('simulado', sa.Column('questoes_puladas', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('simulado', sa.Column('acertos_total', sa.Integer(), nullable=True, server_default='0'))
    
    # Adicionar novo campo ao modelo Questao
    op.add_column('questao', sa.Column('tempo_resposta', sa.Integer(), nullable=True))


def downgrade():
    # Remover os campos adicionados em caso de rollback
    op.drop_column('simulado', 'tempo_medio_por_questao')
    op.drop_column('simulado', 'questoes_puladas')
    op.drop_column('simulado', 'acertos_total')
    op.drop_column('questao', 'tempo_resposta')