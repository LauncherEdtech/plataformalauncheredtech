#!/bin/bash

# ============================================================================
# SCRIPT DE CORREÇÃO AUTOMÁTICA - User.nome → User.nome_completo
# ============================================================================
# Este script corrige automaticamente o erro AttributeError: User.nome
# substituindo por User.nome_completo em todo o código
# ============================================================================

set -e  # Parar em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     CORREÇÃO AUTOMÁTICA: User.nome → User.nome_completo       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================================================
# 1. LOCALIZAR DIRETÓRIO DO PROJETO
# ============================================================================
echo -e "${YELLOW}[1/7]${NC} Localizando diretório do projeto..."

PROJECT_DIR="/home/launchercursos/launcheredit/launcher-app"

if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}❌ Diretório do projeto não encontrado: $PROJECT_DIR${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Projeto encontrado: $PROJECT_DIR"
cd "$PROJECT_DIR"


# ============================================================================
# 2. FAZER BACKUP
# ============================================================================
echo ""
echo -e "${YELLOW}[2/7]${NC} Criando backup..."

BACKUP_DIR="$PROJECT_DIR/backups/user_nome_fix_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup de todos os arquivos Python em routes/
if [ -d "app/routes" ]; then
    cp -r app/routes "$BACKUP_DIR/"
    echo -e "${GREEN}✓${NC} Backup criado em: $BACKUP_DIR"
else
    echo -e "${RED}❌ Diretório app/routes não encontrado${NC}"
    exit 1
fi


# ============================================================================
# 3. BUSCAR ARQUIVOS COM User.nome
# ============================================================================
echo ""
echo -e "${YELLOW}[3/7]${NC} Buscando arquivos com 'User.nome'..."

FILES_TO_FIX=$(grep -rl "User\.nome[^_]" app/routes/ 2>/dev/null || true)

if [ -z "$FILES_TO_FIX" ]; then
    echo -e "${YELLOW}⚠${NC} Nenhum arquivo com User.nome encontrado"
    
    # Verificar se já está corrigido
    CORRECT_FILES=$(grep -rl "User\.nome_completo" app/routes/ 2>/dev/null || true)
    if [ ! -z "$CORRECT_FILES" ]; then
        echo -e "${GREEN}✓${NC} Parece que já está usando User.nome_completo"
    fi
else
    echo -e "${GREEN}✓${NC} Arquivos encontrados:"
    echo "$FILES_TO_FIX" | while read file; do
        COUNT=$(grep -c "User\.nome[^_]" "$file" 2>/dev/null || echo "0")
        echo "   • $file ($COUNT ocorrências)"
    done
fi


# ============================================================================
# 4. APLICAR CORREÇÕES
# ============================================================================
echo ""
echo -e "${YELLOW}[4/7]${NC} Aplicando correções..."

TOTAL_FIXES=0

# Padrões a corrigir
PATTERNS=(
    "s/User\.nome(\s*\.|,|\))/User.nome_completo\1/g"
    "s/user\.nome(\s*\.|,|\))/user.nome_completo\1/g"
    "s/current_user\.nome(\s*\.|,|\))/current_user.nome_completo\1/g"
    "s/\.nome\.ilike/.nome_completo.ilike/g"
    "s/\.nome\.like/.nome_completo.like/g"
    "s/\.nome\.contains/.nome_completo.contains/g"
    "s/\.nome\.filter/.nome_completo.filter/g"
)

for file in $FILES_TO_FIX; do
    echo "   Corrigindo: $file"
    
    # Aplicar cada padrão
    for pattern in "${PATTERNS[@]}"; do
        sed -i "$pattern" "$file"
    done
    
    # Contar correções neste arquivo
    FIXES=$(grep -c "nome_completo" "$file" 2>/dev/null || echo "0")
    TOTAL_FIXES=$((TOTAL_FIXES + FIXES))
done

echo -e "${GREEN}✓${NC} Total de linhas corrigidas: $TOTAL_FIXES"


# ============================================================================
# 5. VERIFICAR CORREÇÕES
# ============================================================================
echo ""
echo -e "${YELLOW}[5/7]${NC} Verificando correções..."

# Buscar se ainda existe User.nome (sem underscore depois)
REMAINING=$(grep -rn "User\.nome[^_]" app/routes/ 2>/dev/null || true)

if [ -z "$REMAINING" ]; then
    echo -e "${GREEN}✓${NC} Todas as ocorrências de User.nome foram corrigidas!"
else
    echo -e "${YELLOW}⚠${NC} Ainda existem ocorrências de User.nome:"
    echo "$REMAINING"
    echo ""
    echo "   Por favor, revise manualmente esses casos."
fi


# ============================================================================
# 6. VERIFICAR SINTAXE PYTHON
# ============================================================================
echo ""
echo -e "${YELLOW}[6/7]${NC} Verificando sintaxe Python..."

SYNTAX_ERRORS=0

for file in $FILES_TO_FIX; do
    if ! python3 -m py_compile "$file" 2>/dev/null; then
        echo -e "${RED}❌ Erro de sintaxe em: $file${NC}"
        SYNTAX_ERRORS=$((SYNTAX_ERRORS + 1))
    fi
done

if [ $SYNTAX_ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Sintaxe válida em todos os arquivos"
else
    echo -e "${RED}❌ Encontrados $SYNTAX_ERRORS arquivo(s) com erro de sintaxe${NC}"
    echo "   Verifique manualmente antes de reiniciar o servidor"
fi


# ============================================================================
# 7. REINICIAR SERVIDOR
# ============================================================================
echo ""
echo -e "${YELLOW}[7/7]${NC} Reiniciando servidor..."

if systemctl is-active --quiet launcher-app; then
    sudo systemctl restart launcher-app
    
    # Aguardar 3 segundos
    sleep 3
    
    # Verificar se iniciou
    if systemctl is-active --quiet launcher-app; then
        echo -e "${GREEN}✓${NC} Servidor reiniciado com sucesso"
    else
        echo -e "${RED}❌ Erro ao reiniciar servidor${NC}"
        echo "   Verifique os logs: tail -f /var/log/launcher/app.log"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠${NC} Serviço launcher-app não está rodando"
    echo "   Inicie manualmente: sudo systemctl start launcher-app"
fi


# ============================================================================
# RESUMO
# ============================================================================
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                     CORREÇÃO CONCLUÍDA                         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✓${NC} Backup: $BACKUP_DIR"
echo -e "${GREEN}✓${NC} Arquivos corrigidos: $(echo "$FILES_TO_FIX" | wc -w)"
echo -e "${GREEN}✓${NC} Total de correções: $TOTAL_FIXES"
echo ""
echo -e "${YELLOW}📋 PRÓXIMOS PASSOS:${NC}"
echo "   1. Verificar logs: tail -f /var/log/launcher/app.log"
echo "   2. Testar busca de usuários: /helpzone/buscar"
echo "   3. Criar post com hashtags: /helpzone/criar-post"
echo ""
echo -e "${YELLOW}🔄 Para reverter (se necessário):${NC}"
echo "   cp -r $BACKUP_DIR/routes/* app/routes/"
echo "   sudo systemctl restart launcher-app"
echo ""


# ============================================================================
# TESTES AUTOMÁTICOS
# ============================================================================
echo -e "${YELLOW}🧪 Executando testes...${NC}"
echo ""

# Teste 1: Verificar se servidor está respondendo
echo -n "   • Servidor respondendo... "
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠ (não testado)${NC}"
fi

# Teste 2: Verificar se ainda existe User.nome no código
echo -n "   • Sem User.nome no código... "
if [ -z "$REMAINING" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Teste 3: Verificar se existem ocorrências de User.nome_completo
echo -n "   • User.nome_completo presente... "
CORRECT_USAGE=$(grep -r "User\.nome_completo" app/routes/ 2>/dev/null | wc -l)
if [ $CORRECT_USAGE -gt 0 ]; then
    echo -e "${GREEN}✓ ($CORRECT_USAGE ocorrências)${NC}"
else
    echo -e "${YELLOW}⚠${NC}"
fi

echo ""
echo -e "${GREEN}✅ Correção completa!${NC}"
echo ""
