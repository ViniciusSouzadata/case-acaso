"use client";

import { useMemo, type ReactNode } from "react";
import { motion, useReducedMotion, type Variants } from "motion/react";
import { MOV } from "@/lib/movimento";

type Tag = "div" | "section" | "article" | "ul" | "li" | "p" | "header";

// Objetos de variantes com identidade fixa: se fossem recriados a cada render do pai, a animação reiniciaria no meio.
const FADE: Variants = { oculto: { opacity: 0 }, visivel: { opacity: 1, transition: { duration: MOV.fade } } };

const ITEM: Variants = {
  oculto: { opacity: 0, filter: `blur(${MOV.cartao.blur}px)`, y: MOV.cartao.y, scale: MOV.cartao.escala },
  visivel: { opacity: 1, filter: "blur(0px)", y: 0, scale: 1, transition: { duration: MOV.cartao.duracao, ease: MOV.curva.entrada } },
};

const CONTEUDO: Variants = {
  oculto: { opacity: 0, filter: `blur(${MOV.cartao.blur}px)` },
  visivel: { opacity: 1, filter: "blur(0px)", transition: { duration: MOV.cartao.duracao, delay: MOV.cartao.atrasoConteudo, ease: MOV.curva.entrada } },
};

/** Variantes de entrada dos cartões; com movimento reduzido sobra só o fade. */
export const variantesItem = (reduzido: boolean): Variants => (reduzido ? FADE : ITEM);

/** O que está dentro do cartão chega um instante depois dele (o cartão aparece primeiro, vazio, como um esqueleto). */
export const variantesConteudo = (reduzido: boolean): Variants => (reduzido ? FADE : CONTEUDO);

/** Grupo: os itens dentro dele entram em sequência (cascata curta). */
export function GrupoEntrada({ children, className, atraso = MOV.cartao.atraso, tag = "div", ...resto }: { children: ReactNode; className?: string; atraso?: number; tag?: Tag } & Record<string, unknown>) {
  const reduzido = useReducedMotion() ?? false;
  const Elemento = motion[tag] as typeof motion.div;
  const variantes = useMemo<Variants>(() => ({ oculto: {}, visivel: { transition: { delayChildren: atraso, staggerChildren: reduzido ? 0 : MOV.cartao.intervalo } } }), [atraso, reduzido]);
  return (
    <Elemento className={className} initial="oculto" animate="visivel" variants={variantes} {...resto}>
      {children}
    </Elemento>
  );
}

/**
 * Item de cartão: blur, subida e escala leves ao entrar.
 * Com `atraso` (segundos) anima por conta própria; sem ele, herda a cascata do GrupoEntrada em que está.
 */
export function ItemEntrada({ children, className, tag = "div", atraso, ...resto }: { children: ReactNode; className?: string; tag?: Tag; atraso?: number } & Record<string, unknown>) {
  const reduzido = useReducedMotion() ?? false;
  const Elemento = motion[tag] as typeof motion.div;
  if (atraso === undefined) {
    return (
      <Elemento className={className} variants={variantesItem(reduzido)} {...resto}>
        {children}
      </Elemento>
    );
  }
  const v = variantesItem(reduzido);
  const alvo = v.visivel as Record<string, unknown>;
  const { transition, ...final } = alvo;
  return (
    <Elemento
      className={className}
      initial={v.oculto as never}
      animate={final as never}
      transition={{ ...(transition as object), delay: atraso }}
      {...resto}
    >
      {children}
    </Elemento>
  );
}

/** Conteúdo interno de um item: entra com ~0,1 s de atraso em relação ao cartão. */
export function ConteudoEntrada({ children, className }: { children: ReactNode; className?: string }) {
  const reduzido = useReducedMotion() ?? false;
  return (
    <motion.div className={className} variants={variantesConteudo(reduzido)}>
      {children}
    </motion.div>
  );
}
