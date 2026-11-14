"use client";

import { motion, useReducedMotion } from "motion/react";
import type { ResumoSemanaApi } from "@/lib/graficos";
import { t } from "@/lib/mensagens";
import { MOV } from "@/lib/movimento";
import { baseSeguinte, deCadaCem, numeroGrande } from "@/lib/painel";

/** Barra horizontal que sai de um zero comum: para a esquerda quando tira, para a direita quando soma. */
function BarraDoZero({ rotulo, valor, maximo, indice }: { rotulo: string; valor: number; maximo: number; indice: number }) {
  const reduzido = useReducedMotion() ?? false;
  const larg = (Math.abs(valor) / maximo) * 50;
  const negativo = valor < 0;
  return (
    <div className="grid grid-cols-[minmax(0,8.5rem)_minmax(0,1fr)_3rem] items-center gap-x-2 text-sm" data-componente={rotulo}>
      <span className="text-slate-800">{rotulo}</span>
      <span className="relative block h-4" role="img" aria-label={`${rotulo}: ${numeroGrande(valor)}`}>
        <span className="absolute inset-y-0 left-1/2 block w-px bg-slate-500" />
        <motion.span
          className="absolute inset-y-0.5 block rounded-sm bg-violeta"
          style={{ width: `${Math.max(larg, 1.5)}%`, [negativo ? "right" : "left"]: "50%", transformOrigin: negativo ? "right center" : "left center" }}
          initial={reduzido ? false : { scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ duration: MOV.barra.duracao, delay: MOV.barra.atraso + indice * MOV.barra.intervalo, ease: MOV.curva.entrada }}
        />
      </span>
      <span className="text-right font-display font-semibold text-tinta">{numeroGrande(valor)}</span>
    </div>
  );
}

/** Semana explicada em duas partes que um leigo lê sozinho: "26 → 22" e "de onde veio a diferença" (duas barras saindo do mesmo zero). */
export function DiferencaSemana({ resumo }: { resumo: ResumoSemanaApi }) {
  if (resumo.taxa_base === null || resumo.taxa_semana === null || resumo.mix_pp === null || resumo.taxa_pp === null) return null;
  const maximo = Math.max(Math.abs(resumo.mix_pp), Math.abs(resumo.taxa_pp), 0.1);
  return (
    <div className="space-y-3" data-testid="diferenca-semana">
      <div>
        <div className="flex items-baseline gap-2 font-display font-semibold leading-none text-tinta">
          <span className="text-4xl">{deCadaCem(resumo.taxa_base)}</span>
          <span aria-hidden className="text-2xl text-slate-400">→</span>
          <span className="text-4xl">{deCadaCem(resumo.taxa_semana)}</span>
        </div>
        <div className="mt-1 text-xs text-slate-600">{t(baseSeguinte(resumo) ? "painel.tela1.diferencaLegendaSeguintes" : "painel.tela1.diferencaLegenda")}</div>
      </div>
      <div>
        <div className="mb-1 text-xs font-medium text-slate-600">{t("painel.tela1.deOndeVeio")}</div>
        <div className="space-y-1.5">
          <BarraDoZero indice={0} rotulo={t("semana.degrauTaxa")} valor={resumo.taxa_pp} maximo={maximo} />
          <BarraDoZero indice={1} rotulo={t("semana.degrauMix")} valor={resumo.mix_pp} maximo={maximo} />
        </div>
      </div>
    </div>
  );
}
