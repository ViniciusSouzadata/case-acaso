-- 012: campos opcionais do cartão curto de achado (Tela 2). Texto longo aprovado (evidencia/decisao/limite) não muda.
ALTER TABLE resultado.achado
    ADD COLUMN IF NOT EXISTS numero_destaque text,
    ADD COLUMN IF NOT EXISTS rotulo_destaque text,
    ADD COLUMN IF NOT EXISTS acao_curta      text;
