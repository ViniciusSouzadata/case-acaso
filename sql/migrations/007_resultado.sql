-- T-201: tabelas do esquema resultado (contrato: .specs/features/m2-analise/design.md). Só agregados; nada de conversa, IP ou user-agent.
-- A permissão de leitura do app_ro vem dos privilégios padrão do esquema (migração 001).

CREATE TABLE resultado.meta (
    versao_analise                    text NOT NULL,
    versao_definicao                  text NOT NULL,
    executado_em                      timestamptz NOT NULL,
    n_elegiveis                       integer NOT NULL,
    n_retornos                        integer NOT NULL,
    taxa_global                       numeric NOT NULL,
    ic_inf                            numeric NOT NULL,
    ic_sup                            numeric NOT NULL,
    efeito_minimo_detectavel_pp       numeric NOT NULL,  -- divisão 50/50 (contrato)
    efeito_minimo_detectavel_15_85_pp numeric NOT NULL,  -- acréscimo da T-201: grupo de 15% contra 85%
    parametros_modelo                 integer            -- T-204: quantos parâmetros entraram no modelo ajustado
);

CREATE TABLE resultado.efeito_fator (
    fator               text NOT NULL,
    nivel               text NOT NULL,
    referencia          text NOT NULL,
    grupo               text NOT NULL CHECK (grupo IN ('assistente', 'perfil', 'engajamento')),
    n_nivel             integer NOT NULL,
    n_referencia        integer NOT NULL,
    taxa_nivel          numeric,
    taxa_referencia     numeric,
    efeito_bruto_pp     numeric,
    bruto_ic_inf        numeric,
    bruto_ic_sup        numeric,
    efeito_ajustado_pp  numeric,
    ajustado_ic_inf     numeric,
    ajustado_ic_sup     numeric,
    p_valor             numeric,
    significativo_fdr   boolean,
    e_value             numeric,
    metodo              text NOT NULL CHECK (metodo IN ('logit_ame', 'ipw')),
    amostra_suficiente  boolean NOT NULL,
    leitura             text,
    ordem               integer,
    PRIMARY KEY (fator, nivel, metodo)
);

CREATE TABLE resultado.balanco_propensao (
    tratamento text NOT NULL,
    covariavel text NOT NULL,
    dp_antes   numeric,
    dp_depois  numeric
);

CREATE TABLE resultado.decomposicao_semana (
    semana         date NOT NULL,
    segmento       text NOT NULL,
    peso_base      numeric,
    peso_semana    numeric,
    taxa_base      numeric,
    taxa_semana    numeric,
    efeito_mix_pp  numeric,
    efeito_taxa_pp numeric
);

CREATE TABLE resultado.decomposicao_resumo (
    semana          date NOT NULL,
    base_descricao  text,
    n_base          integer,
    n_semana        integer,
    taxa_base       numeric,
    taxa_semana     numeric,
    delta_pp        numeric,
    mix_pp          numeric,
    taxa_pp         numeric,
    p_valor         numeric,
    conclusao       text
);

CREATE TABLE resultado.sensibilidade_efeito (
    definicao           text NOT NULL,
    fator               text NOT NULL,
    nivel               text NOT NULL,
    efeito_ajustado_pp  numeric,
    ic_inf              numeric,
    ic_sup              numeric,
    mesmo_sinal         boolean
);

CREATE TABLE resultado.validacao_classificador (
    classificador  text NOT NULL,
    n              integer NOT NULL,
    acuracia       numeric,
    kappa          numeric,
    detalhe_json   jsonb,
    versao_prompt  text,
    modelo         text
);

CREATE TABLE resultado.achado (
    ordem     integer PRIMARY KEY,
    titulo    text NOT NULL,
    evidencia text NOT NULL,
    decisao   text NOT NULL,
    limite    text NOT NULL
);

CREATE TABLE resultado.problema_qualidade (
    problema   text PRIMARY KEY,
    contagem   integer NOT NULL,
    percentual numeric,
    tratamento text
);

GRANT SELECT ON ALL TABLES IN SCHEMA resultado TO app_ro;
