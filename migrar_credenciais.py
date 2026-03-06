#!/usr/bin/env python3
"""
migrar_credenciais.py  v3
=========================
Substitui credenciais hardcoded nos arquivos da aplicação.
Usa substituições simples de string — sem regex, sem surpresas.

USO:
    python migrar_credenciais.py             # preview (não altera nada)
    python migrar_credenciais.py --aplicar   # aplica com backup automático
    python migrar_credenciais.py --reverter  # desfaz o último backup gerado
"""

import os, sys, shutil, argparse, difflib
from pathlib import Path
from datetime import datetime

ROOT       = Path(__file__).parent.resolve()
TIMESTAMP  = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_DIR = ROOT / f"backups/migrar_credenciais_{TIMESTAMP}"

# ─────────────────────────────────────────────────────────────────────────────
# PLANO DE SUBSTITUIÇÕES
# Cada entrada: (arquivo_relativo, [(string_antiga, string_nova), ...])
# As strings são exatas — o que você vê é o que será substituído.
# ─────────────────────────────────────────────────────────────────────────────
PLANO = [

    # ── app/__init__.py ───────────────────────────────────────────────────────
    ("app/__init__.py", [
        (
            'db_host = os.environ.get("DB_HOST", "34.63.141.69")',
            'db_host = os.environ.get("DB_HOST", "")',
        ),
        (
            'db_name = os.environ.get("DB_NAME", "plataforma")',
            'db_name = os.environ.get("DB_NAME", "")',
        ),
        (
            'db_user = os.environ.get("DB_USER", "postgres")',
            'db_user = os.environ.get("DB_USER", "")',
        ),
        (
            'db_password = os.environ.get("DB_PASSWORD", "22092021Dd$")',
            'db_password = os.environ.get("DB_PASSWORD", "")',
        ),
    ]),

    # ── app/config.py ─────────────────────────────────────────────────────────
    ("app/config.py", [
        (
            "DB_HOST = '34.63.141.69'",
            "DB_HOST = os.environ.get('DB_HOST', '')",
        ),
        (
            "DB_PORT = '5432'",
            "DB_PORT = os.environ.get('DB_PORT', '5432')",
        ),
        (
            "DB_NAME = 'plataforma'",
            "DB_NAME = os.environ.get('DB_NAME', '')",
        ),
        (
            "DB_USER = 'postgres'",
            "DB_USER = os.environ.get('DB_USER', '')",
        ),
        (
            "DB_PASSWORD = '22092021Dd$'",
            "DB_PASSWORD = os.environ.get('DB_PASSWORD', '')",
        ),
    ]),

    # ── config.py (raiz) ──────────────────────────────────────────────────────
    ("config.py", [
        (
            "os.environ.get('DATABASE_URL') or 'postgresql://postgres:22092021Dd$@34.63.141.69:5432/plataforma'",
            "os.environ.get('DATABASE_URL')",
        ),
        (
            "'postgresql://postgres:22092021Dd$@34.63.141.69:5432/plataforma'",
            "os.environ.get('DATABASE_URL')",
        ),
    ]),

    # ── app/routes/__init__.py ────────────────────────────────────────────────
    ("app/routes/__init__.py", [
        (
            "app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:22092021Dd$@34.63.141.69:5432/plataforma'",
            "app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')",
        ),
    ]),

    # ── app/routes/simulados.py ───────────────────────────────────────────────
    ("app/routes/simulados.py", [
        # Bloco com import psycopg2 inline (indentação 8 espaços)
        (
            "import psycopg2\n        conn = psycopg2.connect(\n            host='34.63.141.69',\n            user='postgres',\n            password='22092021Dd$',\n            database='plataforma'\n        )",
            "from app.services.db_utils import get_connection\n        conn = get_connection()",
        ),
        # Bloco com indentação 12 espaços (dentro de try aninhado)
        (
            "conn = psycopg2.connect(\n                host='34.63.141.69',\n                user='postgres',\n                password='22092021Dd$',\n                database='plataforma'\n            )",
            "from app.services.db_utils import get_connection\n            conn = get_connection()",
        ),
        # Bloco com indentação 8 espaços sem import
        (
            "conn = psycopg2.connect(\n            host='34.63.141.69',\n            user='postgres',\n            password='22092021Dd$',\n            database='plataforma'\n        )",
            "from app.services.db_utils import get_connection\n        conn = get_connection()",
        ),
    ]),

    # ── app/services/gerador_questoes.py ──────────────────────────────────────
    ("app/services/gerador_questoes.py", [
        (
            "    def __init__(self):\n        self.conn_params = {\n            'host': '34.63.141.69',\n            'port': '5432',\n            'database': 'plataforma',\n            'user': 'postgres',\n            'password': '22092021Dd$'\n        }",
            "    def __init__(self):\n        pass  # credenciais via DATABASE_URL",
        ),
        (
            "        return psycopg2.connect(**self.conn_params)",
            "        from app.services.db_utils import get_connection\n        return get_connection()",
        ),
    ]),

    # ── app/services/gerador_questoes_v2.py ───────────────────────────────────
    ("app/services/gerador_questoes_v2.py", [
        (
            "    def __init__(self):\n        self.conn_params = {\n            'host': '34.63.141.69',\n            'port': '5432',\n            'database': 'plataforma',\n            'user': 'postgres',\n            'password': '22092021Dd$'\n        }",
            "    def __init__(self):\n        pass  # credenciais via DATABASE_URL",
        ),
        (
            "        return psycopg2.connect(**self.conn_params)",
            "        from app.services.db_utils import get_connection\n        return get_connection()",
        ),
    ]),

    # ── app/services/questoes_service.py ──────────────────────────────────────
    # Substitui o dict DB_PARAMS inteiro por uma chamada ao db_utils
    ("app/services/questoes_service.py", [
        (
            "DB_PARAMS = {\n    'host': '34.63.141.69',\n    'port': '5432',\n    'database': 'plataforma',\n    'user': 'postgres',\n    'password': '22092021Dd$'\n}",
            "# DB_PARAMS removido — usar db_utils.get_db_params() ou get_connection()\nfrom app.services.db_utils import get_db_params, get_connection\nDB_PARAMS = get_db_params()",
        ),
        # Variação com dbname em vez de database
        (
            "DB_PARAMS = {\n    'host': '34.63.141.69',\n    'port': '5432',\n    'dbname': 'plataforma',\n    'user': 'postgres',\n    'password': '22092021Dd$'\n}",
            "# DB_PARAMS removido — usar db_utils.get_db_params() ou get_connection()\nfrom app.services.db_utils import get_db_params, get_connection\nDB_PARAMS = get_db_params()",
        ),
        # psycopg2.connect direto com DB_PARAMS
        (
            "psycopg2.connect(**DB_PARAMS)",
            "get_connection()",
        ),
        # psycopg2.connect inline sem variável
        (
            "psycopg2.connect(\n    host='34.63.141.69',\n    user='postgres',\n    password='22092021Dd$',\n    database='plataforma'\n)",
            "get_connection()",
        ),
    ]),

    # ── app/templates/redacao/arquivosRedacaoGCP/config.py ───────────────────
    ("app/templates/redacao/arquivosRedacaoGCP/config.py", [
        (
            "'postgresql://postgres:22092021Dd$@34.63.141.69:5432/plataforma'",
            "os.environ.get('DATABASE_URL')",
        ),
    ]),
]

