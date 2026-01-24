"""
Migration script para atualizar o modelo de Redação com os novos campos de pontos fortes e fracos
"""

from alembic import op
import sqlalchemy as sa


# Função de upgrade: adiciona novos campos ao modelo Redacao
def upgrade():
    # Renomear coluna feedback para parecer_geral se ela existir
    try:
        op.alter_column('redacao', 'feedback', new_column_name='parecer_geral')
    except:
        # Se não existir ou já estiver renomeada, adicionar a coluna
        try:
            op.add_column('redacao', sa.Column('parecer_geral', sa.Text(), nullable=True))
        except:
            pass  # Coluna já existe
    
    # Verificar e adicionar as colunas de competências se ainda não existirem
    try:
        op.add_column('redacao', sa.Column('competencia1', sa.Integer(), nullable=True))
        op.add_column('redacao', sa.Column('competencia2', sa.Integer(), nullable=True))
        op.add_column('redacao', sa.Column('competencia3', sa.Integer(), nullable=True))
        op.add_column('redacao', sa.Column('competencia4', sa.Integer(), nullable=True))
        op.add_column('redacao', sa.Column('competencia5', sa.Integer(), nullable=True))
    except:
        pass  # Colunas já existem
    
    # Adicionar campos de feedback detalhado por competência
    try:
        op.add_column('redacao', sa.Column('feedback_comp1', sa.Text(), nullable=True))
        op.add_column('redacao', sa.Column('feedback_comp2', sa.Text(), nullable=True))
        op.add_column('redacao', sa.Column('feedback_comp3', sa.Text(), nullable=True))
        op.add_column('redacao', sa.Column('feedback_comp4', sa.Text(), nullable=True))
        op.add_column('redacao', sa.Column('feedback_comp5', sa.Text(), nullable=True))
    except:
        pass  # Colunas já existem
    
    # Adicionar novos campos de pontos fortes e fracos
    # Pontos fortes
    op.add_column('redacao', sa.Column('pontos_fortes_comp1', sa.Text(), nullable=True))
    op.add_column('redacao', sa.Column('pontos_fortes_comp2', sa.Text(), nullable=True))
    op.add_column('redacao', sa.Column('pontos_fortes_comp3', sa.Text(), nullable=True))
    op.add_column('redacao', sa.Column('pontos_fortes_comp4', sa.Text(), nullable=True))
    op.add_column('redacao', sa.Column('pontos_fortes_comp5', sa.Text(), nullable=True))
    
    # Pontos fracos
    op.add_column('redacao', sa.Column('pontos_fracos_comp1', sa.Text(), nullable=True))
    op.add_column('redacao', sa.Column('pontos_fracos_comp2', sa.Text(), nullable=True))
    op.add_column('redacao', sa.Column('pontos_fracos_comp3', sa.Text(), nullable=True))
    op.add_column('redacao', sa.Column('pontos_fracos_comp4', sa.Text(), nullable=True))
    op.add_column('redacao', sa.Column('pontos_fracos_comp5', sa.Text(), nullable=True))
    
    # Sugestões
    op.add_column('redacao', sa.Column('sugestoes_comp1', sa.Text(), nullable=True))
    op.add_column('redacao', sa.Column('sugestoes_comp2', sa.Text(), nullable=True))
    op.add_column('redacao', sa.Column('sugestoes_comp3', sa.Text(), nullable=True))
    op.add_column('redacao', sa.Column('sugestoes_comp4', sa.Text(), nullable=True))
    op.add_column('redacao', sa.Column('sugestoes_comp5', sa.Text(), nullable=True))
    
    # Campos adicionais para processamento
    try:
        op.add_column('redacao', sa.Column('tema', sa.String(255), nullable=True))
        op.add_column('redacao', sa.Column('prompt_usado', sa.Text(), nullable=True))
        op.add_column('redacao', sa.Column('resposta_api', sa.Text(), nullable=True))
    except:
        pass  # Colunas já existem
    
    # Campos de status e moedas
    try:
        op.add_column('redacao', sa.Column('status', sa.String(50), server_default='Enviada', nullable=False))
        op.add_column('redacao', sa.Column('moedas_concedidas', sa.Boolean(), server_default='false', nullable=False))
    except:
        pass  # Colunas já existem


# Função de downgrade: remove os campos adicionados (caso precise reverter)
def downgrade():
    # Pontos fortes
    op.drop_column('redacao', 'pontos_fortes_comp1')
    op.drop_column('redacao', 'pontos_fortes_comp2')
    op.drop_column('redacao', 'pontos_fortes_comp3')
    op.drop_column('redacao', 'pontos_fortes_comp4')
    op.drop_column('redacao', 'pontos_fortes_comp5')
    
    # Pontos fracos
    op.drop_column('redacao', 'pontos_fracos_comp1')
    op.drop_column('redacao', 'pontos_fracos_comp2')
    op.drop_column('redacao', 'pontos_fracos_comp3')
    op.drop_column('redacao', 'pontos_fracos_comp4')
    op.drop_column('redacao', 'pontos_fracos_comp5')
    
    # Sugestões
    op.drop_column('redacao', 'sugestoes_comp1')
    op.drop_column('redacao', 'sugestoes_comp2')
    op.drop_column('redacao', 'sugestoes_comp3')
    op.drop_column('redacao', 'sugestoes_comp4')
    op.drop_column('redacao', 'sugestoes_comp5')
    
    # A reversão dos outros campos pode ser implementada caso necessário
    # Não implementado aqui para evitar a perda de dados