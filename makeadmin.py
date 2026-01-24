# arquivo: make_admin.py
from app import create_app, db
from app.models.user import User
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        # Procurar o usuário pelo username ou email
        user = User.query.filter(
            (User.username == 'admin1') | 
            (User.email == 'admin1@gamil.com')
        ).first()
        
        if user:
            # Verificar se o campo is_admin existe
            if hasattr(user, 'is_admin'):
                user.is_admin = True
                db.session.commit()
                print(f"Usuário '{user.username}' (email: {user.email}) promovido a administrador com sucesso!")
            else:
                # Se a coluna existe no banco mas não no modelo, use SQL direto
                db.session.execute(
                    text('UPDATE "user" SET is_admin = TRUE WHERE username = :username OR email = :email'),
                    {"username": "admin1", "email": "admin1@gamil.com"}
                )
                db.session.commit()
                print(f"Usuário 'admin1' promovido a administrador via SQL direto!")
        else:
            print("Usuário não encontrado! Verifique o username e email.")
            
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao promover o usuário: {str(e)}")