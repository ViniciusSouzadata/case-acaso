-- T-205 (LLM): origem do rótulo de recusa por conversa ('regras' ou 'openrouter:<modelo>'), como já existe para o tema.
ALTER TABLE stg.conversa ADD COLUMN IF NOT EXISTS recusa_origem text;
