import { consultar } from "../db";

export interface IndicadorDicionario {
  indicador: string;
  nome_exibicao: string;
  definicao: string;
  formula: string;
  denominador: string;
  periodo_referencia: string;
  fonte: string;
  sql_referencia: string;
  limitacoes: string;
}

export async function dicionario(indicador: string | undefined) {
  return consultar<IndicadorDicionario>(
    `SELECT indicador, nome_exibicao, definicao, formula, denominador,
            periodo_referencia, fonte, sql_referencia, limitacoes
       FROM mart.dicionario_indicador
      WHERE $1::text IS NULL OR indicador = $1::text
      ORDER BY indicador`,
    [indicador ?? null],
  );
}
