-- 013: campo opcional do detalhe técnico do achado (bloco recolhido "Para conferir (técnico)" na Tela 2).
ALTER TABLE resultado.achado
    ADD COLUMN IF NOT EXISTS tecnico text;
