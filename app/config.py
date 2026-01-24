# config.py - Configuração melhorada para resolver problemas de SSL

import os
from urllib.parse import quote_plus

class Config:
    """Configuração base da aplicação"""
    
    # Chave secreta
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sua-chave-secreta-super-segura'
    # Configurações do banco PostgreSQL com tratamento SSL
    DB_HOST = '34.63.141.69'
    DB_PORT = '5432'
    DB_NAME = 'plataforma'
    DB_USER = 'postgres'
    DB_PASSWORD = '22092021Dd$'
    
    # URL do banco com configurações SSL otimizadas
    SQLALCHEMY_DATABASE_URI = (
        f'postgresql://{DB_USER}:{quote_plus(DB_PASSWORD)}'
        f'@{DB_HOST}:{DB_PORT}/{DB_NAME}'
        f'?sslmode=prefer'  # Preferir SSL mas aceitar sem SSL
        f'&connect_timeout=10'  # Timeout de conexão
        f'&application_name=launcher_app'  # Nome da aplicação
    )
    
    # Configurações SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,                    # Tamanho do pool de conexões
        'pool_timeout': 20,                # Timeout para obter conexão do pool
        'pool_recycle': 3600,              # Reciclar conexões após 1h
        'pool_pre_ping': True,             # Verificar conexões antes de usar
        'max_overflow': 10,                # Conexões extras além do pool_size
        'connect_args': {
            'sslmode': 'prefer',           # SSL preferencial
            'connect_timeout': 10,         # Timeout de conexão
            'options': '-c statement_timeout=30000'  # Timeout de query (30s)
        }
    }
    
    # Logging
    LOGGING_LEVEL = 'INFO'
    
    # Flask-Login
    REMEMBER_COOKIE_DURATION = 86400 * 7  # 7 dias

class DevelopmentConfig(Config):
    """Configuração para desenvolvimento"""
    DEBUG = True
    SQLALCHEMY_ECHO = False  # Não mostrar queries SQL por padrão

class ProductionConfig(Config):
    """Configuração para produção"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    # SSL mais rigoroso em produção
    SQLALCHEMY_DATABASE_URI = (
        f'postgresql://{Config.DB_USER}:{quote_plus(Config.DB_PASSWORD)}'
        f'@{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}'
        f'?sslmode=require'  # Exigir SSL em produção
        f'&connect_timeout=10'
        f'&application_name=launcher_app_prod'
    )

class TestingConfig(Config):
    """Configuração para testes"""
    TESTING = True
    WTF_CSRF_ENABLED = False

# Configuração padrão
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
