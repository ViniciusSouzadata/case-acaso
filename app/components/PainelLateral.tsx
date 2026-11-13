"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { t } from "@/lib/mensagens";

/** Painel lateral "Ver detalhes": onde ficam as explicações, definições e métodos que saíram da tela principal. */
export function PainelLateral({ titulo, onFechar, children }: { titulo: string; onFechar: () => void; children: ReactNode }) {
  const fechar = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const aoTecla = (e: KeyboardEvent) => {
      if (e.key === "Escape") onFechar();
    };
    window.addEventListener("keydown", aoTecla);
    fechar.current?.focus();
    return () => window.removeEventListener("keydown", aoTecla);
  }, [onFechar]);

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-tinta/60" onClick={onFechar}>
      <aside
        role="dialog"
        aria-modal="true"
        aria-label={titulo}
        onClick={(e) => e.stopPropagation()}
        className="entra flex h-full w-full max-w-[40rem] flex-col border-l-4 border-violeta bg-fundo shadow-xl"
      >
        <div className="flex items-start justify-between gap-4 border-b border-[#e3e0f3] bg-papel px-5 py-4">
          <h2 className="font-display text-lg font-semibold text-tinta">{titulo}</h2>
          <button ref={fechar} type="button" onClick={onFechar} className="rounded-lg border border-violeta px-3 py-1 text-sm font-medium text-violeta hover:bg-violeta hover:text-papel">
            {t("painel.fechar")}
          </button>
        </div>
        <div className="flex-1 space-y-4 overflow-y-auto px-5 py-4">{children}</div>
      </aside>
    </div>
  );
}
