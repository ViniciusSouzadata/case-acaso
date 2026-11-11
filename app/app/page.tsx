"use client";

import { useState } from "react";
import { BlocoSemana } from "@/components/BlocoSemana";
import { BlocoSensibilidade } from "@/components/BlocoSensibilidade";
import { Estado } from "@/components/Estado";
import { Numero } from "@/components/Numero";
import { GraficoRetencao } from "@/components/graficos/GraficoRetencao";
import { TabelaCoortes } from "@/components/graficos/TabelaCoortes";
import { prepararCoortes, resumoVariacao, type CoorteApi, type EraApi, type Granularidade } from "@/lib/graficos";
import { t } from "@/lib/mensagens";
import { formatarInt, formatarPct } from "@/lib/regras";
import { useApi } from "@/lib/useApi";

interface Resumo {
  usuarios: number;
  voltaram_7d: number;
  taxa: number;
  ic_inf: number;
  ic_sup: number;
}

/** Tela 1 — Retenção. */
export default function PaginaRetencao() {
  const [gran, setGran] = useState<Granularidade>("semana");
  const resumo = useApi<Resumo | null>("/api/retencao/resumo");
  const coortes = useApi<CoorteApi[]>(`/api/retencao/coortes?granularidade=${gran}`);

  const r = resumo.estado === "ok" ? resumo.corpo.dados : null;
  const eras = coortes.estado === "ok" ? ((coortes.corpo.meta.eras as EraApi[] | undefined) ?? []) : [];
  const linhas = coortes.estado === "ok" ? prepararCoortes(coortes.corpo.dados, gran) : [];
  const variacao = resumoVariacao(linhas);
  const pequenas = linhas.filter((l) => !l.amostraOk).length;
  const imaturas = linhas.filter((l) => !l.madura).length;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-xl font-semibold text-slate-900">{t("retencao.pergunta")}</h1>
        <p className="mt-2 text-base text-slate-800" data-testid="frase-resposta">
          {r
            ? t("retencao.resposta", { taxa: formatarPct(r.taxa), inf: formatarPct(r.ic_inf), sup: formatarPct(r.ic_sup), n: formatarInt(r.usuarios) })
            : resumo.estado === "ok"
              ? t("retencao.respostaSemDados")
              : ""}
        </p>
      </header>

      <section aria-label={t("retencao.cartaoRotulo")} className="max-w-sm">
        {resumo.estado === "carregando" ? <Estado tipo="carregando" /> : null}
        {resumo.estado === "erro" ? <Estado tipo="erro" mensagem={resumo.mensagem} requestId={resumo.requestId} /> : null}
        {resumo.estado === "ok" && !r ? <Estado tipo="vazio" /> : null}
        {r ? (
          <Numero rotulo={t("retencao.cartaoRotulo")} valor={r.taxa} formato="pct" icInf={r.ic_inf} icSup={r.ic_sup} n={r.usuarios} indicador="taxa_retorno_7d" />
        ) : null}
      </section>

      <section className="rounded border border-slate-200 bg-white p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <h2 className="max-w-2xl text-base font-semibold text-slate-900">
            {variacao
              ? t("retencao.tituloGrafico", { min: formatarPct(variacao.min), max: formatarPct(variacao.max) })
              : coortes.estado === "ok"
                ? t("retencao.tituloGraficoSemMedida")
                : t("retencao.tituloGraficoCarregando")}
          </h2>
          <div role="group" aria-label="Granularidade" className="flex overflow-hidden rounded border border-slate-300 text-sm">
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

      <BlocoSensibilidade />
      <BlocoSemana />
    </div>
  );
}
