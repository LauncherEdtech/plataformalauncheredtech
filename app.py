#!/usr/bin/env python3
# app.py - Arquivo principal para Gunicorn

import os
import sys

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar e criar a aplicação
from app import create_app

# Criar a aplicação Flask
app = create_app()

if __name__ == '__main__':
    # Executar em modo desenvolvimento
    app.run(host='0.0.0.0', port=8000, debug=True)
