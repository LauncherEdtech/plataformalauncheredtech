# Servidor
bind = "127.0.0.1:8000"  # Gunicorn local; Nginx faz proxy
workers = 2              # t3.micro (1GB) -> recomendado 2 (se pesar, use 1)
worker_class = "sync"
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100

# Logs (garanta que a pasta logs/ existe)
accesslog = "logs/gunicorn-access.log"
errorlog = "logs/gunicorn-error.log"
capture_output = True
loglevel = "info"

# Processo
daemon = False
pidfile = "gunicorn.pid"
preload_app = False      # em 1GB, preload pode aumentar pico de RAM; deixe False

# Performance
worker_tmp_dir = "/dev/shm"

