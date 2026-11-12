// Preparação da Tela 3 (funções puras).
import type { Reconciliacao } from "./consultas/qualidade";

export type VeredictoDados = "sem_lote" | "sem_conferencia" | "ok" | "falha";

/** Resposta à pergunta "posso confiar?": só diz "ok" se houver conferência e todas baterem. */
export function veredicto(temLote: boolean, rec: Pick<Reconciliacao, "ok">[]): { v: VeredictoDados; falhas: number; total: number } {
  const total = rec.length;
  const falhas = rec.filter((r) => !r.ok).length;
  if (!temLote) return { v: "sem_lote", falhas, total };
  if (total === 0) return { v: "sem_conferencia", falhas, total };
  return { v: falhas > 0 ? "falha" : "ok", falhas, total };
}

/** Nome legível de um classificador ou métrica: "tema_classificador" → "tema classificador". */
export function nomeLegivel(chave: string): string {
  return chave.replace(/_/g, " ");
}
