// Preparação do gráfico de floresta da Tela 2 (funções puras).
import { amostraPequena, cruzaZero } from "./regras";

/** "descritivo": comparações só descritivas (tema), nunca misturadas com os fatores do assistente nem do perfil. */
export type GrupoFator = "assistente" | "perfil" | "engajamento" | "descritivo";
type GrupoApi = "assistente" | "perfil" | "engajamento";

/** O tema descritivo vem da API como "perfil", mas é só descrição (sem ajuste): vira um grupo à parte. */
export function grupoEfetivo(e: { fator: string; grupo: GrupoApi }): GrupoFator {
  return e.fator === "tema_descritivo" ? "descritivo" : e.grupo;
}
const semAjuste = (g: GrupoFator) => g === "engajamento" || g === "descritivo";

export interface EfeitoApi {
  fator: string;
  nivel: string;
  referencia: string;
  grupo: GrupoApi;
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

export interface Estimativa {
  efeito: number;
  inf: number;
  sup: number;
}

export interface LinhaFloresta {
  chave: string;
  fator: string;
  nivel: string;
  referencia: string;
  metodo: EfeitoApi["metodo"];
  grupo: GrupoFator;
  nNivel: number;
  nReferencia: number;
  pequena: boolean;
  bruto: Estimativa | null;
  /** nunca existe para o grupo "engajamento" (consequência, não causa) */
  ajustado: Estimativa | null;
  /** o intervalo que vale para o rótulo: o ajustado quando existe, senão o bruto */
  referenciaDoRotulo: Estimativa | null;
  naoDistingue: boolean;
  resisteFdr: boolean;
  /** intervalo fora do zero, mas sem resistir à correção para muitas comparações: pode ser acaso */
  podeSerAcaso: boolean;
  leitura: string | null;
  /** posições em % da trilha: [inf, efeito, sup] */
  pos: { zero: number; bruto: [number, number, number] | null; ajustado: [number, number, number] | null };
}

function estimativa(e: number | null, i: number | null, s: number | null): Estimativa | null {
  return e === null || i === null || s === null ? null : { efeito: e, inf: i, sup: s };
}

/** Linhas de um grupo, ordenadas pelo tamanho do efeito (ajustado se houver, senão bruto), em escala simétrica em torno do zero. */
export function prepararFloresta(efeitos: EfeitoApi[], grupo: GrupoFator): { linhas: LinhaFloresta[]; limite: number } {
  const doGrupo = efeitos.filter((e) => grupoEfetivo(e) === grupo);
  const base = doGrupo.map((e) => {
    const bruto = estimativa(e.efeito_bruto_pp, e.bruto_ic_inf, e.bruto_ic_sup);
    // engajamento nunca mostra o ajustado, mesmo que a API traga algum valor.
    const ajustado = semAjuste(grupo) ? null : estimativa(e.efeito_ajustado_pp, e.ajustado_ic_inf, e.ajustado_ic_sup);
    const ref = ajustado ?? bruto;
    return { e, bruto, ajustado, ref };
  });
  base.sort((a, b) => Math.abs(b.ref?.efeito ?? 0) - Math.abs(a.ref?.efeito ?? 0));

  const extremos = base.flatMap((b) => [b.bruto, b.ajustado]).flatMap((x) => (x ? [Math.abs(x.inf), Math.abs(x.sup)] : []));
  const limite = extremos.length ? Math.max(...extremos) * 1.1 || 1 : 1;
  const pos = (x: number) => ((x + limite) / (2 * limite)) * 100;
  const tri = (x: Estimativa | null): [number, number, number] | null => (x ? [pos(x.inf), pos(x.efeito), pos(x.sup)] : null);

  const linhas = base.map(({ e, bruto, ajustado, ref }): LinhaFloresta => {
    const pequena = amostraPequena(e.amostra_suficiente);
    return {
      chave: `${e.fator}|${e.nivel}|${e.metodo}`,
      fator: e.fator,
      nivel: e.nivel,
      referencia: e.referencia,
      metodo: e.metodo,
      grupo,
      nNivel: e.n_nivel,
      nReferencia: e.n_referencia,
      pequena,
      bruto,
      ajustado,
      referenciaDoRotulo: ref,
      naoDistingue: !pequena && ref !== null && cruzaZero(ref.inf, ref.sup),
      resisteFdr: e.significativo_fdr === true,
      podeSerAcaso: !semAjuste(grupo) && !pequena && ajustado !== null && !cruzaZero(ajustado.inf, ajustado.sup) && e.significativo_fdr !== true,
      leitura: e.leitura,
      pos: { zero: pos(0), bruto: tri(bruto), ajustado: tri(ajustado) },
    };
  });
  return { linhas, limite };
}

/** Quantas comparações (assistente + perfil, amostra suficiente, com ajuste) se distinguem de zero. */
export function contarDistinguiveis(efeitos: EfeitoApi[]): { k: number; m: number; f: number } {
  const validos = efeitos.filter((e) => grupoEfetivo(e) !== "engajamento" && grupoEfetivo(e) !== "descritivo" && e.amostra_suficiente && e.efeito_ajustado_pp !== null);
  const fora = validos.filter((e) => !cruzaZero(e.ajustado_ic_inf, e.ajustado_ic_sup));
  // f: as que continuam depois da correção para comparações múltiplas (Benjamini-Hochberg, feita na análise)
  return { k: fora.length, m: validos.length, f: fora.filter((e) => e.significativo_fdr === true).length };
}

export function contarDoGrupo(linhas: LinhaFloresta[]): { k: number; m: number } {
  const validas = linhas.filter((l) => !l.pequena && l.referenciaDoRotulo !== null);
  return { k: validas.filter((l) => !l.naoDistingue).length, m: validas.length };
}