# ─────────────────────────────────────────────────────────────────────────────
# Utilitários
# ─────────────────────────────────────────────────────────────────────────────

def ler(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"  ⚠️  Não foi possível ler {path}: {e}")
        return None

def diff_texto(nome, antes, depois):
    linhas = list(difflib.unified_diff(
        antes.splitlines(keepends=True),
        depois.splitlines(keepends=True),
        fromfile=f"a/{nome}",
        tofile=f"b/{nome}",
        n=2,
    ))
    if len(linhas) > 80:
        return "".join(linhas[:80]) + f"\n  ... ({len(linhas)-80} linhas omitidas)\n"
    return "".join(linhas)

def backup(arquivo):
    rel  = arquivo.relative_to(ROOT)
    dest = BACKUP_DIR / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(arquivo, dest)

def reverter_ultimo():
    bkp_root   = ROOT / "backups"
    candidatos = sorted(bkp_root.glob("migrar_credenciais_*"), reverse=True)
    if not candidatos:
        print("❌  Nenhum backup encontrado em backups/")
        sys.exit(1)
    ultimo = candidatos[0]
    print(f"↩️  Revertendo: {ultimo.name}\n")
    restaurados = 0
    for bkp in ultimo.rglob("*.py"):
        rel = bkp.relative_to(ultimo)
        shutil.copy2(bkp, ROOT / rel)
        print(f"  ✅  {rel}")
        restaurados += 1
    print(f"\n✅  {restaurados} arquivo(s) restaurado(s).")

# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--aplicar",  action="store_true", help="Aplica as mudanças")
    parser.add_argument("--reverter", action="store_true", help="Reverte o último backup")
    args = parser.parse_args()

    if args.reverter:
        reverter_ultimo()
        return

    modo = "APLICANDO" if args.aplicar else "PREVIEW  (use --aplicar para efetivar)"
    print(f"\n{'='*62}\n  {modo}\n  Raiz: {ROOT}\n{'='*62}\n")

    total_subs     = 0
    total_arqs     = 0
    arquivos_novos = {}   # rel_path -> conteúdo novo (para verificação pós-aplicação)

    for rel_path, subs in PLANO:
        arq = ROOT / rel_path
        if not arq.exists():
            print(f"⚪  {rel_path} — não encontrado, pulando.\n")
            continue

        original = ler(arq)
        if original is None:
            continue

        novo    = original
        feitos  = []
        pulados = []

        for antes, depois in subs:
            if antes in novo:
                novo = novo.replace(antes, depois)
                feitos.append(antes[:70].replace("\n", "↵"))
            else:
                pulados.append(antes[:70].replace("\n", "↵"))

        if feitos:
            print(f"📄  {rel_path}")
            for f in feitos:
                print(f"    ✅  {f}...")
            for p in pulados:
                print(f"    ⚪  não encontrado (já ok?): {p}...")
            print()
            print(diff_texto(rel_path, original, novo))
            print()
            total_subs += len(feitos)
            total_arqs += 1
            arquivos_novos[rel_path] = novo

            if args.aplicar:
                backup(arq)
                arq.write_text(novo, encoding="utf-8")
        else:
            print(f"✅  {rel_path} — já limpo.\n")

    # ── Verificação final ─────────────────────────────────────────────────────
    RESIDUOS = ["34.63.141.69", "22092021Dd$"]
    print(f"\n{'='*62}")
    if args.aplicar:
        print("  VERIFICAÇÃO FINAL — lendo arquivos já modificados")
    else:
        print("  VERIFICAÇÃO FINAL — simulando resultado após --aplicar")
    print(f"{'='*62}")

    tem_residuo = False
    for rel_path, _ in PLANO:
        arq = ROOT / rel_path
        if not arq.exists():
            continue

        # Em preview usa o conteúdo simulado; em aplicar lê o arquivo real
        if args.aplicar:
            conteudo = ler(arq) or ""
        else:
            conteudo = arquivos_novos.get(rel_path, ler(arq) or "")

        encontrados = [r for r in RESIDUOS if r in conteudo]
        if encontrados:
            print(f"  ⚠️  {rel_path} → resíduo: {encontrados}")
            tem_residuo = True
        else:
            print(f"  ✅  {rel_path}")

    # ── Resumo ────────────────────────────────────────────────────────────────
    print()
    if total_subs == 0:
        print("✅  Todos os arquivos já estavam limpos!")
    elif args.aplicar:
        if not tem_residuo:
            print(f"✅  {total_subs} substituição(ões) em {total_arqs} arquivo(s). Tudo limpo!")
        else:
            print(f"⚠️  {total_subs} substituição(ões) aplicadas, mas ainda há resíduos.")
            print(f"   Verifique os arquivos marcados com ⚠️  acima.")
        print(f"\n📦  Backups: backups/migrar_credenciais_{TIMESTAMP}/")
        print(f"   Reverter: python migrar_credenciais.py --reverter")
    else:
        if not tem_residuo:
            print(f"👀  {total_subs} substituição(ões) em {total_arqs} arquivo(s).")
            print(f"   Resultado simulado está limpo. Rode --aplicar para efetivar.")
        else:
            print(f"👀  {total_subs} substituição(ões) encontradas, mas ainda sobraria resíduo.")
            print(f"   Verifique os ⚠️  acima antes de aplicar.")
    print(f"{'='*62}\n")

if __name__ == "__main__":
    main()
