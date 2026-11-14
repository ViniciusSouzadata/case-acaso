"use client";

import type { CSSProperties, ReactNode } from "react";
import { useContagem } from "@/lib/movimento";

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
  atrasoMs = 0,
}: {
  rotulo: string;
  valor: string;
  apoio?: string;
  escuro?: boolean;
  onAbrir?: () => void;
  extra?: ReactNode;
  /** aviso curto embaixo do apoio (ex.: limite honesto de um número) */
  selo?: ReactNode;
  testid?: string;
  /** conta de 0 até o número uma única vez (≤ 600 ms; sem animação com movimento reduzido) */
  animar?: { valor: number; formato: (n: number) => string };
  atrasoMs?: number;
}) {
  const contado = useContagem(animar?.valor ?? null, animar !== undefined);
  const mostrado = animar && contado !== null ? animar.formato(contado) : valor;
  const corpo = (
    <>
      <div className={`flex items-center justify-between gap-2 text-sm ${escuro ? "text-white/80" : "text-slate-600"}`}>
        <span>{rotulo}</span>
        {extra}
      </div>
      <div className={`mt-1 font-display text-3xl font-semibold leading-none tracking-tight sm:text-4xl ${escuro ? "text-papel" : "text-tinta"}`} data-testid={testid}>
        {mostrado}
      </div>
      {apoio ? <div className={`mt-2 text-xs ${escuro ? "text-white/80" : "text-slate-600"}`}>{apoio}</div> : null}
      {selo ? <div className="mt-1.5">{selo}</div> : null}
    </>
  );
  const estilo: CSSProperties = { animationDelay: `${atrasoMs}ms` };
  const base = `entra ${escuro ? "cartao-escuro" : "cartao"} p-4 text-left`;
  return onAbrir ? (
    <button type="button" onClick={onAbrir} style={estilo} className={`${base} clicavel w-full`}>
      {corpo}
    </button>
  ) : (
    <div className={base} style={estilo}>{corpo}</div>
  );
}
