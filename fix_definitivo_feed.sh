#!/bin/bash
# ================================================
# FIX DEFINITIVO - BASEADO NO MODELO REAL
# ================================================

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   FIX DEFINITIVO: Correções no Template Feed      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

BASE_DIR="/home/launchercursos/launcheredit/launcher-app"
FEED_FILE="$BASE_DIR/app/templates/helpzone/feed.html"

# Verificar se arquivo existe
if [ ! -f "$FEED_FILE" ]; then
    echo -e "${RED}❌ Arquivo feed.html não encontrado!${NC}"
    exit 1
fi

# Criar backup
BACKUP_FILE="$FEED_FILE.backup.definitivo.$(date +%Y%m%d_%H%M%S)"
cp "$FEED_FILE" "$BACKUP_FILE"
echo -e "${GREEN}✅ Backup criado: $BACKUP_FILE${NC}"
echo ""

echo -e "${YELLOW}📝 Aplicando correções baseadas no modelo real...${NC}"
echo ""

# Correção 1: post.usuario → post.user
echo "1️⃣  Corrigindo: post.usuario → post.user"
COUNT1=$(grep -c "post\.usuario" "$FEED_FILE" 2>/dev/null || echo "0")
sed -i 's/post\.usuario/post.user/g' "$FEED_FILE"
echo "   ✅ $COUNT1 substituições"

# Correção 2: post.conteudo → post.texto  
echo "2️⃣  Corrigindo: post.conteudo → post.texto"
COUNT2=$(grep -c "post\.conteudo" "$FEED_FILE" 2>/dev/null || echo "0")
sed -i 's/post\.conteudo/post.texto/g' "$FEED_FILE"
echo "   ✅ $COUNT2 substituições"

# Correção 3: post.imagem_url → verificar se existe no modelo
echo "3️⃣  Verificando campos de mídia..."
if grep -q "post\.imagem_url" "$FEED_FILE"; then
    echo "   ⚠️  Campo 'imagem_url' encontrado no template"
    echo "   💡 No modelo real, mídia está em post.midia.url"
    echo "   📝 Substituindo post.imagem_url → post.midia.url (se existir)"
    sed -i 's/post\.imagem_url/post.midia.url/g' "$FEED_FILE"
fi

# Correção 4: post.total_curtidas → post.total_likes
echo "4️⃣  Corrigindo: post.total_curtidas → post.total_likes"
COUNT4=$(grep -c "post\.total_curtidas" "$FEED_FILE" 2>/dev/null || echo "0")
sed -i 's/post\.total_curtidas/post.total_likes/g' "$FEED_FILE"
echo "   ✅ $COUNT4 substituições"

# Correção 5: post.visualizacoes → campo não existe no modelo
echo "5️⃣  Removendo referências a 'visualizacoes' (campo não existe)"
sed -i 's/<i class="fas fa-eye"><\/i>[[:space:]]*<span>{{ post\.visualizacoes or 0 }} visualizações<\/span>//g' "$FEED_FILE"

# Correção 6: post.hashtags → campo não existe no modelo
echo "6️⃣  Verificando campo 'hashtags'..."
if grep -q "post\.hashtags" "$FEED_FILE"; then
    echo "   ⚠️  Campo 'hashtags' não existe no modelo"
    echo "   💡 Comentando seção de hashtags"
    # Comentar bloco de hashtags
    sed -i '/{% if post\.hashtags %}/,/{% endif %}/s/^/<!-- /' "$FEED_FILE"
    sed -i '/{% if post\.hashtags %}/,/{% endif %}/s/$/ -->/' "$FEED_FILE"
fi

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}📊 RESUMO DAS CORREÇÕES${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "✅ post.usuario → post.user: $COUNT1 correções"
echo "✅ post.conteudo → post.texto: $COUNT2 correções"
echo "✅ post.total_curtidas → post.total_likes: $COUNT4 correções"
echo "✅ Campos de mídia atualizados"
echo "✅ Campos inexistentes removidos/comentados"
echo ""

# Verificar resultado
echo -e "${YELLOW}🔍 Verificando correções...${NC}"
ERROS=0

if grep -q "post\.usuario" "$FEED_FILE"; then
    echo -e "${RED}⚠️  Ainda existem 'post.usuario' no arquivo${NC}"
    ERROS=$((ERROS + 1))
else
    echo -e "${GREEN}✅ Nenhum 'post.usuario' encontrado${NC}"
fi

if grep -q "post\.conteudo" "$FEED_FILE"; then
    echo -e "${RED}⚠️  Ainda existem 'post.conteudo' no arquivo${NC}"
    ERROS=$((ERROS + 1))
else
    echo -e "${GREEN}✅ Nenhum 'post.conteudo' encontrado${NC}"
fi

echo ""

if [ $ERROS -eq 0 ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ TODAS AS CORREÇÕES APLICADAS COM SUCESSO!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
else
    echo -e "${YELLOW}⚠️  Algumas correções podem precisar de revisão manual${NC}"
fi

echo ""

# Perguntar se quer reiniciar
echo -e "${YELLOW}🔄 Deseja reiniciar a aplicação agora? (s/n)${NC}"
read -r resposta

if [ "$resposta" = "s" ] || [ "$resposta" = "S" ]; then
    echo "🔄 Reiniciando launcher..."
    sudo systemctl restart launcher
    
    echo "⏳ Aguardando 3 segundos..."
    sleep 3
    
    if systemctl is-active --quiet launcher; then
        echo -e "${GREEN}✅ Launcher reiniciado com sucesso!${NC}"
        
        # Verificar logs
        echo ""
        echo "📋 Últimas linhas do log:"
        sudo journalctl -u launcher -n 10 --no-pager
        
    else
        echo -e "${RED}❌ Erro ao reiniciar launcher!${NC}"
        echo "Verificar logs: sudo journalctl -u launcher -n 50"
    fi
else
    echo "⚠️  Lembre-se de reiniciar manualmente:"
    echo "   sudo systemctl restart launcher"
fi

echo ""
echo "================================================"
echo -e "${GREEN}🎉 FIX CONCLUÍDO!${NC}"
echo "================================================"
echo ""
echo "📋 Teste agora:"
echo "   Acesse: https://plataformalauncher.com.br/helpzone/feed"
echo ""
echo "📂 Backup salvo em:"
echo "   $BACKUP_FILE"
echo ""
echo "↩️  Para reverter (se necessário):"
echo "   cp $BACKUP_FILE $FEED_FILE"
echo "   sudo systemctl restart launcher"
echo ""
