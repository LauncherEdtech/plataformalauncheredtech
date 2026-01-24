import logging
from logging.handlers import RotatingFileHandler
import os
from app import create_app

# Criação da aplicação Flask
app = create_app()

# ==============================
# CONFIGURAÇÃO DE LOGS PARA PRODUÇÃO
# ==============================

# Cria diretório de logs se não existir
if not os.path.exists('logs'):
    os.mkdir('logs')

# Handler para arquivo com rotação
file_handler = RotatingFileHandler('logs/flask_app.log', 
                                 maxBytes=10240000, backupCount=10)
file_handler.setLevel(logging.INFO)  # INFO em produção, não DEBUG

# Handler para erros críticos
error_handler = RotatingFileHandler('logs/flask_errors.log',
                                  maxBytes=10240000, backupCount=5)
error_handler.setLevel(logging.ERROR)

# Formato dos logs
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
error_handler.setFormatter(formatter)

# Adiciona handlers à aplicação Flask
app.logger.addHandler(file_handler)
app.logger.addHandler(error_handler)
app.logger.setLevel(logging.INFO)

# Logs do Werkzeug (mais restritivos em produção)
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.WARNING)
werkzeug_logger.addHandler(file_handler)

# Tratamento de exceções não capturadas
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.exception("Erro não tratado detectado:")
    return "Erro interno no servidor.", 500

# Log inicial
app.logger.info("🚀 Aplicação Flask iniciada em modo PRODUÇÃO")

if __name__ == '__main__':
    # Configuração para produção
    app.logger.info("Servidor Flask sendo iniciado na porta 8080...")
    app.run(debug=False, host='127.0.0.1', port=8080)  # debug=False para produção
