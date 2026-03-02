# migrations_s3_helpzone.sql
-- Migração para adicionar suporte ao S3 no HelpZone Social
-- Execute este SQL no PostgreSQL

-- 1. Adicionar campo s3_key na tabela post_midia
ALTER TABLE post_midia 
ADD COLUMN IF NOT EXISTS s3_key VARCHAR(500);

-- 2. Adicionar índice para busca rápida por s3_key
CREATE INDEX IF NOT EXISTS idx_post_midia_s3_key ON post_midia(s3_key);

-- 3. Adicionar campo s3_key na tabela story (substituindo url_midia)
ALTER TABLE story 
ADD COLUMN IF NOT EXISTS s3_key VARCHAR(500);

-- 4. Adicionar índice para busca rápida por s3_key
CREATE INDEX IF NOT EXISTS idx_story_s3_key ON story(s3_key);

-- 5. Comentários para documentação
COMMENT ON COLUMN post_midia.s3_key IS 'Chave S3 do arquivo de mídia armazenado na AWS';
COMMENT ON COLUMN story.s3_key IS 'Chave S3 do arquivo de story armazenado na AWS';

-- 6. Verificar se as tabelas existem e criar se necessário
-- (só execute se ainda não tiver rodado as migrations principais)

-- NOTA: O campo url_midia em post_midia e story pode ser mantido para compatibilidade
-- ou pode ser removido após migração completa para S3
-- Para remover: ALTER TABLE post_midia DROP COLUMN IF EXISTS url_midia;
-- Para remover: ALTER TABLE story DROP COLUMN IF EXISTS url_midia;
