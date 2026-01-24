# create_tables.py - Coloque este arquivo na raiz do projeto

from app import create_app, db
from app.models.helpzone import Badge, Duvida, Resposta, DuvidaVoto, RespostaVoto, Notificacao, UserBadge
from app.models.user import User

app = create_app()

with app.app_context():
    print("[+] Verificando e criando tabelas do banco de dados...")
    # Isso criará todas as tabelas definidas nos modelos
    db.create_all()
    print("[+] Tabelas criadas com sucesso!")
    
    # Lista as tabelas criadas
    engine = db.engine
    inspector = db.inspect(engine)
    tabelas = inspector.get_table_names()
    print("[+] Tabelas disponíveis no banco de dados:")
    for tabela in tabelas:
        print(f"    - {tabela}")
    
    print("\n[+] IMPORTANTE: Se as tabelas esperadas não aparecerem na lista acima,")
    print("[+] verifique se os modelos estão corretamente definidos e importados.")