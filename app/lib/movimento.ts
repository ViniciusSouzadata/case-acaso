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
