# app/models/user.py - VERSÃO COMPLETA COM RESET DE SENHA

# ========================================
# CONTROLE FREEMIUM - MODO CAMPANHA
# ========================================
FREEMIUM_ATIVO = False


from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
from sqlalchemy.exc import OperationalError, DatabaseError
from sqlalchemy import event
import logging
import time

logger = logging.getLogger(__name__)

class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), index=True, unique=True)
    email = db.Column(db.String(256), index=True, unique=True)
    password_hash = db.Column(db.String(256))
    nome_completo = db.Column(db.String(256))
    
    # Sistema XP e Diamantes
    xp_total = db.Column(db.Integer, default=0)
    diamantes = db.Column(db.Integer, default=0)
    ultimo_reset_diamantes = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Campos legados
    total_moedas = db.Column(db.Integer, default=0)

    # Campos Freemium
    redacoes_gratuitas_restantes = db.Column(db.Integer, default=3)
    simulados_gratuitos_restantes = db.Column(db.Integer, default=3)
    aulas_gratuitas_restantes = db.Column(db.Integer, default=10)
    plano_ativo = db.Column(db.String(20), default='free')
    data_expiracao_plano = db.Column(db.DateTime, nullable=True)
    plano_kiwify_id = db.Column(db.String(100), nullable=True)
    pode_resgatar_roleta = db.Column(db.Boolean, default=False)

    data_registro = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    cpf = db.Column(db.String(14))
    telefone = db.Column(db.String(15), nullable=True)
    password_changed = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    sequencia_dias = db.Column(db.Integer, default=0)
    ultimo_acesso = db.Column(db.Date)
    
    # ========================================
    # 🔐 CAMPOS PARA RESET DE SENHA
    # ========================================
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    password_last_changed = db.Column(db.DateTime, nullable=True)
    
    # Relacionamentos
    simulados = db.relationship('Simulado', backref='usuario', lazy='dynamic')

    # ========================
    # MÉTODOS DE SEQUÊNCIA
    # ========================
    def atualizar_sequencia(self):
        """Atualiza a sequência de dias consecutivos de acesso"""
        from datetime import date, timedelta
        
        hoje = date.today()
        
        if self.ultimo_acesso is None:
            self.sequencia_dias = 1
            self.ultimo_acesso = hoje
            db.session.commit()
            logger.info(f"Usuário {self.id} iniciou sequência: 1 dia")
            return
        
        if self.ultimo_acesso == hoje:
            return
        
        if self.ultimo_acesso == hoje - timedelta(days=1):
            self.sequencia_dias += 1
            self.ultimo_acesso = hoje
            db.session.commit()
            logger.info(f"Usuário {self.id} manteve sequência: {self.sequencia_dias} dias")
            return
        
        self.sequencia_dias = 1
        self.ultimo_acesso = hoje
        db.session.commit()
        logger.info(f"Usuário {self.id} quebrou sequência, resetando para: 1 dia")

    # ========================================
    # 🔐 MÉTODOS DE RESET DE SENHA
    # ========================================
    def generate_reset_token(self):
        """Gera token de reset de senha válido por 30 minutos"""
        import secrets
        
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expiry = datetime.utcnow() + timedelta(minutes=30)
        
        try:
            db.session.commit()
            logger.info(f"🔑 Token de reset gerado para {self.email}")
            return self.reset_token
        except Exception as e:
            logger.error(f"Erro ao gerar token: {e}")
            db.session.rollback()
            return None

    def validate_reset_token(self, token):
        """Valida token de reset de senha"""
        if not self.reset_token or self.reset_token != token:
            logger.warning(f"⚠️ Token inválido para {self.email}")
            return False
        
        if not self.reset_token_expiry or self.reset_token_expiry < datetime.utcnow():
            logger.warning(f"⏰ Token expirado para {self.email}")
            return False
        
        return True

    def clear_reset_token(self):
        """Limpa token de reset após uso"""
        self.reset_token = None
        self.reset_token_expiry = None
        
        try:
            db.session.commit()
            logger.info(f"🧹 Token de reset limpo para {self.email}")
        except Exception as e:
            logger.error(f"Erro ao limpar token: {e}")
            db.session.rollback()

    @classmethod
    def find_by_reset_token(cls, token):
        """Busca usuário por token de reset"""
        try:
            return cls.query.filter_by(reset_token=token).first()
        except Exception as e:
            logger.error(f"Erro ao buscar por token: {e}")
            return None

    # ========================
    # MÉTODOS FREEMIUM
    # ========================
    @property
    def tem_plano_ativo(self):
        """Verifica se o usuário tem um plano pago ativo"""
        if self.plano_ativo == 'free':
            return False
        
        if self.data_expiracao_plano and self.data_expiracao_plano > datetime.utcnow():
            return True
        
        if self.plano_ativo != 'free':
            self.plano_ativo = 'free'
            db.session.commit()
        
        return False
    
    @property
    def pode_fazer_redacao(self):
        """Verifica se pode fazer redação"""
        # ⚠️ MODO CAMPANHA - Libera acesso ilimitado
        if not FREEMIUM_ATIVO:
            return True, None
        
        if self.tem_plano_ativo:
            return True, None
        
        if self.redacoes_gratuitas_restantes > 0:
            return True, None
        
        return False, "Você atingiu o limite de redações gratuitas"
    

    @property
    def pode_fazer_simulado(self):
        """Verifica se pode fazer simulado"""
        # ⚠️ MODO CAMPANHA - Libera acesso ilimitado
        if not FREEMIUM_ATIVO:
            return True, None
        
        if self.tem_plano_ativo:
            return True, None
        
        if self.simulados_gratuitos_restantes > 0:
            return True, None
        
        return False, "Você atingiu o limite de simulados gratuitos"

    @property
    def pode_assistir_aula(self):
        """Verifica se pode assistir aula"""
        # ⚠️ MODO CAMPANHA - Libera acesso ilimitado
        if not FREEMIUM_ATIVO:
            return True, None
        
        if self.tem_plano_ativo:
            return True, None
        
        if self.aulas_gratuitas_restantes > 0:
            return True, None
        
        return False, "Você atingiu o limite de aulas gratuitas"

    def consumir_redacao_gratuita(self):
        """Consome uma redação gratuita"""
        if not self.tem_plano_ativo and self.redacoes_gratuitas_restantes > 0:
            self.redacoes_gratuitas_restantes -= 1
            db.session.commit()
            logger.info(f"Usuário {self.id} consumiu redação gratuita. Restantes: {self.redacoes_gratuitas_restantes}")
    
    def consumir_simulado_gratuito(self):
        """Consome um simulado gratuito"""
        if not self.tem_plano_ativo and self.simulados_gratuitos_restantes > 0:
            self.simulados_gratuitos_restantes -= 1
            db.session.commit()
            logger.info(f"Usuário {self.id} consumiu simulado gratuito. Restantes: {self.simulados_gratuitos_restantes}")
    
    def consumir_aula_gratuita(self):
        """Consome uma aula gratuita"""
        if not self.tem_plano_ativo and self.aulas_gratuitas_restantes > 0:
            self.aulas_gratuitas_restantes -= 1
            db.session.commit()
            logger.info(f"Usuário {self.id} consumiu aula gratuita. Restantes: {self.aulas_gratuitas_restantes}")
    
    def ativar_plano(self, tipo_plano, kiwify_id=None):
        """Ativa um plano pago (mensal ou anual)"""
        if tipo_plano not in ['mensal', 'anual']:
            logger.error(f"Tipo de plano inválido: {tipo_plano}")
            return False
        
        self.plano_ativo = tipo_plano
        self.plano_kiwify_id = kiwify_id
        
        if tipo_plano == 'mensal':
            self.data_expiracao_plano = datetime.utcnow() + timedelta(days=30)
        elif tipo_plano == 'anual':
            self.data_expiracao_plano = datetime.utcnow() + timedelta(days=365)
        
        logger.info(f"Plano {tipo_plano} ativado para usuário {self.id}. Expira em: {self.data_expiracao_plano}")
        db.session.commit()
        return True
    
    def liberar_resgate_roleta(self):
        """Libera o resgate da roleta após pagamento da taxa"""
        self.pode_resgatar_roleta = True
        db.session.commit()
        logger.info(f"Resgate de roleta liberado para usuário {self.id}")
    
    @property
    def status_plano_display(self):
        """Retorna string legível do status do plano"""
        if self.tem_plano_ativo:
            dias_restantes = (self.data_expiracao_plano - datetime.utcnow()).days
            return f"Plano {self.plano_ativo.title()} - {dias_restantes} dias restantes"
        return "Plano Gratuito"

    # ========================
    # OPERAÇÕES DE BANCO SEGURAS
    # ========================
    def safe_db_operation(self, operation_func, max_retries=3, delay=1):
        """Executa operação de banco com retry automático"""
        for attempt in range(max_retries):
            try:
                return operation_func()
            except (OperationalError, DatabaseError) as e:
                logger.warning(f"Tentativa {attempt + 1} falhou para {operation_func.__name__}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(delay * (attempt + 1))
                    try:
                        db.session.rollback()
                    except:
                        pass
                else:
                    logger.error(f"Todas as tentativas falharam para {operation_func.__name__}")
                    raise e

    # ========================
    # MÉTODOS DE SENHA
    # ========================
    def set_password(self, password):
        """Define senha de forma segura"""
        try:
            self.password_hash = generate_password_hash(password)
            self.password_changed = True
            self.password_last_changed = datetime.utcnow()
            logger.info(f"Senha definida para usuário {self.id or 'novo'}")
        except Exception as e:
            logger.error(f"Erro ao definir senha: {e}")
            raise
        
    def check_password(self, password):
        """Verifica senha de forma segura"""
        try:
            if not self.password_hash:
                logger.warning(f"Usuário {self.id} sem hash de senha")
                return False
            return check_password_hash(self.password_hash, password)
        except Exception as e:
            logger.error(f"Erro ao verificar senha do usuário {self.id}: {e}")
            return False
    
    @property
    def active(self):
        """Propriedade para Flask-Login"""
        try:
            return bool(self.is_active)
        except:
            return True
    
    def needs_password_change(self):
        """Verifica se precisa mudar senha"""
        try:
            return not bool(self.password_changed)
        except (OperationalError, DatabaseError) as e:
            logger.warning(f"Erro ao verificar necessidade de mudança de senha: {e}")
            return False

    # ========================
    # MÉTODOS DE XP E DIAMANTES
    # ========================
    def adicionar_xp(self, quantidade, atividade='geral', descricao=''):
        """Adiciona XP de forma segura"""
        try:
            def operacao_xp():
                from app.services.xp_service import XpService
                resultado = XpService.conceder_xp(self, quantidade, atividade, descricao)
                return resultado is not None
            
            return self.safe_db_operation(operacao_xp)
        except Exception as e:
            logger.error(f"Erro ao adicionar XP para usuário {self.id}: {e}")
            return False
    
    def pode_gastar_diamantes(self, quantidade):
        """Verifica se pode gastar diamantes"""
        try:
            diamantes_atual = getattr(self, 'diamantes', 0) or 0
            return diamantes_atual >= quantidade
        except Exception as e:
            logger.warning(f"Erro ao verificar diamantes do usuário {self.id}: {e}")
            return False
    
    def gastar_diamantes(self, quantidade, motivo=''):
        """Gasta diamantes de forma segura"""
        try:
            def operacao_diamantes():
                from app.services.xp_service import XpService
                sucesso, resultado = XpService.gastar_diamantes(self, quantidade, motivo)
                return sucesso
            
            return self.safe_db_operation(operacao_diamantes)
        except Exception as e:
            logger.error(f"Erro ao gastar diamantes do usuário {self.id}: {e}")
            return False
    
    def adicionar_diamantes(self, quantidade, motivo=''):
        """Adiciona diamantes de forma segura"""
        try:
            def operacao_add_diamantes():
                self.diamantes = (getattr(self, 'diamantes', 0) or 0) + quantidade
                logger.info(f"Usuário {self.id} ganhou {quantidade} diamantes. Total: {self.diamantes}")
                return True
            
            return self.safe_db_operation(operacao_add_diamantes)
        except Exception as e:
            logger.error(f"Erro ao adicionar diamantes para usuário {self.id}: {e}")
            return False

    # ========================
    # PROPRIEDADES DE TEMPO DE ESTUDO
    # ========================
    @property
    def tempo_estudo_hoje(self):
        """Calcula tempo de estudo de hoje de forma segura"""
        try:
            def operacao_tempo_hoje():
                from app.models.estatisticas import TempoEstudo
                return TempoEstudo.calcular_tempo_hoje(self.id) or 0
            
            return self.safe_db_operation(operacao_tempo_hoje)
        except Exception as e:
            logger.warning(f"Erro ao calcular tempo de hoje para usuário {self.id}: {e}")
            return 0



    @property
    def tempo_estudo_semana(self):
        """Calcula tempo de estudo da semana de forma segura"""
        try:
            def operacao_tempo_semana():
                from app.models.estatisticas import TempoEstudo
                return TempoEstudo.calcular_tempo_semana(self.id) or 0
            
            return self.safe_db_operation(operacao_tempo_semana)
        except Exception as e:
            logger.warning(f"Erro ao calcular tempo da semana para usuário {self.id}: {e}")
            return 0

    @property
    def tempo_estudo_mes(self):
        """Calcula tempo de estudo do mês de forma segura"""
        try:
            def operacao_tempo_mes():
                from app.models.estatisticas import TempoEstudo
                return TempoEstudo.calcular_tempo_mes(self.id) or 0
            
            return self.safe_db_operation(operacao_tempo_mes)
        except Exception as e:
            logger.warning(f"Erro ao calcular tempo do mês para usuário {self.id}: {e}")
            return 0

    # ========================
    # MÉTODOS LEGADOS
    # ========================
    def adicionar_moedas(self, quantidade, tipo='geral', descricao=''):
        """LEGADO: Convertido para usar o novo sistema XP"""
        logger.warning("Método adicionar_moedas é legado. Use adicionar_xp")
        return self.adicionar_xp(quantidade, tipo, descricao)
    
    def gastar_moedas(self, quantidade, tipo='compra', descricao=''):
        """LEGADO: Convertido para usar diamantes"""
        logger.warning("Método gastar_moedas é legado. Use gastar_diamantes")
        return self.gastar_diamantes(quantidade, descricao)

    # ========================
    # PROPRIEDADES ÚTEIS
    # ========================
    @property
    def status_diamantes(self):
        """Retorna informações sobre os diamantes do usuário"""
        try:
            return {
                'diamantes': getattr(self, 'diamantes', 0) or 0,
                'xp_total': getattr(self, 'xp_total', 0) or 0,
                'ratio_diamantes': "1 XP = 0.5 💎",
                'proximo_reset': self.calcular_proximo_reset()
            }
        except Exception as e:
            logger.warning(f"Erro ao obter status de diamantes: {e}")
            return {
                'diamantes': 0,
                'xp_total': 0,
                'ratio_diamantes': "1 XP = 0.5 💎",
                'proximo_reset': None
            }
    
    def calcular_proximo_reset(self):
        """Calcula quando será o próximo reset de diamantes"""
        try:
            hoje = datetime.utcnow()
            if hoje.month == 12:
                proximo_mes = hoje.replace(year=hoje.year + 1, month=1, day=1)
            else:
                proximo_mes = hoje.replace(month=hoje.month + 1, day=1)
            return proximo_mes
        except Exception as e:
            logger.warning(f"Erro ao calcular próximo reset: {e}")
            return None
    
    # ========================
    # MÉTODOS DE ESTUDO
    # ========================
    def calcular_sequencia_estudo(self):
        """Calcula sequência de dias estudando de forma segura"""
        try:
            def operacao_sequencia():
                from app.models.estudo import SessaoEstudo
                from sqlalchemy import func
                from datetime import datetime, timedelta
                
                hoje = datetime.now().date()
                sequencia = 0
                data_verificacao = hoje
                
                while sequencia < 365:
                    sessoes_do_dia = SessaoEstudo.query.filter(
                        SessaoEstudo.user_id == self.id,
                        func.date(SessaoEstudo.inicio) == data_verificacao,
                        SessaoEstudo.tempo_ativo > 300
                    ).first()
                    if sessoes_do_dia:
                        sequencia += 1
                        data_verificacao -= timedelta(days=1)
                    else:
                        break
                return sequencia
            
            return self.safe_db_operation(operacao_sequencia)
        except Exception as e:
            logger.error(f"Erro ao calcular sequência de estudo: {e}")
            return 0

    def calcular_total_moedas_from_history(self):
        """LEGADO: Mantido para compatibilidade"""
        try:
            return getattr(self, 'xp_total', 0) or 0
        except:
            return 0

    # ========================
    # MÉTODOS DE CLASSE
    # ========================
    @classmethod
    def safe_get_by_email(cls, email):
        """Busca usuário por email de forma segura"""
        try:
            return cls.query.filter_by(email=email).first()
        except (OperationalError, DatabaseError) as e:
            logger.error(f"Erro ao buscar usuário por email: {e}")
            raise e
    
    @classmethod
    def safe_get_by_id(cls, user_id):
        """Busca usuário por ID de forma segura"""
        try:
            return cls.query.get(int(user_id))
        except (OperationalError, DatabaseError, ValueError) as e:
            logger.error(f"Erro ao buscar usuário por ID: {e}")
            return None


# ========================
# CONFIGURAÇÃO DE RELACIONAMENTOS
# ========================
def setup_user_relationships():
    """Adiciona relacionamentos extras ao User depois que todos os modelos estão definidos"""
    try:
        if not hasattr(User, 'historico_moedas'):
            from app.models.estudo import Moeda
            User.historico_moedas = db.relationship('Moeda', backref='usuario', lazy='dynamic')
        
        if not hasattr(User, 'xp_sessions'):
            pass
            
        logger.info("✅ Relacionamentos do User configurados com sucesso")
    except Exception as e:
        logger.warning(f"Aviso ao configurar relacionamentos: {e}")


# ========================
# USER LOADER
# ========================
@login_manager.user_loader
def load_user(user_id):
    """User loader resistente a erros"""
    try:
        return User.safe_get_by_id(user_id)
    except Exception as e:
        logger.error(f"Erro no user_loader para ID {user_id}: {e}")
        return None
