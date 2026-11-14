"use client";

import { Estado } from "@/components/Estado";
import { t } from "@/lib/mensagens";
import { useApi } from "@/lib/useApi";

interface Indicador {
  indicador: string;
  nome_exibicao: string;
  definicao: string;
  formula: string;
  denominador: string;
  periodo_referencia: string;
  fonte: string;
  limitacoes: string;
}

function Campo({ rotulo, children }: { rotulo: string; children: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wide text-violeta-escuro">{rotulo}</dt>
      <dd className="mt-0.5 text-slate-900">{children}</dd>
    </div>
  );
}

/** Conteúdo do painel lateral de um cartão: definição em linguagem comum primeiro; fórmula e fonte na parte técnica. Vem do dicionário de indicadores. */
export function DetalheIndicador({ indicador }: { indicador: string }) {
  const r = useApi<Indicador[]>(`/api/dicionario?indicador=${encodeURIComponent(indicador)}`);
  const item = r.estado === "ok" ? r.corpo.dados[0] : undefined;
  return (
    <section className="cartao p-4" data-testid="detalhe-indicador">
      {r.estado === "carregando" ? <Estado tipo="carregando" /> : null}
      {r.estado === "erro" ? <Estado tipo="erro" mensagem={r.mensagem} requestId={r.requestId} /> : null}
      {r.estado === "ok" && !item ? <Estado tipo="vazio" mensagem={t("glossario.naoEncontrado")} /> : null}
      {item ? (
        <dl className="space-y-3 text-sm">
          <Campo rotulo={t("glossario.definicao")}>{item.definicao}</Campo>
          <Campo rotulo={t("glossario.denominador")}>{item.denominador}</Campo>
          <Campo rotulo={t("glossario.periodo")}>{item.periodo_referencia}</Campo>
          <Campo rotulo={t("glossario.limitacoes")}>{item.limitacoes}</Campo>
          <details className="rounded-lg border border-[#e3e0f3] p-2">
            <summary className="cursor-pointer font-medium text-violeta-escuro">{t("glossario.tecnicoTitulo")}</summary>
            <div className="mt-2 space-y-3">
              <Campo rotulo={t("glossario.formula")}>{item.formula}</Campo>
              <Campo rotulo={t("glossario.fonte")}>{item.fonte}</Campo>
            </div>
          </details>
        </dl>
      ) : null}
    </section>
  );
}
