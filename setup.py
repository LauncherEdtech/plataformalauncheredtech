# setup.py
import os
import sys
from flask.cli import FlaskGroup
from app import create_app, db

app = create_app()
cli = FlaskGroup(create_app=lambda: app)

@cli.command("create_db")
def create_db():
    db.drop_all()
    db.create_all()
    db.session.commit()
    print("Banco de dados criado com sucesso!")

@cli.command("seed_db")
def seed_db():
    # Executar o script de seed
    exec(open("seed.py").read())
    print("Dados iniciais inseridos no banco de dados!")

@cli.command("setup")
def setup():
    """Configura o projeto completo: cria o banco, insere dados iniciais e inicia o servidor"""
    create_db()
    seed_db()
    os.system("flask run")

if __name__ == "__main__":
    cli()