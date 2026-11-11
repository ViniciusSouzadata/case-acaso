-- T-303: a tela de Qualidade dos dados mostra a reconciliação bruto x marts (só contagens por métrica, nada sensível).
-- Acrescenta SELECT em ops.reconciliacao ao app_ro. ops.parametros e ops.rejeitado seguem sem acesso.
GRANT SELECT ON ops.reconciliacao TO app_ro;
