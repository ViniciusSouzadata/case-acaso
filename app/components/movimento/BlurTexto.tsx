"use client";

import { Fragment, useMemo, type ReactNode } from "react";
import { motion, useReducedMotion } from "motion/react";
import { MOV } from "@/lib/movimento";

/** Título que entra palavra por palavra (opacidade, desfoque e subida). O texto inteiro fica no DOM; com movimento reduzido é só um fade. */
export function BlurTexto({ texto, className, tag = "h1", atraso = 0 }: { texto: string; className?: string; tag?: "h1" | "h2"; atraso?: number }) {
  const reduzido = useReducedMotion() ?? false;
  const Elemento = motion[tag] as typeof motion.h1;
  const palavras = texto.split(" ");
  const palavra = useMemo(() => (reduzido
    ? { oculto: { opacity: 0 }, visivel: { opacity: 1, transition: { duration: MOV.fade } } }
    : {
        oculto: { opacity: 0, filter: `blur(${MOV.palavra.blur}px)`, y: MOV.palavra.y },
        visivel: { opacity: 1, filter: "blur(0px)", y: 0, transition: { duration: MOV.palavra.duracao, ease: MOV.curva.entrada } },
      }), [reduzido]);
  const grupo = useMemo(() => ({ oculto: {}, visivel: { transition: { delayChildren: atraso, staggerChildren: reduzido ? 0 : MOV.palavra.intervalo } } }), [atraso, reduzido]);
  return (
    <Elemento className={className} initial="oculto" animate="visivel" variants={grupo}>
      {palavras.map((p, i) => (
        <Fragment key={i}>
          <motion.span variants={palavra} className="inline-block">{p}</motion.span>
          {i < palavras.length - 1 ? " " : null}
        </Fragment>
      ))}
    </Elemento>
  );
}

/** Bloco (a frase-resposta) que entra inteiro, logo depois do título. */
export function BlocoBlur({ children, className, atraso = MOV.frase.atraso, ...resto }: { children: ReactNode; className?: string; atraso?: number } & Record<string, unknown>) {
  const reduzido = useReducedMotion() ?? false;
  return (
    <motion.p
      className={className}
      initial={reduzido ? { opacity: 0 } : { opacity: 0, filter: `blur(${MOV.palavra.blur}px)`, y: MOV.palavra.y }}
      animate={reduzido ? { opacity: 1 } : { opacity: 1, filter: "blur(0px)", y: 0 }}
      transition={{ duration: reduzido ? MOV.fade : MOV.frase.duracao, delay: atraso, ease: MOV.curva.entrada }}
      {...resto}
    >
      {children}
    </motion.p>
  );
}
