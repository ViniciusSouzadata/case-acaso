// Preparação dos dados dos gráficos (funções puras, testáveis). O desenho fica em components/graficos/.

export type Granularidade = "semana" | "mes";

export interface CoorteApi {
  periodo: string; // AAAA-MM-DD
  novos: number;
  voltaram_7d: number | null;
  taxa: number | null; // fração
  ic_inf: number | null;
  ic_sup: number | null;
  taxa_mm4: number | null;
  madura: boolean;
  amostra_suficiente: boolean;
}

export interface EraApi {
  era: string;
  inicio: string;
  fim: string | null;
  descricao: string;
}

export interface LinhaGrafico {
  periodo: string;
  rotulo: string;
  /** em % (0–100), pronto para o eixo */
  taxa: number | null;
  icBase: number | null;
  icAltura: number | null;
  mm4: number | null;
  novos: number;
  voltaram: number | null;
  icInf: number | null; // fração
  icSup: number | null; // fração
  taxaFracao: number | null;
  amostraOk: boolean;
  madura: boolean;
}

const MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];

/** "2023-05-01" → "01/05/23" (semana) ou "mai/23" (mês). */
export function rotuloPeriodo(periodo: string, g: Granularidade): string {
  const [a, m, d] = periodo.split("-");
  if (!a || !m || !d) return periodo;
  return g === "mes" ? `${MESES[Number(m) - 1]}/${a.slice(2)}` : `${d}/${m}/${a.slice(2)}`;
}

const pct = (x: number | null) => (x === null ? null : x * 100);

export function prepararCoortes(c: CoorteApi[], g: Granularidade): LinhaGrafico[] {
  return c.map((x) => {
    const mostrarTaxa = x.madura && x.taxa !== null;
    return {
      periodo: x.periodo,
      rotulo: rotuloPeriodo(x.periodo, g),
      taxa: mostrarTaxa ? pct(x.taxa) : null,
      icBase: mostrarTaxa && x.ic_inf !== null ? pct(x.ic_inf) : null,
      icAltura: mostrarTaxa && x.ic_inf !== null && x.ic_sup !== null ? (x.ic_sup - x.ic_inf) * 100 : null,
      mm4: pct(x.taxa_mm4),
      novos: x.novos,
      voltaram: x.voltaram_7d,
      icInf: x.ic_inf,
      icSup: x.ic_sup,
      taxaFracao: x.taxa,
      amostraOk: x.amostra_suficiente,
      madura: x.madura,
    };
  });
}

export interface FaixaEra {
  era: string;
  descricao: string;
  inicio: string;
  fim: string | null;
  x1: string;
  x2: string;
  cor: string;
}

// Okabe-Ito, em tom claro, só para o fundo.
const CORES_ERA = ["#56b4e9", "#e69f00", "#009e73", "#cc79a7", "#f0e442"];

/** Para cada era, a primeira e a última categoria do eixo X que cai dentro dela. */
export function faixasEras(linhas: LinhaGrafico[], eras: EraApi[]): FaixaEra[] {
  const faixas: FaixaEra[] = [];
  eras.forEach((e, i) => {
    const dentro = linhas.filter((l) => l.periodo >= e.inicio && (e.fim === null || l.periodo <= e.fim));
    const primeira = dentro[0];
    const ultima = dentro[dentro.length - 1];
    if (primeira && ultima)
      faixas.push({
        era: e.era,
        descricao: e.descricao,
        inicio: e.inicio,
        fim: e.fim,
        x1: primeira.periodo,
        x2: ultima.periodo,
        cor: CORES_ERA[i % CORES_ERA.length]!,
      });
  });
  return faixas;
}

/** Trechos consecutivos de coortes ainda imaturas (hachurados no gráfico). */
export function faixasImaturas(linhas: LinhaGrafico[]): { x1: string; x2: string }[] {
  const trechos: { x1: string; x2: string }[] = [];
  let inicio: string | null = null;
  let fimAtual: string | null = null;
  for (const l of linhas) {
    if (!l.madura) {
      inicio ??= l.periodo;
      fimAtual = l.periodo;
    } else if (inicio !== null && fimAtual !== null) {
      trechos.push({ x1: inicio, x2: fimAtual });
      inicio = null;
      fimAtual = null;
    }
  }
  if (inicio !== null && fimAtual !== null) trechos.push({ x1: inicio, x2: fimAtual });
  return trechos;
}

/** Menor e maior taxa entre as coortes maduras e com amostra suficiente (para o título que diz a conclusão). */
export function resumoVariacao(linhas: LinhaGrafico[]): { min: number; max: number; validas: number; total: number } | null {
  const validas = linhas.filter((l) => l.madura && l.amostraOk && l.taxaFracao !== null);
  if (validas.length === 0) return null;
  const taxas = validas.map((l) => l.taxaFracao as number);
  return { min: Math.min(...taxas), max: Math.max(...taxas), validas: validas.length, total: linhas.length };
}
