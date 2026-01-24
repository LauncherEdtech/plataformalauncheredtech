import os
import logging
from logging.handlers import RotatingFileHandler
from app import create_app

# Criar aplicação
app = create_app()

# Configurar logs para produção
if not app.debug:
    # Criar diretório de logs se não existir
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # Handler para logs gerais
    file_handler = RotatingFileHandler('logs/flask_app.log', 
                                     maxBytes=10240000, backupCount=10)
    file_handler.setLevel(logging.INFO)
    
    # Handler para erros
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
    
    # Adicionar handlers
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    app.logger.setLevel(logging.INFO)
    
    # Configurar logs do Werkzeug
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.WARNING)
    werkzeug_logger.addHandler(file_handler)
    
    # Log inicial
    app.logger.info("🚀 Aplicação Flask iniciada via Gunicorn")

# Handler para exceções não tratadas
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.exception("Erro não tratado detectado:")
    return "Erro interno no servidor.", 500

if __name__ == "__main__":
    app.run()
