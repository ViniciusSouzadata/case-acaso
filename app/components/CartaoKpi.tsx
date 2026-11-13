"use client";

import type { ReactNode } from "react";

/** Cartão grande de um número: rótulo, valor em destaque e uma linha de apoio. `onAbrir` transforma o cartão em botão para o detalhe. */
export function CartaoKpi({
  rotulo,
  valor,
  apoio,
  escuro = false,
  onAbrir,
  extra,
  testid,
}: {
  rotulo: string;
  valor: string;
  apoio?: string;
  escuro?: boolean;
  onAbrir?: () => void;
  extra?: ReactNode;
  testid?: string;
}) {
  const corpo = (
    <>
      <div className={`flex items-center justify-between gap-2 text-sm ${escuro ? "text-white/80" : "text-slate-600"}`}>
        <span>{rotulo}</span>
        {extra}
      </div>
      <div className={`mt-1 font-display text-3xl font-semibold leading-none tracking-tight sm:text-4xl ${escuro ? "text-papel" : "text-tinta"}`} data-testid={testid}>
        {valor}
      </div>
      {apoio ? <div className={`mt-2 text-xs ${escuro ? "text-white/80" : "text-slate-600"}`}>{apoio}</div> : null}
    </>
  );
  const base = `${escuro ? "cartao-escuro" : "cartao"} p-4 text-left`;
  return onAbrir ? (
    <button type="button" onClick={onAbrir} className={`${base} w-full transition-shadow hover:shadow-md`}>
      {corpo}
    </button>
  ) : (
    <div className={base}>{corpo}</div>
  );
}
