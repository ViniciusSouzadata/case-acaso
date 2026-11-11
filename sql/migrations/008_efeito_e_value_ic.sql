-- T-206: E-value também para o limite do intervalo de confiança mais próximo de 1 (acréscimo; o contrato de efeito_fator não muda para quem lê).
ALTER TABLE resultado.efeito_fator ADD COLUMN e_value_ic numeric;
