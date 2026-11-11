// REGRAS DE CONFIANÇA — um só lugar. Telas e componentes não repetem estas decisões; chamam estas funções.
// (REQ-403..406). Os limiares de amostra vêm da API (`amostra_suficiente`), nunca escritos aqui.

export const NUMERO_VAZIO = "—";

/** REQ-404: amostra pequena quando a API diz que não basta. */
export function amostraPequena(amostraSuficiente: boolean | null | undefined): boolean {
  return amostraSuficiente === false;
}

/** REQ-406: o intervalo de 95% inclui o zero (efeito não distinguível de zero). */
export function cruzaZero(inf: number | null | undefined, sup: number | null | undefined): boolean {
  if (inf == null || sup == null) return false;
  return inf <= 0 && sup >= 0;
}

/** REQ-405: coorte ainda dentro da janela de 7 dias. */
export function imatura(madura: boolean | null | undefined): boolean {
  return madura === false;
}

const nf = (casas: number) =>
  new Intl.NumberFormat("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas });

/** Taxa em fração (0,2386) → "23,9%". */
export function formatarPct(x: number | null | undefined, casas = 1): string {
  return x == null ? NUMERO_VAZIO : `${nf(casas).format(x * 100)}%`;
}

/** Efeito em pontos percentuais (já em pp) → "+4,9 p.p.". */
export function formatarPP(x: number | null | undefined, casas = 1): string {
  if (x == null) return NUMERO_VAZIO;
  const sinal = x > 0 ? "+" : "";
  return `${sinal}${nf(casas).format(x)} p.p.`;
}

export function formatarInt(x: number | null | undefined): string {
  return x == null ? NUMERO_VAZIO : new Intl.NumberFormat("pt-BR").format(x);
}

export type FormatoNumero = "pct" | "pp" | "int";

export function formatar(valor: number | null | undefined, formato: FormatoNumero): string {
  return formato === "pct" ? formatarPct(valor) : formato === "pp" ? formatarPP(valor) : formatarInt(valor);
}
