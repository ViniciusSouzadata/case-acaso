// Funções puras do formato "painel" (Telas 1 e 2): nomes curtos, "a cada 100", frases de conclusão.
import type { LinhaFloresta } from "./floresta";
import type { ResumoSemanaApi } from "./graficos";
import { t } from "./mensagens";

const nf = (casas: number) => new Intl.NumberFormat("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas });

/** Efeito em pontos percentuais → "−16 a cada 100" (sem jargão). Abaixo de 1 mantém uma casa; arredondado para zero vira "perto de zero". */
export function aCadaCem(pp: number | null | undefined): string {
  if (pp == null) return "—";
  const abs = Math.abs(pp);
  const texto = abs >= 10 ? nf(0).format(abs) : nf(1).format(abs);
  if (Number(texto.replace(",", ".")) === 0) return t("painel.pertoDeZero");
  return `${pp < 0 ? "−" : "+"}${texto} ${t("painel.aCadaCem")}`;
}

/** Só o número, para o destaque grande ("−16"). */
export function numeroGrande(pp: number | null | undefined): string {
  if (pp == null) return "—";
  const abs = Math.abs(pp);
  const texto = abs >= 10 ? nf(0).format(abs) : nf(1).format(abs);
  return `${pp < 0 ? "−" : pp > 0 ? "+" : ""}${texto}`;
}

/** Nome curto, em linguagem comum, de uma linha do ranking. Sem tradução cadastrada, cai em "rótulo: nível". */
export function nomeCurto(fator: string, nivel: string): string {
  return NOMES[`${fator}|${nivel}`] ?? `${rotuloFator(fator)}: ${nivel}`;
}

function rotuloFator(f: string): string {
  const chave = `fatores.rotulos.${f}`;
  const r = t(chave);
  return r === chave ? f : r;
}

const NOMES: Record<string, string> = {
  "recusa|sim": "Recebeu recusa",
  "faixa_chars_resposta|301–1.000": "Resposta média",
  "faixa_chars_resposta|1.001–2.500": "Resposta longa",
  "faixa_chars_resposta|mais de 2.500": "Resposta muito longa",
  "modelo_familia|gpt-4": "GPT-4 (em vez de GPT-3.5)",
  "idioma_divergente|sim": "Resposta em outro idioma",
  "virada_dez2023|depois (dez/2023 em diante, GPT-4 padrão)": "Depois de dez/2023",
  "idioma|Spanish": "Escreve em espanhol",
  "idioma|English": "Escreve em inglês",
  "idioma|outros": "Escreve em outro idioma",
  "tema|conversa pessoal/conselho": "Tema: conversa pessoal",
  "tema|estudo/dever de casa": "Tema: estudo",
  "tema|informação geral/curiosidade": "Tema: curiosidade",
  "periodo_dia|manhã": "Usa de manhã",
  "periodo_dia|noite": "Usa à noite",
  "periodo_dia|madrugada": "Usa de madrugada",
  "era_modelo|2023-07..10 (só 3.5)": "Chegou entre jul e out/2023",
  "era_modelo|2023-11 (4 volta)": "Chegou em nov/2023",
  "era_modelo|2023-04..06 (3.5 + 4 opcional)": "Chegou entre abr e jun/2023",
  "regiao|Nordeste": "Região Nordeste",
  "regiao|outras regiões": "Outras regiões",
  "faixa_chars_pergunta|31–100": "Pergunta de tamanho médio",
  "faixa_chars_pergunta|101–400": "Pergunta longa",
  "faixa_chars_pergunta|mais de 400": "Pergunta muito longa",
  "fim_de_semana|sim": "Primeira vez no fim de semana",
  "dispositivo|celular": "Usa o celular",
  "dispositivo|outro": "Outro aparelho",
  "n_turnos_sessao|2 a 3": "2 a 3 turnos na 1ª visita",
  "n_turnos_sessao|4 ou mais": "4 ou mais turnos na 1ª visita",
  "n_conversas_sessao|2": "2 conversas na 1ª visita",
  "n_conversas_sessao|3 ou mais": "3 ou mais conversas na 1ª visita",
};

export type Selo = "sustenta" | "acaso" | "semDiferenca" | "pequena" | "descritivo";

/** O selo de uma linha: laranja só para o que resiste à correção para muitas comparações. */
export function seloDaLinha(l: LinhaFloresta): Selo {
  if (l.pequena) return "pequena";
  if (l.grupo === "engajamento" || l.grupo === "descritivo") return "descritivo";
  if (l.resisteFdr) return "sustenta";
  if (l.podeSerAcaso) return "acaso";
  return "semDiferenca";
}

/** Valor que vai para o destaque da linha: o ajustado quando existe, senão o bruto. Amostra pequena nunca vira número. */
export function efeitoDaLinha(l: LinhaFloresta): number | null {
  if (l.pequena) return null;
  return l.referenciaDoRotulo?.efeito ?? null;
}

/** Frase única da Tela 2, a partir da contagem do que resiste à correção. */
export function conclusaoFatores(sustentam: string[], total: number): string {
  if (total === 0) return t("painel.fatores.semDados");
  if (sustentam.length === 0) return t("painel.fatores.nenhum");
  if (sustentam.length === 1) return t("painel.fatores.um", { nome: sustentam[0]!.toLowerCase() });
  return t("painel.fatores.varios", { k: sustentam.length });
}

/** Linha de conclusão da semana: quanto caiu/subiu, por quê, e se cabe na variação normal. */
export function conclusaoSemana(r: ResumoSemanaApi): { frase: string; normal: boolean | null } | null {
  if (r.delta_pp === null || r.mix_pp === null || r.taxa_pp === null) return null;
  const abs = nf(1).format(Math.abs(r.delta_pp));
  const causa = Math.abs(r.taxa_pp) >= Math.abs(r.mix_pp) ? t("painel.semana.causaComportamento") : t("painel.semana.causaPublico");
  const frase = t(r.delta_pp < 0 ? "painel.semana.caiu" : "painel.semana.subiu", { abs, causa });
  return { frase, normal: r.p_valor === null ? null : r.p_valor >= 0.05 };
}

/** Taxa em fração → "24" (inteiro, para a frase "24 de cada 100"). */
export function deCadaCem(taxa: number): string {
  return nf(0).format(taxa * 100);
}

// ---------------------------------------------------------------- Tela 3 (confiança nos dados)

/** Nome curto, em linguagem comum, de um problema de qualidade. O texto longo (do banco) continua no detalhe. */
const NOMES_PROBLEMA: [string, string][] = [
  ["Conversas de IPs de tráfego anômalo", "Tráfego fora do comum"],
  ["Conversas do IP mais ativo", "IP mais ativo"],
  ["Idioma divergente em pergunta curta", "Idioma mal detectado"],
  ["IP muda no meio da conversa", "IP que muda"],
  ["Pergunta vazia", "Pergunta vazia"],
  ["Conteúdo repetido", "Conteúdo repetido"],
  ["Conversa sem nenhuma mensagem do usuário", "Sem mensagem do usuário"],
  ["Conversas com dado pessoal ocultado", "Dado pessoal ocultado"],
  ["Semanas com queda forte", "Semanas com queda de volume"],
  ["Conversas tóxicas", "Conversas tóxicas"],
];

export function nomeProblema(texto: string): string {
  return NOMES_PROBLEMA.find(([prefixo]) => texto.startsWith(prefixo))?.[1] ?? texto;
}

/** "semanas" quando o percentual é de semanas (não de conversas): fica fora das barras de % de conversas. */
export function unidadeProblema(texto: string): "conversas" | "semanas" {
  return texto.startsWith("Semanas") ? "semanas" : "conversas";
}

/** Frase única da Tela 3, montada da carga e das conferências. O tom muda quando alguma não bate. */
export function fraseConfianca(v: "sem_lote" | "sem_conferencia" | "ok" | "falha", total: number, falhas: number, rejeitadas: number | null): { frase: string; ok: boolean } {
  if (v === "falha") return { frase: t("painel.tela3.falha", { k: falhas, m: total }), ok: false };
  if (v === "sem_lote") return { frase: t("dados.respostaSemLote"), ok: false };
  if (v === "sem_conferencia") return { frase: t("dados.respostaSemConf"), ok: false };
  const rej = rejeitadas === null ? "" : rejeitadas === 0 ? t("painel.tela3.nenhumaRejeitada") : t("painel.tela3.rejeitadas", { n: new Intl.NumberFormat("pt-BR").format(rejeitadas) });
  return { frase: t("painel.tela3.ok", { m: total, rej }), ok: true };
}

/** Acerto do classificador feito por IA (o que alimenta os números do painel), ou null se não houver conferência dele. */
export function acertoIA(validacao: { classificador: string; modelo: string | null; acuracia: number | null; n: number | null }[], classificador: string): { acuracia: number; n: number } | null {
  const v = validacao.find((x) => x.classificador === classificador && x.modelo !== null && !x.modelo.startsWith("regras") && x.acuracia !== null && x.n !== null);
  return v ? { acuracia: v.acuracia as number, n: v.n as number } : null;
}
