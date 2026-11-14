"use client";

import { useEffect, useRef, useState } from "react";
import { animate, useInView } from "motion/react";
import { MOV, useMovimentoReduzido } from "@/lib/movimento";

/**
 * Número que conta de 0 até o valor, uma única vez, mantendo o formato pt-BR durante a contagem (dígitos tabulares).
 * O valor final fica sempre no DOM (texto para leitor de tela); com movimento reduzido, e nos testes, só ele aparece.
 */
export function Contagem({ valor, formato, duracao = MOV.contagem }: { valor: number; formato: (n: number) => string; duracao?: number }) {
  const reduzido = useMovimentoReduzido();
  const final = formato(valor);
  const ref = useRef<HTMLSpanElement>(null);
  const emVista = useInView(ref, { once: true });
  const [texto, setTexto] = useState(final);

  useEffect(() => {
    if (reduzido || !emVista) return;
    const controle = animate(0, valor, { duration: duracao, ease: MOV.curva.contagem, onUpdate: (v) => setTexto(formato(v)) });
    return () => controle.stop();
    // formato é recriado a cada render do pai; a contagem só reinicia quando o valor muda
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reduzido, emVista, valor, duracao]);

  if (reduzido) return <span className="tabular-nums">{final}</span>;
  return (
    <>
      <span ref={ref} aria-hidden className="tabular-nums">{texto}</span>
      <span className="sr-only">{final}</span>
    </>
  );
}
