-- 014: campos opcionais do painel curto do achado: "O que vimos" e "Cuidado" em uma frase cada.
ALTER TABLE resultado.achado
    ADD COLUMN IF NOT EXISTS vimos_curto text,
    ADD COLUMN IF NOT EXISTS limite_curto text;
