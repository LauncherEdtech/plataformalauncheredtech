#!/usr/bin/env python3
"""
Script de Verificação Completa do HelpZone Backend
Executar: python3 verify_helpzone_complete.py
"""

import os
import sys
from datetime import datetime

# Cores para terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def test_imports():
    """Testa se todos os imports necessários estão disponíveis"""
    print_header("TESTE 1: Imports e Dependências")
    
    try:
        from app import app, db
        print_success("Flask app e db importados")
        
        from app.models.user import User
        print_success("Modelo User importado")
        
        from app.models.helpzone_social import (
            Post, PostMidia, PostLike, PostComentario,
            PostSalvo, Seguidor, NotificacaoSocial, PerfilSocial
        )
        print_success("Modelos HelpZone importados")
        
        return True, app, db
    except Exception as e:
        print_error(f"Erro nos imports: {e}")
        return False, None, None

def test_database_tables(app, db):
    """Testa se todas as tabelas existem no banco"""
    print_header("TESTE 2: Tabelas do Banco de Dados")
    
    from app.models.helpzone_social import (
        Post, PostMidia, PostLike, PostComentario,
        PostSalvo, Seguidor, NotificacaoSocial, PerfilSocial
    )
    
    tables = {
        'Post': Post,
        'PostMidia': PostMidia,
        'PostLike': PostLike,
        'PostComentario': PostComentario,
        'PostSalvo': PostSalvo,
        'Seguidor': Seguidor,
        'NotificacaoSocial': NotificacaoSocial,
        'PerfilSocial': PerfilSocial
    }
    
    all_ok = True
    with app.app_context():
        for name, model in tables.items():
            try:
                count = model.query.count()
                print_success(f"{name}: {count} registros")
            except Exception as e:
                print_error(f"{name}: ERRO - {str(e)[:50]}...")
                all_ok = False
    
    return all_ok

def test_user_model(app):
    """Testa o modelo User e seus relacionamentos"""
    print_header("TESTE 3: Modelo User")
    
    from app.models.user import User
    
    with app.app_context():
        user = User.query.first()
        
        if not user:
            print_warning("Nenhum usuário encontrado no banco")
            print_warning("Crie ao menos um usuário para testar completamente")
            return True  # Não é erro crítico
        
        # Testar atributo nome_completo
        try:
            nome = user.nome_completo
            print_success(f"User.nome_completo: '{nome}'")
        except Exception as e:
            print_error(f"User.nome_completo: ERRO - {e}")
            print_warning("Adicione propriedade @nome_completo no modelo User")
            return False
        
        # Testar relacionamento perfil_social
        try:
            perfil = user.perfil_social
            if perfil:
                print_success(f"User.perfil_social: OK (ID: {perfil.id})")
            else:
                print_warning("User.perfil_social existe mas retornou None")
                print_warning("Execute a migração ou crie perfis manualmente")
        except Exception as e:
            print_error(f"User.perfil_social: ERRO - {e}")
            print_warning("Adicione relacionamento perfil_social no User")
            return False
    
    return True

def test_jinja_filters(app):
    """Testa se os filtros Jinja necessários existem"""
    print_header("TESTE 4: Filtros Jinja")
    
    with app.app_context():
        if 'timeago' in app.jinja_env.filters:
            print_success("Filtro 'timeago': OK")
            
            # Testar funcionamento
            test_filter = app.jinja_env.filters['timeago']
            test_date = datetime.utcnow()
            result = test_filter(test_date)
            print_success(f"Teste do filtro: '{result}'")
            return True
        else:
            print_error("Filtro 'timeago': NÃO ENCONTRADO")
            print_warning("Adicione o filtro timeago em app/__init__.py")
            return False

def test_routes(app):
    """Lista e valida as rotas do HelpZone"""
    print_header("TESTE 5: Rotas da API")
    
    required_routes = [
        '/helpzone/feed',
        '/helpzone/criar-post',
        '/helpzone/api/post/<int:post_id>/like',
        '/helpzone/api/post/<int:post_id>/save',
        '/helpzone/api/post/<int:post_id>/comentar',
        '/helpzone/api/user/<int:user_id>/follow',
        '/helpzone/api/perfil/editar',
        '/helpzone/perfil/<int:user_id>',
        '/helpzone/notificacoes',
        '/helpzone/buscar',
    ]
    
    with app.app_context():
        existing_routes = [r.rule for r in app.url_map.iter_rules() if 'helpzone' in r.rule]
        
        all_ok = True
        for route in required_routes:
            # Normalizar para comparação (remover <int:...>)
            route_pattern = route.replace('<int:post_id>', '<post_id>').replace('<int:user_id>', '<user_id>')
            
            found = any(route_pattern.replace('<post_id>', '').replace('<user_id>', '') in r for r in existing_routes)
            
            if found:
                print_success(f"{route}")
            else:
                print_error(f"{route} - NÃO ENCONTRADA")
                all_ok = False
        
        print(f"\n{Colors.BOLD}Total de rotas HelpZone encontradas: {len(existing_routes)}{Colors.END}")
    
    return all_ok

def test_upload_folders():
    """Verifica a existência e permissões das pastas de upload"""
    print_header("TESTE 6: Pastas de Upload")
    
    folders = [
        'app/static/uploads',
        'app/static/uploads/avatars',
        'app/static/uploads/helpzone'
    ]
    
    all_ok = True
    for folder in folders:
        if not os.path.exists(folder):
            print_error(f"{folder}: NÃO EXISTE")
            print_warning(f"Execute: mkdir -p {folder}")
            all_ok = False
        elif not os.access(folder, os.W_OK):
            print_warning(f"{folder}: SEM PERMISSÃO DE ESCRITA")
            print_warning(f"Execute: chmod 755 {folder}")
            all_ok = False
        else:
            # Verificar permissões numéricas
            perms = oct(os.stat(folder).st_mode)[-3:]
            print_success(f"{folder}: OK (permissões: {perms})")
    
    return all_ok

