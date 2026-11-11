import pt from "../mensagens/pt.json";

type Arvore = { [k: string]: string | Arvore };

/** Busca um texto por caminho ("amostra.titulo") e troca {variaveis}. Chave inexistente devolve a própria chave (aparece no teste). */
export function t(chave: string, vars: Record<string, string | number> = {}): string {
  let atual: string | Arvore | undefined = pt as Arvore;
  for (const parte of chave.split(".")) {
    if (atual === undefined || typeof atual === "string") return chave;
    atual = atual[parte];
  }
  if (typeof atual !== "string") return chave;
  return atual.replace(/\{(\w+)\}/g, (_, k: string) => (k in vars ? String(vars[k]) : `{${k}}`));
}

export const todasAsMensagens = pt as Arvore;
