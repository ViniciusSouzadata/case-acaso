"use client";

import { Estado } from "@/components/Estado";
import { PontosSensibilidade } from "@/components/graficos/PontosSensibilidade";
import { resumoSensibilidade, type SensibilidadeApi } from "@/lib/graficos";
import { t } from "@/lib/mensagens";
import { formatarPct } from "@/lib/regras";
import { useApi } from "@/lib/useApi";

/** "E se a definição de usuário ou de sessão mudar?" */
export function BlocoSensibilidade() {
  const r = useApi<SensibilidadeApi[]>("/api/retencao/sensibilidade");
  const linhas = r.estado === "ok" ? r.corpo.dados : [];
  const v = resumoSensibilidade(linhas);

  return (
    <section className="rounded border border-slate-200 bg-white p-4" aria-labelledby="sens-titulo">
      <h2 id="sens-titulo" className="text-base font-semibold text-slate-900">{t("sens.titulo")}</h2>
      <p className="mt-1 text-sm text-slate-700">{t("sens.intro")}</p>
      {r.estado === "carregando" ? <Estado tipo="carregando" /> : null}
      {r.estado === "erro" ? <Estado tipo="erro" mensagem={r.mensagem} requestId={r.requestId} /> : null}
      {r.estado === "ok" && linhas.length === 0 ? <Estado tipo="vazio" /> : null}
      {v ? (
        <>
          <h3 className="mt-3 mb-2 text-sm font-medium text-slate-800">
            {t("sens.tituloGrafico", { min: formatarPct(v.min), max: formatarPct(v.max) })}
          </h3>
          <PontosSensibilidade linhas={linhas} />
        </>
      ) : null}
    </section>
  );
}
