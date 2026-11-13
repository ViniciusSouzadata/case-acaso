"use client";

import { Estado } from "@/components/Estado";
import { resumir } from "@/lib/achados";
import { t } from "@/lib/mensagens";
import { useApi } from "@/lib/useApi";

interface Achado {
  ordem: number;
  titulo: string;
  evidencia: string;
  decisao: string;
  limite: string;
}

/** Cartões dos achados, com a decisão e o limite (vêm de resultado.achado via API). */
export function Achados() {
  const r = useApi<Achado[]>("/api/achados");
  const achados = r.estado === "ok" ? r.corpo.dados : [];
  return (
    <section aria-labelledby="achados-titulo">
      <h2 id="achados-titulo" className="mb-2 text-base font-semibold text-slate-900">{t("fatores.achadosTitulo")}</h2>
      {r.estado === "carregando" ? <Estado tipo="carregando" /> : null}
      {r.estado === "erro" ? <Estado tipo="erro" mensagem={r.mensagem} requestId={r.requestId} /> : null}
      {r.estado === "ok" && achados.length === 0 ? <Estado tipo="vazio" mensagem={t("fatores.achadosVazio")} /> : null}
      <div className="grid gap-3 md:grid-cols-3">
        {achados.map((a) => {
          const ev = resumir(a.evidencia);
          const de = resumir(a.decisao);
          const temDetalhe = ev.resto !== "" || de.resto !== "" || a.limite !== "";
          return (
            <article key={a.ordem} className="cartao p-4 text-sm">
              <h3 className="font-semibold text-slate-900">{a.titulo}</h3>
              <p className="mt-2"><span className="font-medium">{t("fatores.achadoEvidencia")}:</span> {ev.visivel}</p>
              <p className="mt-2"><span className="font-medium">{t("fatores.achadoDecisao")}:</span> {de.visivel}</p>
              {temDetalhe ? (
                <details className="mt-2">
                  <summary className="cursor-pointer text-azul">{t("fatores.achadoDetalhes")}</summary>
                  {ev.resto !== "" ? <p className="mt-2"><span className="font-medium">{t("fatores.achadoMaisEvidencia")}:</span> {ev.resto}</p> : null}
                  {de.resto !== "" ? <p className="mt-2"><span className="font-medium">{t("fatores.achadoMaisDecisao")}:</span> {de.resto}</p> : null}
                  <p className="mt-2 text-slate-700"><span className="font-medium">{t("fatores.achadoLimite")}:</span> {a.limite}</p>
                </details>
              ) : null}
            </article>
          );
        })}
      </div>
    </section>
  );
}
