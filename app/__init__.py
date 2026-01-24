# app/__init__.py - VERSÃO UNIFICADA (produção + inicialização resiliente + .env)

import logging
import os
from datetime import datetime
from flask import Flask, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from sqlalchemy.exc import OperationalError, DatabaseError
from sqlalchemy import inspect, text

# NOVO: Carregar variáveis de ambiente do .env
try:
   # from dotenv import load_dotenv
    #load_dotenv()
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv())
    print("✅ Arquivo .env carregado com sucesso")
except ImportError:
    print("⚠️ python-dotenv não instalado - usando apenas variáveis de ambiente do sistema")
except Exception as e:
    print(f"⚠️ Erro ao carregar .env: {e}")

# ----------------------- Extensões -----------------------
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'warning'


# ----------------------- Logging -----------------------
def setup_logging(app):
    """Configura logging para produção."""
    if not app.debug and not app.testing:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] - %(name)s - %(message)s",
        )
    # Reduz verbosidade do engine do SQLAlchemy
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


# ----------------------- Error Handlers -----------------------
def register_error_handlers(app):
    """Registra handlers de erro amigáveis e com rollback."""
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Erro interno do servidor: {error}")
        db.session.rollback()
        flash("Ocorreu um erro interno. Nossa equipe foi notificada.", "danger")
        return render_template("errors/500.html"), 500

    @app.errorhandler(OperationalError)
    def handle_db_operational_error(error):
        app.logger.error(f"Erro operacional do banco: {error}")
        db.session.rollback()
        flash("Problema temporário de conexão. Tente novamente em instantes.", "warning")
        return render_template("auth/login.html"), 500

    @app.errorhandler(DatabaseError)
    def handle_db_error(error):
        app.logger.error(f"Erro de banco de dados: {error}")
        db.session.rollback()
        flash("Erro de banco de dados. Tente novamente.", "danger")
        return render_template("auth/login.html"), 500


