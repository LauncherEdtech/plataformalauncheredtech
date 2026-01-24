# Servidor
bind = "127.0.0.1:8000"  # Mantendo sua porta 8080
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100

# Logs
accesslog = "logs/gunicorn-access.log"
errorlog = "logs/gunicorn-error.log"
capture_output = True
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Processo
daemon = False
pidfile = "gunicorn.pid"
preload_app = True

# Performance
worker_tmp_dir = "/dev/shm"

# Segurança
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190
