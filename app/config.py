# config.py - Configuração usando DATABASE_URL (AWS/RDS friendly)

import os

class Config:
    """Configuração base da aplicação"""

    # Chave secreta
    SECRET_KEY = os.environ.get("SECRET_KEY") or "sua-chave-secreta-super-segura"

    # ✅ Fonte única de verdade do banco
    # Ex: postgresql://user:senha@host:5432/dbname?sslmode=require
    DATABASE_URL = os.environ.get("DATABASE_URL")

    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL não definido. Configure no /etc/launcher.env (systemd) ou .env (dev)."
        )

    SQLALCHEMY_DATABASE_URI = DATABASE_URL

    # Configurações SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 5,
        "pool_timeout": 20,
        "pool_recycle": 3600,
        "pool_pre_ping": True,
        "max_overflow": 10,
        # ⚠️ Não force sslmode aqui se já estiver no DATABASE_URL
        # Se quiser forçar em produção, ajuste no ProductionConfig abaixo.
        "connect_args": {
            "connect_timeout": 10,
            "options": "-c statement_timeout=30000",
        },
    }

    LOGGING_LEVEL = "INFO"
    REMEMBER_COOKIE_DURATION = 86400 * 7  # 7 dias


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False

    # ✅ Em produção, preferimos SSL obrigatório.
    # Se o seu DATABASE_URL já tiver sslmode=require, ótimo.
    # Se não tiver, a gente injeta aqui de forma segura.
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        url = os.environ.get("DATABASE_URL", "")
        if "sslmode=" in url:
            return url
        sep = "&" if "?" in url else "?"
        return f"{url}{sep}sslmode=require"


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
