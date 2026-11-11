-- T-103: tabelas de operação.
CREATE TABLE ops.parametros (
    chave     text PRIMARY KEY,
    valor     text NOT NULL,
    descricao text
);

INSERT INTO ops.parametros (chave, valor, descricao) VALUES
    ('versao_definicao',     '1.0.0',             'Versão das definições de sessão, usuário e retenção'),
    ('gap_sessao_min',       '30',                'Minutos de inatividade que encerram uma sessão'),
    ('janela_retorno_horas', '168',               'Janela (horas) para contar o retorno do usuário'),
    ('burn_in_dias',         '14',                'Dias iniciais da base excluídos como burn-in'),
    ('n_minimo',             '30',                'Tamanho mínimo de grupo para exibir uma taxa'),
    ('limiar_conversas_ip',  '200',               'Conversas por IP acima do qual o tráfego é anômalo'),
    ('limiar_uas_ip',        '10',                'User-agents distintos por IP acima do qual o tráfego é anômalo'),
    ('fuso_pais',            'America/Sao_Paulo', 'Fuso padrão para agrupar por dia/hora local');

CREATE TABLE ops.lote_carga (
    lote_id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    iniciado_em       timestamptz NOT NULL DEFAULT now(),
    terminado_em      timestamptz,
    fonte             text,
    sha256            text,
    linhas_lidas      integer,
    linhas_gravadas   integer,
    linhas_rejeitadas integer,
    versao_definicao  text,
    status            text NOT NULL DEFAULT 'em_andamento',
    erro              text
);

CREATE TABLE ops.rejeitado (
    lote_id     bigint NOT NULL REFERENCES ops.lote_carga (lote_id),
    conversa_id bigint,
    motivo      text NOT NULL
);

CREATE TABLE ops.reconciliacao (
    lote_id     bigint NOT NULL REFERENCES ops.lote_carga (lote_id),
    metrica     text NOT NULL,
    valor_bruto numeric,
    valor_mart  numeric,
    diferenca   numeric,
    tolerancia  numeric,
    ok          boolean NOT NULL
);

-- app_ro lê só o lote (para "dados atualizados em"); precisa de USAGE no esquema ops.
GRANT USAGE ON SCHEMA ops TO app_ro;
GRANT SELECT ON ops.lote_carga TO app_ro;
