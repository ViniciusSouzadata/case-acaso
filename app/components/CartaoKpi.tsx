"use client";

import type { ReactNode } from "react";
import { motion, useReducedMotion, type Variants } from "motion/react";
import { Contagem } from "@/components/movimento/Contagem";
import { variantesConteudo, variantesItem } from "@/components/movimento/Entrada";
import { t } from "@/lib/mensagens";
import { MOV } from "@/lib/movimento";

const HEROI: Variants = {
  oculto: { opacity: 0, clipPath: "circle(0% at 0% 0%)" },
  visivel: { opacity: 1, clipPath: "circle(150% at 0% 0%)", transition: { duration: MOV.revela.duracao, ease: MOV.curva.revela } },
};

/** Cartão-herói: abre em círculo a partir do canto superior esquerdo (só fade com movimento reduzido). Identidade fixa das variantes. */
export const variantesHeroi = (reduzido: boolean): Variants => (reduzido ? variantesItem(true) : HEROI);

/** Cartão grande de um número: rótulo, valor em destaque e uma linha de apoio. `onAbrir` transforma o cartão em botão para o detalhe. */
export function CartaoKpi({
  rotulo,
  valor,
  apoio,
  escuro = false,
  onAbrir,
  extra,
  selo,
  testid,
  animar,
}: {
  rotulo: string;
  valor: string;
  apoio?: string;
  /** cartão-herói da tela (degradê violeta, texto branco) */
  escuro?: boolean;
  onAbrir?: () => void;
  extra?: ReactNode;
  /** aviso curto embaixo do apoio (ex.: limite honesto de um número) */
  selo?: ReactNode;
  testid?: string;
  /** conta de 0 até o número uma única vez (~1,2 s; sem contagem com movimento reduzido) */
  animar?: { valor: number; formato: (n: number) => string };
}) {
  const reduzido = useReducedMotion() ?? false;
  const corpo = (
    <motion.div variants={variantesConteudo(reduzido)}>
      <div className={`flex items-center justify-between gap-2 text-sm ${escuro ? "text-white" : "text-slate-600"}`}>
        <span>{rotulo}</span>
        <span className="flex items-center gap-2">
          {extra}
          {onAbrir ? <span aria-hidden title={t("painel.pistaClique")} className={`text-xl leading-none ${escuro ? "text-white" : "text-slate-400"}`}>›</span> : null}
        </span>
      </div>
      <div className={`mt-1 font-display text-3xl font-semibold leading-none tracking-tight sm:text-4xl ${escuro ? "text-papel" : "text-tinta"}`} data-testid={testid}>
        {animar ? <Contagem valor={animar.valor} formato={animar.formato} /> : valor}
      </div>
      {apoio ? <div className={`mt-2 text-xs ${escuro ? "text-white" : "text-slate-600"}`}>{apoio}</div> : null}
      {selo ? <div className="mt-1.5">{selo}</div> : null}
    </motion.div>
  );
  const variantes = escuro ? variantesHeroi(reduzido) : variantesItem(reduzido);
  const base = `${escuro ? "cartao-escuro" : "cartao"} p-4 text-left`;
  const hover = reduzido ? undefined : { y: -4, transition: MOV.mola };
  const toque = reduzido ? undefined : { scale: MOV.toque };
  return onAbrir ? (
    <motion.button type="button" onClick={onAbrir} variants={variantes} whileHover={hover} whileTap={toque} className={`${base} clicavel w-full`}>
      {corpo}
    </motion.button>
  ) : (
    <motion.div variants={variantes} whileHover={hover} className={base}>{corpo}</motion.div>
  );
}
