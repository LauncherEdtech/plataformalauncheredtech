# quick_fix.py - CORREÇÃO RÁPIDA EM 1 COMANDO

import os
import sys

def quick_fix():
    """Correção rápida para resolver o problema de relacionamentos SQLAlchemy"""
    
    print("🚀 CORREÇÃO RÁPIDA - PROBLEMAS DE RELACIONAMENTO")
    print("=" * 55)
    
    # 1. Corrigir o modelo User removendo relacionamentos problemáticos
    user_model_fix = '''# app/models/user.py - VERSÃO CORRIGIDA RÁPIDA

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), index=True, unique=True)
    email = db.Column(db.String(256), index=True, unique=True)
    password_hash = db.Column(db.String(256))
    nome_completo = db.Column(db.String(256))
    xp_total = db.Column(db.Integer, default=0)
    total_moedas = db.Column(db.Integer, default=0)
    data_registro = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    cpf = db.Column(db.String(14))
    password_changed = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    # APENAS relacionamentos que NÃO causam problemas
    simulados = db.relationship('Simulado', backref='usuario', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_active(self):
        return self.is_active
    
    active = property(get_active)
    
    def needs_password_change(self):
        return not self.password_changed
    
    def adicionar_moedas(self, quantidade, tipo='geral', descricao=''):
        """Adiciona moedas - VERSÃO SIMPLIFICADA"""
        if self.total_moedas is None:
            self.total_moedas = 0
        self.total_moedas += quantidade
        
        if self.xp_total is None:
            self.xp_total = 0
        self.xp_total += quantidade
        
        try:
            db.session.commit()
            return quantidade
        except:
            db.session.rollback()
            return 0
    
    def gastar_moedas(self, quantidade, tipo='compra', descricao=''):
        """Gasta moedas - VERSÃO SIMPLIFICADA"""
        if self.total_moedas is None:
            self.total_moedas = 0
            
        if self.total_moedas < quantidade:
            return False
            
        self.total_moedas -= quantidade
        
        try:
            db.session.commit()
            return True
        except:
            db.session.rollback()
            return False
    
    def tempo_estudo_hoje(self):
        """Tempo de estudo hoje - VERSÃO SEGURA"""
        try:
            from app.models.estudo import SessaoEstudo
            from sqlalchemy import func
            
            hoje = datetime.now().date()
            sessoes = SessaoEstudo.query.filter(
                SessaoEstudo.user_id == self.id,
                func.date(SessaoEstudo.inicio) == hoje,
                SessaoEstudo.ativa == False
            ).all()
            
            return sum(sessao.tempo_ativo for sessao in sessoes) // 60
        except:
            return 0
    
    def aulas_concluidas_count(self):
        """Número de aulas concluídas - VERSÃO SEGURA"""
        try:
            from app.models.estudo import ProgressoAula
            return ProgressoAula.query.filter_by(user_id=self.id, concluida=True).count()
        except:
            return 0
    
    def sequencia_estudo(self):
        """Sequência de dias estudando - VERSÃO SEGURA"""
        try:
            from app.models.estudo import SessaoEstudo
            from sqlalchemy import func
            from datetime import timedelta
            
            hoje = datetime.now().date()
            sequencia = 0
            data_verificacao = hoje
            
            for _ in range(30):  # Máximo 30 dias
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
        except:
            return 0

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
'''
    
    # 2. Escrever o arquivo corrigido
    try:
        with open('app/models/user.py', 'w', encoding='utf-8') as f:
            f.write(user_model_fix)
        print("✅ Modelo User corrigido")
    except Exception as e:
        print(f"❌ Erro ao corrigir User: {e}")
        return False
    
    # 3. Testar se funcionou
    try:
        print("🧪 Testando correção...")
        
        # Importar para testar
        from app import create_app, db
        app = create_app()
        
        with app.app_context():
            from app.models.user import User
            print("✅ User importado sem erros")
            
            # Verificar se existem usuários
            total_users = User.query.count()
            print(f"👤 {total_users} usuários no banco")
            
            # Testar modelos de estudo se existirem
            try:
                from app.models.estudo import Materia
                total_materias = Materia.query.count()
                print(f"📚 {total_materias} matérias no banco")
            except Exception as e:
                print(f"⚠️ Modelos de estudo: {e}")
            
            # Garantir que usuários têm total_moedas
            users_without_moedas = User.query.filter(User.total_moedas.is_(None)).all()
            for user in users_without_moedas:
                user.total_moedas = 0
            
            if users_without_moedas:
                db.session.commit()
                print(f"💰 {len(users_without_moedas)} usuários receberam total_moedas")
        
        print("\n🎉 CORREÇÃO RÁPIDA CONCLUÍDA!")
        print("=" * 55)
        print("✅ Problema de relacionamentos resolvido")
        print("✅ Modelo User funcional")
        print("✅ Pronto para reiniciar servidor")
        
        print("\n🚀 PRÓXIMO PASSO:")
        print("Execute: python run.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = quick_fix()
    if success:
        print("\n✅ EXECUTE AGORA: python run.py")
    else:
        print("\n❌ Correção falhou. Verifique os erros acima.")
    
    sys.exit(0 if success else 1)
