# arquivo: add_columns_postgres.py
from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        def add_column_if_not_exists(table, column, definition):
            exists = db.session.execute(text(
                f"SELECT EXISTS (SELECT 1 FROM information_schema.columns "
                f"WHERE table_name='{table}' AND column_name='{column}')"
            )).scalar()

            if not exists:
                print(f"Adicionando coluna '{column}' à tabela '{table}'...")
                db.session.execute(text(
                    f'ALTER TABLE "{table}" ADD COLUMN {column} {definition}'
                ))
                print(f"Coluna '{column}' adicionada com sucesso!")
            else:
                print(f"Coluna '{column}' já existe na tabela '{table}'.")

        # Tabela produto
        add_column_if_not_exists("produto", "categoria", "VARCHAR(50) DEFAULT 'Outros'")
        # Tabela user
        add_column_if_not_exists("user", "is_admin", "BOOLEAN DEFAULT FALSE")
        # Tabela resgate
        add_column_if_not_exists("resgate", "nome_contato", "VARCHAR(100)")
        add_column_if_not_exists("resgate", "email_contato", "VARCHAR(120)")
        add_column_if_not_exists("resgate", "telefone_contato", "VARCHAR(20)")

        # Confirmar alterações
        db.session.commit()
        print("Todas as alterações foram aplicadas com sucesso!")

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao modificar o esquema: {str(e)}")
