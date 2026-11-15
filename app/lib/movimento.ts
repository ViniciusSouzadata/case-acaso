"use client";

import { useEffect, useState } from "react";

/** true quando a pessoa pediu menos movimento; sem matchMedia (testes, SSR) conta como "sem animação". */
export function useMovimentoReduzido(): boolean {
  const [reduzido, setReduzido] = useState(true);
  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") return;
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduzido(mq.matches);
    const ouvir = (e: MediaQueryListEvent) => setReduzido(e.matches);
    mq.addEventListener("change", ouvir);
    return () => mq.removeEventListener("change", ouvir);
  }, []);
  return reduzido;
}

/** Contagem de 0 até o valor (ease-out, uma vez por valor). Com movimento reduzido devolve o valor direto. */
export function useContagem(valor: number | null, ativo: boolean, duracaoMs = 600): number | null {
  const reduzido = useMovimentoReduzido();
  const [atual, setAtual] = useState<number | null>(valor);
  useEffect(() => {
    if (valor === null || !ativo || reduzido || typeof requestAnimationFrame !== "function") {
      setAtual(valor);
      return;
    }
    let quadro = 0;
    const ini = performance.now();
    const passo = (agora: number) => {
      const p = Math.min(1, (agora - ini) / duracaoMs);
      setAtual(valor * (1 - Math.pow(1 - p, 3)));
      if (p < 1) quadro = requestAnimationFrame(passo);
    };
    quadro = requestAnimationFrame(passo);
    return () => cancelAnimationFrame(quadro);
  }, [valor, ativo, reduzido, duracaoMs]);
  return atual;
}

const bezier = (a: number, b: number, c: number, d: number): [number, number, number, number] => [a, b, c, d];

/** Durações, atrasos e curvas do movimento — o ritmo todo se ajusta aqui. Segundos, exceto onde indicado. */
export const MOV = {
  /** curvas (cubic-bezier) */
  curva: { entrada: bezier(0.22, 1, 0.36, 1), contagem: bezier(0.16, 1, 0.3, 1), revela: bezier(0.65, 0, 0.35, 1) },
  /** título palavra por palavra (blur → nítido) */
  palavra: { duracao: 0.5, intervalo: 0.08, blur: 10, y: 8 },
  /** frase logo abaixo do título */
  frase: { atraso: 0.25, duracao: 0.5 },
  /** cartões: entram em sequência; o conteúdo vem um instante depois do cartão */
  cartao: { duracao: 0.6, intervalo: 0.07, atraso: 0.2, blur: 8, y: 16, escala: 0.98, atrasoConteudo: 0.1 },
  /** saída da página ao trocar de tela (a entrada é a das peças da tela nova) */
  pagina: { saida: 0.25, blurSaida: 6 },
  /** pílula do menu que desliza (mola) */
  pilula: { type: "spring", stiffness: 380, damping: 32 },
  /** números grandes contando de 0 */
  contagem: 1.2,
  /** cartão de destaque abrindo em círculo a partir do canto */
  revela: { duracao: 0.8, atraso: 0.3, atrasoTexto: 0.4 },
  /** barras crescendo (Tela 3 e margem de erro do ranking) */
  barra: { duracao: 1, atraso: 0.6, intervalo: 0.05 },
  /** hover (mola) e toque */
  mola: { type: "spring", stiffness: 300, damping: 20 },
  toque: 0.97,
  /** só o fade, quando a pessoa pediu menos movimento */
  fade: 0.25,
} as const;