# ----------------------- App Factory -----------------------
def create_app(config_name=None):
    """Factory principal da aplicação Flask."""
    app = Flask(__name__)

    # Config básica
    if config_name is None:
        config_name = os.environ.get("FLASK_CONFIG", "development")

    # Segredo
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "sua-chave-secreta-super-segura")

    # NOVO: Configurações do .env - OpenAI API
    openai_key = os.environ.get("OPENAI_API_KEY")
    app.config["OPENAI_API_KEY"] = openai_key
    
    # Debug para verificar se a chave foi carregada
    if openai_key:
        print(f"✅ OPENAI_API_KEY carregada: {openai_key[:10]}...")
        app.logger.info(f"OPENAI_API_KEY configurada: {openai_key[:10]}...")
    else:
        print("❌ OPENAI_API_KEY não encontrada no .env")
        app.logger.warning("OPENAI_API_KEY não encontrada no arquivo .env")

    # NOVO: Outras configurações do .env
    app.config['FLASK_ENV'] = os.environ.get('FLASK_ENV', 'production')
    
    # Configurações de email do .env
    app.config['SMTP_SERVER'] = os.environ.get('SMTP_SERVER')
    app.config['SMTP_PORT'] = int(os.environ.get('SMTP_PORT', 587))
    app.config['SMTP_USER'] = os.environ.get('SMTP_USER')
    app.config['SMTP_PASSWORD'] = os.environ.get('SMTP_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

    # Banco: prioriza DATABASE_URL; senão, compõe com ENV (mantém fallback compatível)
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        db_host = os.environ.get("DB_HOST", "34.63.141.69")
        db_port = os.environ.get("DB_PORT", "5432")
        db_name = os.environ.get("DB_NAME", "plataforma")
        db_user = os.environ.get("DB_USER", "postgres")
        db_password = os.environ.get("DB_PASSWORD", "22092021Dd$")
        database_url = (
            f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            f"?sslmode=prefer&connect_timeout=10&application_name=launcher_app"
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_size": 5,
        "pool_timeout": 20,
        "pool_recycle": 3600,
        "pool_pre_ping": True,
        "max_overflow": 10,
        "connect_args": {
            "sslmode": "prefer",
            "connect_timeout": 10,
            "options": "-c statement_timeout=30000",
        },
    }

    # Inicializa extensões
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Logging + handlers
    setup_logging(app)
    register_error_handlers(app)

#---------------------------------------------------
    # ✅ NOVO: Registrar filtros do YouTube para thumbnails
    try:
        from app.utils.youtube_helper import registrar_filtros_youtube
        registrar_filtros_youtube(app)
        app.logger.info("✅ Filtros do YouTube registrados com sucesso")
    except ImportError as e:
        app.logger.warning(f"⚠️ youtube_helper não encontrado: {e}")
        app.logger.warning("⚠️ Thumbnails do YouTube não estarão disponíveis")
    except Exception as e:
        app.logger.error(f"❌ Erro ao registrar filtros do YouTube: {e}")
#-------------------------------------------------



    # Middleware opcional
    try:
        from middleware import init_middleware  # type: ignore
        init_middleware(app)
        app.logger.info("Middleware inicializado.")
    except Exception as e:
        app.logger.warning(f"Middleware não inicializado: {e}")

    # --------- Import ordenado de modelos (resiliente) ----------
    with app.app_context():
        try:
            # 1) Modelos base
            from app.models.user import User  # noqa
            from app.models.simulado import Simulado, Questao, Alternativa  # noqa
            from app.models.dashboard import Estatistica  # noqa

            # 2) Modelos de estudo (opcionais)
            try:
                from app.models.estudo import (  # noqa
                    Materia, Modulo, Aula, MaterialAula,
                    ProgressoAula, SessaoEstudo, Moeda, Cronograma, ItemCronograma
                )
                try:
                    from app.models.user import setup_user_relationships  # type: ignore
                    setup_user_relationships()
                except Exception as e:
                    app.logger.warning(f"setup_user_relationships() não aplicado: {e}")
            except Exception as e:
                app.logger.warning(f"Modelos de estudo não disponíveis: {e}")

            # 3) Modelos opcionais diversos
            try:
                from app.models.helpzone import Pergunta, Resposta, Badge, UserBadge  # noqa
                from app.models.redacao import Redacao  # noqa
                from app.models.ranking import RankingEntry  # noqa
                from app.models.forms import FormsQuestao, FormsAlternativa, FormsParticipante  # nForms
                from app.models.helpzone_social import Post, PostMidia, PostLike, Seguidor, PerfilSocial, NotificacaoSocial  # noqa
            except Exception as e:
                app.logger.warning(f"Alguns modelos opcionais não disponíveis: {e}")

        except Exception as e:
            app.logger.error(f"Aviso durante importação de modelos: {e}")

    # --------- Registro de Blueprints (obrigatórios/opcionais) ----------
    def _register_bp(module_path, attr_name, name_for_log, required=False):
        try:
            mod = __import__(module_path, fromlist=[attr_name])
            bp = getattr(mod, attr_name)
            app.register_blueprint(bp)
            app.logger.info(f"✅ Blueprint {name_for_log} registrado")
            return True
        except ImportError as e:
            msg = f"Blueprint {name_for_log} indisponível: {e}"
            if required:
                app.logger.error(f"❌ {msg}")
                raise
            app.logger.warning(f"⚠️ {msg}")
            return False
        except Exception as e:
            msg = f"Erro ao registrar blueprint {name_for_log}: {e}"
            if required:
                app.logger.error(f"❌ {msg}")
                raise
            app.logger.warning(f"⚠️ {msg}")
            return False

    # Obrigatórios (núcleo)
    _register_bp("app.routes.auth", "auth_bp", "auth", required=True)
    _register_bp("app.routes.main", "main_bp", "main", required=True)
    _register_bp("app.routes.dashboard", "dashboard_bp", "dashboard", required=True)
    _register_bp("app.routes.simulados", "simulados_bp", "simulados", required=True)
    _register_bp("app.routes.progresso", "progresso_bp", "progresso", required=True)
    _register_bp("app.routes.estudo", "estudo_bp", "estudo", required=False)

    # Opcionais (não derrubam o boot se ausentes)
    _register_bp("app.routes.analise", "analise_bp", "analise", required=False)
    _register_bp("app.routes.helpzone", "helpzone_bp", "helpzone", required=False)
    _register_bp("app.routes.shop", "shop_bp", "shop", required=False)
    _register_bp("app.routes.yampi_shop", "yampi_bp", "yampi_shop", required=False)
    _register_bp("app.routes.mapeamento", "mapeamento_bp", "mapeamento", required=False)

    #ROLETA
    #_register_bp("app.routes.roleta", "roleta_bp", "roleta", required=False)
    # ✨ NOVO: Cronograma Personalizado
    _register_bp("app.routes.cronograma", "cronograma_bp", "cronograma", required=False)

    # _register_bp("app.routes.estudo", "estudo_bp", "estudo", required=False)
    _register_bp("app.routes.agendar_simulado", "agendar_simulado_bp", "agendar_simulado", required=False)
    _register_bp("app.routes.redacao", "redacao_bp", "redacao", required=False)
    _register_bp("app.routes.ranking", "ranking_bp", "ranking", required=False)
    _register_bp("app.routes.perfil", "perfil_bp", "perfil", required=False)

    _register_bp("app.routes.webhook_kiwify", "webhook_bp", "webhook_kiwify", required=False) 
    #_register_bp("app.routes.admin_analytics", "admin_analytics_bp", "admin_analytics", required=False)
    _register_bp("app.routes.diagnostico_enem", "diagnostico_bp", "diagnostico_enem", required=False)

    #Fremium
    _register_bp("app.routes.api_freemium", "api_freemium_bp", "api_freemium", required=False)

    #Formulario ENEM
    _register_bp("app.routes.forms_enem", "forms_bp", "forms_enem", required=False)
    _register_bp("app.routes.admin_analytics", "admin_analytics_bp", "admin_analytics", required=False)
   

    #Metricas
    _register_bp("app.routes.dashboard_analytics", "dashboard_analytics_bp", "dashboard_analytics", required=False)



    # Inicialização de badges (se a tabela existir)
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            if inspector.has_table("badge"):
                try:
                    from app.routes.helpzone import initialize_badges  # type: ignore
                    initialize_badges()
                    app.logger.info("[+] Badges inicializadas com sucesso!")
                except Exception as e:
                    app.logger.warning(f"Aviso ao inicializar badges: {e}")
        except Exception as e:
            app.logger.warning(f"Falha ao inspecionar tabelas para badges: {e}")

    # --------- Filtros de template ---------
    @app.template_filter("timeago")
    def timeago_filter(dt):
        """Mostra tempo relativo (ex.: '2 horas atrás')."""
        if not dt:
            return ""
        now = datetime.now()
        diff = now - dt
        if diff.days > 0:
            dias = diff.days
            return f"{dias} dia{'s' if dias > 1 else ''} atrás"
        if diff.seconds > 3600:
            horas = diff.seconds // 3600
            return f"{horas} hora{'s' if horas > 1 else ''} atrás"
        if diff.seconds > 60:
            minutos = diff.seconds // 60
            return f"{minutos} minuto{'s' if minutos > 1 else ''} atrás"
        return "Agora"

    @app.template_filter("format_duration")
    def format_duration_filter(seconds):
        """Formata duração em segundos para 'Xh Ymin'."""
        if not seconds:
            return "0min"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}min" if hours > 0 else f"{minutes}min"

    # --------- Context processors ---------
    @app.context_processor
    def inject_globals():
        return {"app_name": "Plataforma Launcher", "app_version": "2.0.0"}

    @app.context_processor
    def inject_user_data():
        """Injeta métricas do usuário (com fallback seguro)."""
        from flask_login import current_user
        if current_user.is_authenticated:
            try:
                return {
                    "user_moedas": getattr(current_user, "total_moedas", 0) or 0,
                    "user_diamantes": getattr(current_user, "diamantes", 0) or 0,  # ✅ NOVO
                    "user_xp": getattr(current_user, "xp_total", 0) or 0,  # ✅ NOVO
                    "user_tempo_hoje": current_user.tempo_estudo_hoje,  # ✅ SEM ()
                    "user_aulas_concluidas": getattr(current_user, "aulas_concluidas_count", 0),  # ✅ SAFE
                    "user_sequencia": getattr(current_user, "sequencia_dias", 0) or 0,  # ✅ DIRETO
                }
            except Exception as e:
                app.logger.warning(f"Erro ao injetar dados do usuário: {e}")
                return {
                    "user_moedas": 0,
                    "user_diamantes": 0,  # ✅ NOVO
                    "user_xp": 0,  # ✅ NOVO
                    "user_tempo_hoje": 0,
                    "user_aulas_concluidas": 0,
                    "user_sequencia": 0,
                }
        return {}
    # --------- Flask-Login: user_loader ---------
    @login_manager.user_loader
    def load_user(user_id):
        try:
            from app.models.user import User
            return User.query.get(int(user_id))
        except (OperationalError, DatabaseError, ValueError) as e:
            app.logger.warning(f"Erro ao carregar usuário {user_id}: {e}")
            return None

    # --------- Healthcheck ---------
    @app.route("/healthz")
    def healthz():
        # liveness simples (não depende do banco)
        return "ok", 200

    @app.route("/health")
    def health_check():
        try:
            db.session.execute(text("SELECT 1"))
            return {"status": "healthy", "database": "connected"}, 200
        except Exception as e:
            app.logger.error(f"Health check falhou: {e}")
            return {"status": "unhealthy", "error": str(e)}, 500

    app.logger.info("🚀 Aplicação Flask criada com sucesso")
    return app
