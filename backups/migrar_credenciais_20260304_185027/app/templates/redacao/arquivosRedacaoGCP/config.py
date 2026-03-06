import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'chave-secreta-em-desenvolvimento')
    
    # Exemplo de string de conexão com PostgreSQL local
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:22092021Dd$@34.63.141.69:5432/plataforma'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', 'chave-da-openai')
    KIWIFY_WEBHOOK_SECRET = os.environ.get('KIWIFY_WEBHOOK_SECRET', 'segredo-kiwify')