def test_post_model_methods(app, db):
    """Testa métodos específicos do modelo Post"""
    print_header("TESTE 7: Métodos do Modelo Post")
    
    from app.models.helpzone_social import Post
    
    with app.app_context():
        post = Post.query.first()
        
        if not post:
            print_warning("Nenhum post encontrado no banco")
            print_warning("Métodos não puderam ser testados completamente")
            return True  # Não é erro crítico
        
        # Testar métodos
        methods = ['user_liked', 'user_disliked', 'user_saved', 'get_score', 'to_dict']
        
        all_ok = True
        for method_name in methods:
            if hasattr(post, method_name):
                try:
                    if method_name in ['user_liked', 'user_disliked', 'user_saved']:
                        # Métodos que precisam de user_id
                        result = getattr(post, method_name)(1)
                    else:
                        # Métodos sem parâmetros
                        result = getattr(post, method_name)()
                    
                    print_success(f"Post.{method_name}(): OK")
                except Exception as e:
                    print_error(f"Post.{method_name}(): ERRO - {e}")
                    all_ok = False
            else:
                print_error(f"Post.{method_name}(): MÉTODO NÃO ENCONTRADO")
                all_ok = False
        
        return all_ok

def test_profile_auto_creation(app, db):
    """Testa se perfis sociais são criados automaticamente"""
    print_header("TESTE 8: Criação Automática de Perfil")
    
    from app.models.user import User
    from app.models.helpzone_social import PerfilSocial
    
    with app.app_context():
        users = User.query.all()
        
        if not users:
            print_warning("Nenhum usuário encontrado")
            return True
        
        users_without_profile = []
        for user in users:
            if not PerfilSocial.query.filter_by(user_id=user.id).first():
                users_without_profile.append(user.id)
        
        if users_without_profile:
            print_warning(f"{len(users_without_profile)} usuários sem perfil social")
            print_warning(f"IDs: {users_without_profile}")
            print_warning("Adicione hook de criação automática ou crie manualmente")
            return False
        else:
            print_success(f"Todos os {len(users)} usuários têm perfil social")
            return True

def generate_fix_script(failed_tests):
    """Gera script de correção baseado nos testes que falharam"""
    print_header("SCRIPT DE CORREÇÃO")
    
    if not failed_tests:
        print_success("Nenhuma correção necessária!")
        return
    
    print(f"{Colors.BOLD}Para corrigir os problemas, execute:{Colors.END}\n")
    
    if 'tables' in failed_tests:
        print("# Criar tabelas do banco:")
        print("python3 -c \"from app import app, db; app.app_context().push(); db.create_all()\"")
        print()
    
    if 'folders' in failed_tests:
        print("# Criar pastas de upload:")
        print("mkdir -p app/static/uploads/{avatars,helpzone}")
        print("chmod -R 755 app/static/uploads")
        print()
    
    if 'timeago' in failed_tests:
        print("# Adicionar filtro timeago em app/__init__.py:")
        print("# Ver arquivo CORRECOES_ESPECIFICAS.md seção #1")
        print()
    
    if 'user_relations' in failed_tests:
        print("# Adicionar relacionamentos no User:")
        print("# Ver arquivo CORRECOES_ESPECIFICAS.md seção #2")
        print()
    
    if 'profiles' in failed_tests:
        print("# Criar perfis sociais para usuários existentes:")
        print("python3 -c \"from app import app, db; from app.models.user import User; from app.models.helpzone_social import PerfilSocial; app.app_context().push(); [db.session.add(PerfilSocial(user_id=u.id)) for u in User.query.all() if not PerfilSocial.query.filter_by(user_id=u.id).first()]; db.session.commit()\"")
        print()

def main():
    """Executa todos os testes"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}🚀 VERIFICAÇÃO COMPLETA DO HELPZONE BACKEND{Colors.END}")
    print(f"{Colors.BOLD}Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}\n")
    
    failed_tests = []
    
    # Teste 1: Imports
    success, app, db = test_imports()
    if not success:
        print_error("\nErro crítico nos imports. Impossível continuar.")
        sys.exit(1)
    
    # Teste 2: Tabelas
    if not test_database_tables(app, db):
        failed_tests.append('tables')
    
    # Teste 3: User Model
    if not test_user_model(app):
        failed_tests.append('user_relations')
    
    # Teste 4: Filtros Jinja
    if not test_jinja_filters(app):
        failed_tests.append('timeago')
    
    # Teste 5: Rotas
    if not test_routes(app):
        failed_tests.append('routes')
    
    # Teste 6: Pastas
    if not test_upload_folders():
        failed_tests.append('folders')
    
    # Teste 7: Métodos do Post
    if not test_post_model_methods(app, db):
        failed_tests.append('post_methods')
    
    # Teste 8: Perfis
    if not test_profile_auto_creation(app, db):
        failed_tests.append('profiles')
    
    # Resultado Final
    print_header("RESULTADO FINAL")
    
    if not failed_tests:
        print_success("🎉 TODOS OS TESTES PASSARAM!")
        print(f"\n{Colors.GREEN}{Colors.BOLD}O HelpZone está 100% funcional e pronto para uso!{Colors.END}\n")
    else:
        print_warning(f"⚠️  {len(failed_tests)} categoria(s) com problemas")
        print(f"\n{Colors.YELLOW}Corrija os problemas antes de usar o HelpZone em produção.{Colors.END}\n")
        generate_fix_script(failed_tests)
    
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Verificação interrompida pelo usuário.{Colors.END}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}ERRO INESPERADO: {e}{Colors.END}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
