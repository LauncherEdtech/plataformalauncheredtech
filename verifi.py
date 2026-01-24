#!/usr/bin/env python3
"""
Script de Diagnóstico - Sistema de Busca HelpZone
Verifica dados no banco e identifica problemas
"""

import sys
import os

# Adicionar path do projeto
sys.path.insert(0, '/home/launchercursos/launcheredit/launcher-app')

from app import create_app, db
from app.models.user import User
from app.models.helpzone_social import Post, Hashtag, PerfilSocial, post_hashtags
from sqlalchemy import text

app = create_app()

print("=" * 70)
print("DIAGNÓSTICO - SISTEMA DE BUSCA HELPZONE")
print("=" * 70)
print()

with app.app_context():
    
    # ====================================================================
    # 1. VERIFICAR USUÁRIOS
    # ====================================================================
    print("📊 [1/6] VERIFICANDO USUÁRIOS")
    print("-" * 70)
    
    try:
        total_usuarios = User.query.count()
        usuarios_ativos = User.query.filter_by(is_active=True).count()
        usuarios_com_nome = User.query.filter(User.nome_completo.isnot(None)).count()
        
        print(f"  ✓ Total de usuários: {total_usuarios}")
        print(f"  ✓ Usuários ativos: {usuarios_ativos}")
        print(f"  ✓ Usuários com nome_completo: {usuarios_com_nome}")
        
        # Mostrar alguns exemplos
        exemplos = User.query.filter(User.is_active == True).limit(5).all()
        print(f"\n  Exemplos de usuários:")
        for u in exemplos:
            print(f"    • ID {u.id}: {u.nome_completo or u.username} (username: {u.username})")
        
    except Exception as e:
        print(f"  ❌ ERRO: {str(e)}")
    
    print()
    
    # ====================================================================
    # 2. VERIFICAR PERFIS SOCIAIS
    # ====================================================================
    print("📊 [2/6] VERIFICANDO PERFIS SOCIAIS")
    print("-" * 70)
    
    try:
        total_perfis = PerfilSocial.query.count()
        perfis_com_posts = PerfilSocial.query.filter(PerfilSocial.total_posts > 0).count()
        
        print(f"  ✓ Total de perfis sociais: {total_perfis}")
        print(f"  ✓ Perfis com posts: {perfis_com_posts}")
        
        # Perfil mais ativo
        perfil_ativo = PerfilSocial.query.order_by(PerfilSocial.score_social.desc()).first()
        if perfil_ativo:
            usuario = User.query.get(perfil_ativo.user_id)
            print(f"\n  Perfil mais ativo:")
            print(f"    • {usuario.nome_completo if usuario else 'Desconhecido'}")
            print(f"    • Posts: {perfil_ativo.total_posts}")
            print(f"    • Seguidores: {perfil_ativo.total_seguidores}")
            print(f"    • Score: {perfil_ativo.score_social}")
        
    except Exception as e:
        print(f"  ❌ ERRO: {str(e)}")
    
    print()
    
    # ====================================================================
    # 3. VERIFICAR POSTS
    # ====================================================================
    print("📊 [3/6] VERIFICANDO POSTS")
    print("-" * 70)
    
    try:
        total_posts = Post.query.count()
        posts_ativos = Post.query.filter_by(ativo=True).count()
        posts_com_texto = Post.query.filter(Post.texto.isnot(None), Post.ativo == True).count()
        
        print(f"  ✓ Total de posts: {total_posts}")
        print(f"  ✓ Posts ativos: {posts_ativos}")
        print(f"  ✓ Posts com texto: {posts_com_texto}")
        
        # Mostrar alguns posts
        exemplos = Post.query.filter_by(ativo=True).order_by(Post.data_criacao.desc()).limit(3).all()
        print(f"\n  Últimos posts:")
        for p in exemplos:
            autor = User.query.get(p.user_id)
            texto_preview = p.texto[:50] + "..." if p.texto and len(p.texto) > 50 else p.texto or "[sem texto]"
            print(f"    • Post {p.id} por {autor.nome_completo if autor else 'Desconhecido'}")
            print(f"      {texto_preview}")
        
    except Exception as e:
        print(f"  ❌ ERRO: {str(e)}")
    
    print()
    
    # ====================================================================
    # 4. VERIFICAR HASHTAGS
    # ====================================================================
    print("📊 [4/6] VERIFICANDO HASHTAGS")
    print("-" * 70)
    
    try:
        # Verificar se a tabela existe
        result = db.session.execute(text(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'hashtag'"
        )).scalar()
        
        if result == 0:
            print("  ❌ TABELA 'hashtag' NÃO EXISTE!")
            print("  ⚠️  Execute o script SQL: EXECUTAR_NO_BANCO.sql")
        else:
            total_hashtags = Hashtag.query.count()
            hashtags_usadas = Hashtag.query.filter(Hashtag.total_uso > 0).count()
            hashtags_semana = Hashtag.query.filter(Hashtag.uso_ultima_semana > 0).count()
            
            print(f"  ✓ Total de hashtags: {total_hashtags}")
            print(f"  ✓ Hashtags usadas: {hashtags_usadas}")
            print(f"  ✓ Hashtags ativas (última semana): {hashtags_semana}")
            
            if total_hashtags == 0:
                print("\n  ⚠️  NENHUMA HASHTAG CRIADA!")
                print("  → Crie posts com hashtags (ex: #matematica #enem)")
            else:
                # Top hashtags
                top_hashtags = Hashtag.query.order_by(Hashtag.total_uso.desc()).limit(5).all()
                print(f"\n  Top 5 hashtags:")
                for h in top_hashtags:
                    print(f"    • #{h.tag} → {h.total_uso} posts ({h.uso_ultima_semana} esta semana)")
        
    except Exception as e:
        print(f"  ❌ ERRO: {str(e)}")
        print(f"  ⚠️  Possível causa: Tabela 'hashtag' não existe")
        print(f"  → Execute: psql -U usuario -d banco -f EXECUTAR_NO_BANCO.sql")
    
    print()
    
    # ====================================================================
    # 5. VERIFICAR ASSOCIAÇÕES POST-HASHTAG
    # ====================================================================
    print("📊 [5/6] VERIFICANDO ASSOCIAÇÕES POST-HASHTAG")
    print("-" * 70)
    
    try:
        result = db.session.execute(text(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'post_hashtags'"
        )).scalar()
        
        if result == 0:
            print("  ❌ TABELA 'post_hashtags' NÃO EXISTE!")
        else:
            total_associacoes = db.session.execute(
                text("SELECT COUNT(*) FROM post_hashtags")
            ).scalar()
            
            print(f"  ✓ Total de associações: {total_associacoes}")
            
            if total_associacoes == 0:
                print("\n  ⚠️  NENHUMA ASSOCIAÇÃO CRIADA!")
                print("  → Posts existentes não têm hashtags extraídas")
                print("  → Execute: psql -U usuario -d banco -f processar_posts_existentes.sql")
            else:
                # Posts com mais hashtags
                posts_com_hashtags = db.session.execute(text("""
                    SELECT p.id, COUNT(ph.hashtag_id) as total
                    FROM post p
                    JOIN post_hashtags ph ON p.id = ph.post_id
                    GROUP BY p.id
                    ORDER BY total DESC
                    LIMIT 3
                """)).fetchall()
                
                print(f"\n  Posts com mais hashtags:")
                for row in posts_com_hashtags:
                    post = Post.query.get(row[0])
                    print(f"    • Post {row[0]}: {row[1]} hashtags")
        
    except Exception as e:
        print(f"  ❌ ERRO: {str(e)}")
    
    print()
    
    # ====================================================================
    # 6. TESTAR BUSCAS
    # ====================================================================
    print("📊 [6/6] TESTANDO BUSCAS")
    print("-" * 70)
    
    # Teste 1: Busca de usuários
    print("\n  Teste 1: Buscar usuários com 'a' no nome")
    try:
        usuarios_teste = User.query.filter(
            User.nome_completo.ilike('%a%'),
            User.is_active == True
        ).limit(3).all()
        
        print(f"    ✓ Encontrados: {len(usuarios_teste)} usuários")
        for u in usuarios_teste:
            print(f"      • {u.nome_completo or u.username}")
    except Exception as e:
        print(f"    ❌ ERRO: {str(e)}")
    
    # Teste 2: Busca de posts
    print("\n  Teste 2: Buscar posts com 'estud' no texto")
    try:
        posts_teste = Post.query.filter(
            Post.texto.ilike('%estud%'),
            Post.ativo == True
        ).limit(3).all()
        
        print(f"    ✓ Encontrados: {len(posts_teste)} posts")
        for p in posts_teste:
            texto_preview = p.texto[:40] + "..." if p.texto and len(p.texto) > 40 else p.texto
            print(f"      • Post {p.id}: {texto_preview}")
    except Exception as e:
        print(f"    ❌ ERRO: {str(e)}")
    
    # Teste 3: Busca de hashtags
    print("\n  Teste 3: Buscar hashtags com 'mat' no nome")
    try:
        hashtags_teste = Hashtag.query.filter(
            Hashtag.tag.ilike('%mat%')
        ).limit(3).all()
        
        print(f"    ✓ Encontradas: {len(hashtags_teste)} hashtags")
        for h in hashtags_teste:
            print(f"      • #{h.tag} ({h.total_uso} usos)")
    except Exception as e:
        print(f"    ❌ ERRO: {str(e)}")
        print(f"    ⚠️  Tabela 'hashtag' provavelmente não existe")
    
    print()
    print("=" * 70)
    print("DIAGNÓSTICO CONCLUÍDO")
    print("=" * 70)
    print()
    
    # ====================================================================
    # RECOMENDAÇÕES
    # ====================================================================
    print("📋 RECOMENDAÇÕES:")
    print("-" * 70)
    
    recomendacoes = []
    
    if total_usuarios == 0:
        recomendacoes.append("❌ Não há usuários no sistema - Registre usuários primeiro")
    
    if total_posts == 0:
        recomendacoes.append("❌ Não há posts - Crie posts para testar a busca")
    
    try:
        if Hashtag.query.count() == 0:
            recomendacoes.append("❌ Não há hashtags - Execute: EXECUTAR_NO_BANCO.sql")
    except:
        recomendacoes.append("❌ Tabela hashtag não existe - Execute: EXECUTAR_NO_BANCO.sql")
    
    try:
        total_assoc = db.session.execute(text("SELECT COUNT(*) FROM post_hashtags")).scalar()
        if total_assoc == 0 and total_posts > 0:
            recomendacoes.append("⚠️  Posts existem mas não têm hashtags - Execute: processar_posts_existentes.sql")
    except:
        recomendacoes.append("❌ Tabela post_hashtags não existe - Execute: EXECUTAR_NO_BANCO.sql")
    
    if not recomendacoes:
        print("  ✅ Sistema aparentemente está OK!")
        print("  → Se a busca não funciona no frontend, verifique:")
        print("    1. Logs do servidor: tail -f /var/log/launcher/app.log")
        print("    2. Console do navegador (F12)")
        print("    3. Template buscar.html está correto")
    else:
        for rec in recomendacoes:
            print(f"  {rec}")
    
    print()
    print("Para ver logs detalhados da busca:")
    print("  tail -f /var/log/launcher/app.log | grep BUSCA")
    print()
