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

/** Troca nomes técnicos por descrição em português no texto principal; devolve os nomes originais para o detalhe recolhível. */
export function traduzirTermos(texto: string, termos: Record<string, { inline: string; nota: string }>): { texto: string; tecnicos: { termo: string; nota: string }[] } {
  let saida = texto;
  const tecnicos: { termo: string; nota: string }[] = [];
  // chaves mais longas primeiro, para "hash da conversa repetido" não ser quebrada por outra regra
  for (const termo of Object.keys(termos).sort((a, b) => b.length - a.length)) {
    if (!saida.includes(termo)) continue;
    saida = saida.split(termo).join(termos[termo]!.inline);
    tecnicos.push({ termo: termo.trim(), nota: termos[termo]!.nota });
  }
  return { texto: saida, tecnicos };
}

/** Tipo do classificador a partir do campo modelo: "openrouter:..." é IA; "regras..." é palavras-chave; sem modelo, desconhecido. */
export function tipoClassificador(modelo: string | null): "ia" | "regras" | null {
  if (!modelo) return null;
  return modelo.startsWith("regras") ? "regras" : "ia";
}

/** "recusa" → "Recusa" (nome do que o classificador marca, para a frase da validação). */
export function nomeCapitalizado(chave: string): string {
  const n = nomeLegivel(chave);
  return n.charAt(0).toUpperCase() + n.slice(1);
}
