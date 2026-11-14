import { consultar } from "../db";

export interface Achado {
  ordem: number;
  titulo: string;
  evidencia: string;
  decisao: string;
  limite: string;
  numero_destaque: string | null;
  rotulo_destaque: string | null;
  acao_curta: string | null;
  tecnico: string | null;
  vimos_curto: string | null;
  limite_curto: string | null;
}

export async function achados() {
  return consultar<Achado>(`SELECT ordem, titulo, evidencia, decisao, limite, numero_destaque, rotulo_destaque, acao_curta, tecnico, vimos_curto, limite_curto FROM resultado.achado ORDER BY ordem`);
}

export interface LoteQualidade {
  lote_id: number;
  iniciado_em: string;
  terminado_em: string | null;
  fonte: string | null;
  linhas_lidas: number | null;
  linhas_gravadas: number | null;
  linhas_rejeitadas: number | null;
  versao_definicao: string | null;
  status: string;
}

export interface Reconciliacao {
  metrica: string;
  valor_bruto: number | null;
  valor_mart: number | null;
  diferenca: number | null;
  tolerancia: number | null;
  ok: boolean;
}

export interface Problema {
  problema: string;
  contagem: number;
  percentual: number | null;
  tratamento: string | null;
}

export interface Validacao {
  classificador: string;
  n: number;
  acuracia: number | null;
  kappa: number | null;
  detalhe_json: unknown;
  versao_prompt: string | null;
  modelo: string | null;
}

/** Último lote com sucesso + reconciliação desse lote + problemas + validação do classificador. Só agregados. */
export async function qualidade() {
  const lote = await consultar<LoteQualidade>(
    `SELECT lote_id, iniciado_em::text AS iniciado_em, terminado_em::text AS terminado_em, fonte,
            linhas_lidas, linhas_gravadas, linhas_rejeitadas, versao_definicao, status
       FROM ops.lote_carga WHERE status = 'sucesso' ORDER BY lote_id DESC LIMIT 1`,
  );
  const loteId = lote.linhas[0]?.lote_id ?? null;
  const [rec, prob, val] = await Promise.all([
    consultar<Reconciliacao>(
      `SELECT metrica, valor_bruto, valor_mart, diferenca, tolerancia, ok
         FROM ops.reconciliacao WHERE lote_id = $1 ORDER BY metrica`,
      [loteId],
    ),
    consultar<Problema>(
      `SELECT problema, contagem, percentual, tratamento FROM resultado.problema_qualidade ORDER BY contagem DESC, problema`,
    ),
    consultar<Validacao>(
      `SELECT classificador, n, acuracia, kappa, detalhe_json, versao_prompt, modelo
         FROM resultado.validacao_classificador ORDER BY classificador`,
    ),
  ]);
  return {
    lote: lote.linhas[0] ?? null,
    reconciliacao: rec.linhas,
    problemas: prob.linhas,
    validacao: val.linhas,
    ms: lote.ms + rec.ms + prob.ms + val.ms,
  };
}
