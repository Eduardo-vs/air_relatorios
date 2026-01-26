-- Migração: Adicionar novas colunas às tabelas existentes
-- Execute este script no seu banco PostgreSQL

-- ========================================
-- TABELA: influenciadores
-- ========================================

-- Adicionar coluna vinculo_id (para vincular contas de diferentes redes)
ALTER TABLE influenciadores ADD COLUMN IF NOT EXISTS vinculo_id INTEGER;

-- Adicionar coluna categoria (para categorizar influenciadores)
ALTER TABLE influenciadores ADD COLUMN IF NOT EXISTS categoria TEXT;

-- Adicionar coluna profile_id (ID do perfil no AIR)
ALTER TABLE influenciadores ADD COLUMN IF NOT EXISTS profile_id TEXT;

-- ========================================
-- TABELA: campanhas
-- ========================================

-- Adicionar coluna top_conteudos (JSON com top 3 conteúdos)
ALTER TABLE campanhas ADD COLUMN IF NOT EXISTS top_conteudos TEXT;

-- Adicionar coluna colunas_personalizadas (JSON com config de colunas extras)
ALTER TABLE campanhas ADD COLUMN IF NOT EXISTS colunas_personalizadas TEXT;

-- ========================================
-- VERIFICAÇÃO
-- ========================================

-- Verificar se as colunas foram adicionadas
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'influenciadores' 
AND column_name IN ('vinculo_id', 'categoria', 'profile_id');

SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'campanhas' 
AND column_name IN ('top_conteudos', 'colunas_personalizadas');
