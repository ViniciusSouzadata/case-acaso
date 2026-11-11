import { consultar } from "../db";

// SQL parametrizado; lê só mart.* e resultado.* (princípio: nada de stg).

export interface Resumo {
  usuarios: number;
  voltaram_7d: number;
  taxa: number;
  ic_inf: number;
  ic_sup: number;
  periodo_inicio: string | null;
  periodo_fim: string | null;
  efeito_minimo_detectavel_pp: number;
}

/** Números globais de resultado.meta; período = 1ª e última semana madura de mart.agg_retencao_periodo. */
export async function resumo() {
  const { linhas, ms } = await consultar<Resumo>(
    `SELECT m.n_elegiveis AS usuarios, m.n_retornos AS voltaram_7d, m.taxa_global AS taxa,
            m.ic_inf, m.ic_sup,
            p.inicio AS periodo_inicio, p.fim AS periodo_fim,
            m.efeito_minimo_detectavel_pp
       FROM (SELECT * FROM resultado.meta ORDER BY executado_em DESC LIMIT 1) m
       CROSS JOIN (SELECT min(periodo)::text AS inicio, (max(periodo) + 7)::text AS fim
                     FROM mart.agg_retencao_periodo
                    WHERE granularidade = 'semana' AND madura) p`,
  );
  return { linhas, ms };
}

export interface Coorte {
  periodo: string;
  novos: number;
  voltaram_7d: number | null;
  taxa: number | null;
  ic_inf: number | null;
  ic_sup: number | null;
  taxa_mm4: number | null;
  madura: boolean;
  amostra_suficiente: boolean;
}

export async function coortes(granularidade: string, inicio: string | undefined, fim: string | undefined) {
  return consultar<Coorte>(
    `SELECT periodo, novos, voltaram_7d, taxa, ic_inf, ic_sup, taxa_mm4, madura, amostra_suficiente
       FROM mart.agg_retencao_periodo
      WHERE granularidade = $1
        AND ($2::date IS NULL OR periodo >= $2::date)
        AND ($3::date IS NULL OR periodo < $3::date)
      ORDER BY periodo`,
    [granularidade, inicio ?? null, fim ?? null],
  );
}

export interface Era {
  era: string;
  inicio: string;
  fim: string | null;
  descricao: string;
}

export async function eras() {
  return consultar<Era>(`SELECT era, inicio, fim, descricao FROM mart.dim_era_modelo ORDER BY inicio`);
}

export interface Sensibilidade {
  definicao: string;
  descricao: string;
  usuarios: number;
  voltaram_7d: number;
  taxa: number;
  ic_inf: number;
  ic_sup: number;
  delta_vs_oficial: number;
}

export async function sensibilidade() {
  return consultar<Sensibilidade>(
    `SELECT definicao, descricao, usuarios, voltaram_7d, taxa, ic_inf, ic_sup, delta_vs_oficial
       FROM mart.agg_retencao_sensibilidade
      ORDER BY (definicao <> 'oficial'), definicao`,
  );
}
