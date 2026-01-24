# ===== ARQUIVO DE DEBUG: debug_context_processors.py =====
# Use este arquivo para identificar e corrigir problemas de context processors

import traceback
from flask import current_app
from flask_login import current_user

def debug_user_properties():
    """
    Função para debugar propriedades do usuário que estão causando o erro
    """
    if not current_user.is_authenticated:
        print("❌ Usuário não autenticado")
        return
    
    print("🔍 DEBUGANDO PROPRIEDADES DO USUÁRIO:")
    print(f"  • ID: {current_user.id}")
    print(f"  • Nome: {current_user.nome}")
    
    # Testar cada propriedade individualmente
    propriedades_testar = [
        'xp_total', 'diamantes', 'tempo_estudo_hoje', 
        'tempo_estudo_semana', 'tempo_estudo_mes'
    ]
    
    for prop in propriedades_testar:
        try:
            if hasattr(current_user, prop):
                valor = getattr(current_user, prop)
                
                # Verificar se é callable
                if callable(valor):
                    print(f"  ⚠️ {prop}: É CALLABLE - tentando chamar...")
                    try:
                        resultado = valor()
                        print(f"    ✅ Resultado: {resultado} (tipo: {type(resultado)})")
                    except Exception as e:
                        print(f"    ❌ ERRO ao chamar: {e}")
                else:
                    print(f"  ✅ {prop}: {valor} (tipo: {type(valor)})")
            else:
                print(f"  ❌ {prop}: NÃO EXISTE")
                
        except Exception as e:
            print(f"  ❌ ERRO ao acessar {prop}: {e}")
            traceback.print_exc()

def safe_get_user_property(prop_name, default_value=0):
    """
    Função auxiliar para acessar propriedades do usuário de forma segura
    """
    if not current_user.is_authenticated:
        return default_value
        
    try:
        if hasattr(current_user, prop_name):
            valor = getattr(current_user, prop_name)
            
            # Se for callable, chamar
            if callable(valor):
                try:
                    return valor()
                except Exception as e:
                    print(f"⚠️ Erro ao chamar {prop_name}(): {e}")
                    return default_value
            else:
                # Se for None, retornar valor padrão
                return valor if valor is not None else default_value
        else:
            return default_value
            
    except Exception as e:
        print(f"⚠️ Erro ao acessar {prop_name}: {e}")
        return default_value

# ===== CORREÇÃO DEFINITIVA PARA O CONTEXT PROCESSOR =====

def create_safe_context_processor():
    """
    Cria um context processor super seguro que não causará erros
    """
    def inject_user_data_safe():
        try:
            if not current_user.is_authenticated:
                return {}
            
            # Dados seguros com fallbacks
            dados_seguros = {
                'user_xp_total': safe_get_user_property('xp_total', 0),
                'user_diamantes': safe_get_user_property('diamantes', 0),
                'user_tempo_hoje': safe_get_user_property('tempo_estudo_hoje', 0),
                'user_tempo_semana': safe_get_user_property('tempo_estudo_semana', 0),
                'user_tempo_mes': safe_get_user_property('tempo_estudo_mes', 0),
            }
            
            # Garantir que todos são integers
            for key, value in dados_seguros.items():
                try:
                    dados_seguros[key] = int(value) if value is not None else 0
                except (ValueError, TypeError):
                    dados_seguros[key] = 0
            
            return dados_seguros
            
        except Exception as e:
            print(f"⚠️ Erro crítico no context processor: {e}")
            traceback.print_exc()
            # Retornar valores padrão
            return {
                'user_xp_total': 0,
                'user_diamantes': 0,
                'user_tempo_hoje': 0,
                'user_tempo_semana': 0,
                'user_tempo_mes': 0
            }
    
    return inject_user_data_safe

# ===== CORREÇÃO PARA O MODELO USER.PY =====

def fix_user_properties():
    """
    Código para adicionar ao user.py para corrigir as propriedades
    """
    codigo_correcao = '''
    # ✅ CORREÇÃO: Propriedades de tempo como @property (não callable diretamente)
    @property
    def tempo_estudo_hoje(self):
        """Propriedade segura para tempo de estudo hoje"""
        try:
            from app.models.estatisticas import TempoEstudo
            return TempoEstudo.calcular_tempo_hoje(self.id) or 0
        except Exception as e:
            from flask import current_app
            current_app.logger.warning(f"Erro ao calcular tempo hoje: {e}")
            return 0

    @property
    def tempo_estudo_semana(self):
        """Propriedade segura para tempo de estudo da semana"""
        try:
            from app.models.estatisticas import TempoEstudo
            return TempoEstudo.calcular_tempo_semana(self.id) or 0
        except Exception as e:
            from flask import current_app
            current_app.logger.warning(f"Erro ao calcular tempo semana: {e}")
            return 0

    @property
    def tempo_estudo_mes(self):
        """Propriedade segura para tempo de estudo do mês"""
        try:
            from app.models.estatisticas import TempoEstudo
            return TempoEstudo.calcular_tempo_mes(self.id) or 0
        except Exception as e:
            from flask import current_app
            current_app.logger.warning(f"Erro ao calcular tempo mês: {e}")
            return 0
    '''
    
    print("📝 Adicione este código ao modelo User:")
    print(codigo_correcao)

if __name__ == "__main__":
    print("🔧 EXECUTANDO DEBUG DOS CONTEXT PROCESSORS...")
    # Use estas funções para debugar:
    # debug_user_properties()
    # fix_user_properties()
    pass
