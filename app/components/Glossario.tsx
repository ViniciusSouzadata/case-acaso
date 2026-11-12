"use client";

import { useEffect } from "react";
import { t } from "@/lib/mensagens";
import { useApi } from "@/lib/useApi";
import { Estado } from "./Estado";

interface Indicador {
  indicador: string;
  nome_exibicao: string;
  definicao: string;
  formula: string;
  denominador: string;
  periodo_referencia: string;
  fonte: string;
  sql_referencia: string;
  limitacoes: string;
}

/** REQ-402: painel com definição, fórmula, denominador, período, fonte e SQL, vindos de /api/dicionario. */
export function Glossario({ indicador, onFechar }: { indicador: string; onFechar: () => void }) {
  const r = useApi<Indicador[]>(`/api/dicionario?indicador=${encodeURIComponent(indicador)}`);

  useEffect(() => {
    const fechar = (e: KeyboardEvent) => {
      if (e.key === "Escape") onFechar();
    };
    window.addEventListener("keydown", fechar);
    return () => window.removeEventListener("keydown", fechar);
  }, [onFechar]);

  const item = r.estado === "ok" ? r.corpo.dados[0] : undefined;

  return (
    <div role="dialog" aria-modal="true" aria-label={t("glossario.titulo")} className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 sm:items-center">
      <div className="max-h-[85vh] w-full max-w-xl overflow-y-auto rounded-t-lg bg-white p-5 shadow-xl sm:rounded-lg">
        <div className="flex items-start justify-between gap-4">
          <h2 className="text-lg font-semibold">{item ? item.nome_exibicao : t("glossario.titulo")}</h2>
          <button type="button" onClick={onFechar} className="rounded border px-2 py-1 text-sm">
            {t("glossario.fechar")}
          </button>
        </div>
        {r.estado === "carregando" ? <Estado tipo="carregando" /> : null}
        {r.estado === "erro" ? <Estado tipo="erro" mensagem={r.mensagem} requestId={r.requestId} /> : null}
        {r.estado === "ok" && !item ? <Estado tipo="vazio" mensagem={t("glossario.naoEncontrado")} /> : null}
        {item ? (
          <dl className="mt-3 space-y-3 text-sm">
            <Campo rotulo={t("glossario.definicao")}>{item.definicao}</Campo>
            <Campo rotulo={t("glossario.formula")}>{item.formula}</Campo>
            <Campo rotulo={t("glossario.denominador")}>{item.denominador}</Campo>
            <Campo rotulo={t("glossario.periodo")}>{item.periodo_referencia}</Campo>
            <Campo rotulo={t("glossario.fonte")}>{item.fonte}</Campo>
            <Campo rotulo={t("glossario.limitacoes")}>{item.limitacoes}</Campo>
            <Campo rotulo={t("glossario.sql")}>
              <pre className="overflow-x-auto rounded bg-slate-100 p-2 text-xs">{item.sql_referencia}</pre>
            </Campo>
          </dl>
        ) : null}
      </div>
    </div>
  );
}

function Campo({ rotulo, children }: { rotulo: string; children: React.ReactNode }) {
  return (
    <div>
      <dt className="font-medium text-slate-700">{rotulo}</dt>
      <dd className="mt-0.5 text-slate-900">{children}</dd>
    </div>
  );
}
