import { readFileSync } from "node:fs";

// Banco simulado para os testes sem Docker: devolve as linhas dos exemplos conforme a tabela consultada.
type Ex = { dados: any; meta: Record<string, any> };
const ex = (nome: string) => JSON.parse(readFileSync(`exemplos/${nome}.json`, "utf8")) as Ex;

export async function consultarSimulado(sql: string): Promise<{ linhas: unknown[]; ms: number }> {
  const r = (linhas: unknown) => ({ linhas: linhas as unknown[], ms: 1 });
  if (sql.includes("FROM ops.lote_carga WHERE status") && sql.includes("iniciado_em")) return r([ex("qualidade").dados.lote]);
  if (sql.includes("FROM ops.lote_carga"))
    return r([{ lote_id: 1, versao_definicao: "1.0.0", terminado_em: "2026-11-14T12:00:00Z" }]);
  if (sql.includes("SELECT versao_analise FROM resultado.meta")) return r([{ versao_analise: "1.0.0" }]);
  if (sql.includes("n_elegiveis")) return r([ex("retencao-resumo").dados]);
  if (sql.includes("mart.agg_retencao_periodo")) return r(ex("retencao-coortes").dados);
  if (sql.includes("mart.dim_era_modelo")) return r(ex("retencao-coortes").meta.eras);
  if (sql.includes("mart.agg_retencao_sensibilidade")) return r(ex("retencao-sensibilidade").dados);
  if (sql.includes("mart.dicionario_indicador")) return r(ex("dicionario").dados);
  if (sql.includes("resultado.efeito_fator")) return r(ex("fatores-efeitos").dados);
  if (sql.includes("mart.agg_retencao_segmento")) return r(ex("fatores-segmentos").dados);
  if (sql.includes("resultado.balanco_propensao")) return r(ex("fatores-balanco").dados);
  if (sql.includes("resultado.decomposicao_resumo")) return r([ex("semana-decomposicao").dados.resumo]);
  if (sql.includes("resultado.decomposicao_semana")) return r(ex("semana-decomposicao").dados.segmentos);
  if (sql.includes("resultado.achado")) return r(ex("achados").dados);
  if (sql.includes("ops.reconciliacao")) return r(ex("qualidade").dados.reconciliacao);
  if (sql.includes("resultado.problema_qualidade")) return r(ex("qualidade").dados.problemas);
  if (sql.includes("resultado.validacao_classificador")) return r(ex("qualidade").dados.validacao);
  throw new Error("consulta inesperada: " + sql.slice(0, 60));
}
