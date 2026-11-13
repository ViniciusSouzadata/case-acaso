"use client";

import { useState } from "react";
import { Estado } from "@/components/Estado";
import { GraficoRetencao } from "@/components/graficos/GraficoRetencao";
import { TabelaCoortes } from "@/components/graficos/TabelaCoortes";
import { prepararCoortes, resumoVariacao, type CoorteApi, type EraApi, type Granularidade } from "@/lib/graficos";
import { t } from "@/lib/mensagens";
import { formatarPct } from "@/lib/regras";
import { useApi } from "@/lib/useApi";

/** Visão completa do gráfico de retenção (épocas do produto, volume, legenda inteira, tabela e alternância semana/mês). Só abre no painel lateral. */
export function DetalheTaxa() {
  const [gran, setGran] = useState<Granularidade>("semana");
  const coortes = useApi<CoorteApi[]>(`/api/retencao/coortes?granularidade=${gran}`);
  const eras = coortes.estado === "ok" ? ((coortes.corpo.meta.eras as EraApi[] | undefined) ?? []) : [];
  const linhas = coortes.estado === "ok" ? prepararCoortes(coortes.corpo.dados, gran) : [];
  const variacao = resumoVariacao(linhas);
  const pequenas = linhas.filter((l) => !l.amostraOk).length;
  const imaturas = linhas.filter((l) => !l.madura).length;

  return (
    <section className="cartao p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h3 className="max-w-md text-base font-semibold text-slate-900">
          {variacao ? t("retencao.tituloGrafico", { min: formatarPct(variacao.min), max: formatarPct(variacao.max) }) : t("retencao.tituloGraficoCarregando")}
        </h3>
        <div role="group" aria-label="Granularidade" className="flex overflow-hidden rounded-lg border border-[#cfc9ee] text-sm">
          <button type="button" aria-pressed={gran === "semana"} onClick={() => setGran("semana")} className={`px-3 py-1 ${gran === "semana" ? "bg-azul text-white" : "bg-white text-slate-800"}`}>
            {t("retencao.alternarSemana")}
          </button>
          <button type="button" aria-pressed={gran === "mes"} onClick={() => setGran("mes")} className={`px-3 py-1 ${gran === "mes" ? "bg-azul text-white" : "bg-white text-slate-800"}`}>
            {t("retencao.alternarMes")}
          </button>
        </div>
      </div>
      {coortes.estado === "carregando" ? <Estado tipo="carregando" /> : null}
      {coortes.estado === "erro" ? <Estado tipo="erro" mensagem={coortes.mensagem} requestId={coortes.requestId} /> : null}
      {coortes.estado === "ok" && linhas.length === 0 ? <Estado tipo="vazio" /> : null}
      {coortes.estado === "ok" && linhas.length > 0 ? (
        <>
          <GraficoRetencao linhas={linhas} eras={eras} granularidade={gran} />
          {pequenas > 0 ? <p role="note" className="mt-2 text-xs text-slate-700">{t("retencao.notaPequena", { k: pequenas, total: linhas.length })}</p> : null}
          {imaturas > 0 ? <p role="note" className="mt-1 text-xs text-slate-700">{t("retencao.notaImatura", { k: imaturas, total: linhas.length })}</p> : null}
          <details className="mt-3">
            <summary className="cursor-pointer text-sm text-azul">{t("retencao.tabelaResumo")}</summary>
            <div className="mt-2 max-h-96 overflow-auto">
              <TabelaCoortes linhas={linhas} unidade={t(gran === "mes" ? "retencao.unidadeMes" : "retencao.unidadeSemana")} />
            </div>
          </details>
        </>
      ) : null}
    </section>
  );
}
