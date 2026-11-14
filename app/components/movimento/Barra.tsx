"use client";

import type { CSSProperties } from "react";
import { motion, useReducedMotion } from "motion/react";
import { MOV } from "@/lib/movimento";

/** Barra que cresce da esquerda para a direita (largura final já no estilo; com movimento reduzido só aparece). */
export function BarraCrescente({ className, style, indice = 0 }: { className?: string; style?: CSSProperties; indice?: number }) {
  const reduzido = useReducedMotion() ?? false;
  return (
    <motion.span
      className={className}
      style={{ ...style, transformOrigin: "left center" }}
      initial={reduzido ? { opacity: 0 } : { scaleX: 0 }}
      animate={reduzido ? { opacity: 1 } : { scaleX: 1 }}
      transition={{ duration: reduzido ? MOV.fade : MOV.barra.duracao, delay: reduzido ? 0 : MOV.barra.atraso + indice * MOV.barra.intervalo, ease: MOV.curva.entrada }}
    />
  );
}
