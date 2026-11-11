import { consultar } from "../db";

export interface ResumoSemana {
  semana: string;
  base_descricao: string | null;
  n_base: number | null;
  n_semana: number | null;
  taxa_base: number | null;
  taxa_semana: number | null;
  delta_pp: number | null;
  mix_pp: number | null;
  taxa_pp: number | null;
  p_valor: number | null;
  conclusao: string | null;
}

export interface SegmentoSemana {
  semana: string;
  segmento: string;
  peso_base: number | null;
  peso_semana: number | null;
  taxa_base: number | null;
  taxa_semana: number | null;
  efeito_mix_pp: number | null;
  efeito_taxa_pp: number | null;
}

export async function decomposicao(semana: string) {
  const [r, s] = await Promise.all([
    consultar<ResumoSemana>(
      `SELECT semana, base_descricao, n_base, n_semana, taxa_base, taxa_semana, delta_pp, mix_pp, taxa_pp, p_valor, conclusao
         FROM resultado.decomposicao_resumo WHERE semana = $1::date LIMIT 1`,
      [semana],
    ),
    consultar<SegmentoSemana>(
      `SELECT semana, segmento, peso_base, peso_semana, taxa_base, taxa_semana, efeito_mix_pp, efeito_taxa_pp
         FROM resultado.decomposicao_semana WHERE semana = $1::date ORDER BY segmento`,
      [semana],
    ),
  ]);
  return { resumo: r.linhas[0] ?? null, segmentos: s.linhas, ms: r.ms + s.ms };
}
