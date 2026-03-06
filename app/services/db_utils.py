# app/services/db_utils.py
"""
Utilitário central para conexões psycopg2 diretas.
Lê credenciais EXCLUSIVAMENTE do DATABASE_URL no .env
Nunca use credenciais hardcoded - use este módulo.
"""

import os
import psycopg2
from urllib.parse import urlparse


def get_db_params() -> dict:
    """
    Retorna os parâmetros de conexão psycopg2 lendo do DATABASE_URL.
    Falha explicitamente se a variável não estiver definida.
    """
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise EnvironmentError(
            "❌ DATABASE_URL não está definida no ambiente. "
            "Verifique o arquivo .env na raiz do projeto."
        )

    parsed = urlparse(database_url)

    return {
        "host":     parsed.hostname,
        "port":     parsed.port or 5432,
        "dbname":   parsed.path.lstrip("/"),
        "user":     parsed.username,
        "password": parsed.password,
    }


def get_connection():
    """
    Retorna uma conexão psycopg2 pronta para uso.

    Uso:
        from app.services.db_utils import get_connection

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ...")
        conn.close()
    """
    return psycopg2.connect(**get_db_params())
