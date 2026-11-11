import { consultar } from "../db";

export interface EfeitoFator {
  fator: string;
  nivel: string;
  referencia: string;
  grupo: "assistente" | "perfil" | "engajamento";
  n_nivel: number;
  n_referencia: number;
  taxa_nivel: number | null;
  taxa_referencia: number | null;
  efeito_bruto_pp: number | null;
  bruto_ic_inf: number | null;
  bruto_ic_sup: number | null;
  efeito_ajustado_pp: number | null;
  ajustado_ic_inf: number | null;
  ajustado_ic_sup: number | null;
  p_valor: number | null;
  significativo_fdr: boolean | null;
  e_value: number | null;
  metodo: "logit_ame" | "ipw";
  amostra_suficiente: boolean;
  leitura: string | null;
  ordem: number | null;
}

export async function efeitos(grupo: string | undefined) {
  return consultar<EfeitoFator>(
    `SELECT fator, nivel, referencia, grupo, n_nivel, n_referencia, taxa_nivel, taxa_referencia,
            efeito_bruto_pp, bruto_ic_inf, bruto_ic_sup, efeito_ajustado_pp, ajustado_ic_inf, ajustado_ic_sup,
            p_valor, significativo_fdr, e_value, metodo, amostra_suficiente, leitura, ordem
       FROM resultado.efeito_fator
      WHERE $1::text IS NULL OR grupo = $1::text
      ORDER BY ordem NULLS LAST, fator, nivel, metodo`,
    [grupo ?? null],
  );
}

export interface Segmento {
  valor: string;
  novos: number;
  voltaram_7d: number;
  taxa: number;
  ic_inf: number;
  ic_sup: number;
  amostra_suficiente: boolean;
}

export async function segmentos(variavel: string) {
  return consultar<Segmento>(
    `SELECT valor, novos, voltaram_7d, taxa, ic_inf, ic_sup, amostra_suficiente
       FROM mart.agg_retencao_segmento
      WHERE variavel = $1
      ORDER BY valor`,
    [variavel],
  );
}

export interface Balanco {
  covariavel: string;
  dp_antes: number | null;
  dp_depois: number | null;
}

export async function balanco(tratamento: string) {
  return consultar<Balanco>(
    `SELECT covariavel, dp_antes, dp_depois
       FROM resultado.balanco_propensao
      WHERE tratamento = $1
      ORDER BY covariavel`,
    [tratamento],
  );
}
