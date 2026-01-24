"""
Script para resetar o banco de dados: apaga todas as tabelas e recria conforme seus models.
Usage: python reset_db.py
"""

from app import create_app, db


def reset_database():
    # Cria a aplicação e entra no contexto
    app = create_app()
    with app.app_context():
        print("[+] Dropping all tables...")
        db.drop_all()
        print("[+] Creating all tables...")
        db.create_all()
        print("[+] Banco de dados resetado com sucesso!")


if __name__ == "__main__":
    reset_database()