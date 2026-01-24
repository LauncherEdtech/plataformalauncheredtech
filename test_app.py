from app import create_app, db
from app.models.user import User
import os

def test_config():
    """Teste de configuração básica da aplicação"""
    app = create_app()
    with app.app_context():
        # Verifica se consegue se conectar ao banco de dados
        try:
            db.session.execute("SELECT 1")
            print("✅ Conexão com o banco de dados bem-sucedida!")
        except Exception as e:
            print(f"❌ Erro ao conectar ao banco de dados: {e}")
            return False
        
        # Verifica se os modelos estão corretamente registrados
        try:
            user = User(username="teste", email="teste@example.com")
            user.set_password("senha123")
            db.session.add(user)
            db.session.commit()
            db.session.delete(user)
            db.session.commit()
            print("✅ Modelos registrados e funcionando corretamente!")
        except Exception as e:
            print(f"❌ Erro ao testar modelos: {e}")
            return False
        
        return True

if __name__ == "__main__":
    print("🔍 Testando configuração da aplicação...")
    success = test_config()
    if success:
        print("✨ Configuração básica da aplicação está funcionando corretamente!")
        print("🚀 Você pode iniciar a aplicação com 'flask run'")
    else:
        print("❌ Há problemas na configuração da aplicação. Verifique os erros acima.")