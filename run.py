import logging
from app import create_app

# Criação da aplicação Flask
app = create_app()

# ==============================
# CONFIGURAÇÃO DE LOGS DETALHADOS
# ==============================

# Cria um handler para gravar em arquivo
file_handler = logging.FileHandler('flask_detalhado.log')
file_handler.setLevel(logging.DEBUG)

# Define o formato dos logs
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)

# Adiciona o handler à aplicação Flask
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.DEBUG)

# Captura logs de bibliotecas Flask e Werkzeug
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.DEBUG)
werkzeug_logger.addHandler(file_handler)

# Tratamento de exceções não capturadas
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.exception("Erro não tratado detectado:")
    return "Erro interno no servidor.", 500

# Log inicial quando a aplicação começa
app.logger.info("🚀 Iniciando aplicação Flask...")

# ==============================
# INICIALIZAÇÃO DO SERVIDOR
# ==============================
if __name__ == '__main__':
    app.logger.info("Servidor Flask sendo iniciado na porta 8080...")
    app.run(debug=True, host='0.0.0.0', port=8080)
