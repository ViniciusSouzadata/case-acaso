"use client";

import { useState } from "react";
import { Estado } from "@/components/Estado";
import { GraficoRetencao } from "@/components/graficos/GraficoRetencao";
import { TabelaCoortes } from "@/components/graficos/TabelaCoortes";
import { Tecnico } from "@/components/painel/Blocos";
import { prepararCoortes, resumoVariacao, type CoorteApi, type EraApi, type Granularidade } from "@/lib/graficos";
import { t } from "@/lib/mensagens";
import { formatarPct } from "@/lib/regras";
import { useApi } from "@/lib/useApi";

/** Painel do gráfico de retenção: uma frase, o gráfico grande e 3 itens de legenda. "Como ler", épocas do produto e tabela ficam recolhidos. */
export function DetalheTaxa() {
  const [gran, setGran] = useState<Granularidade>("semana");
  const [epocas, setEpocas] = useState(false);
  const coortes = useApi<CoorteApi[]>(`/api/retencao/coortes?granularidade=${gran}`);
  const eras = coortes.estado === "ok" ? ((coortes.corpo.meta.eras as EraApi[] | undefined) ?? []) : [];
  const linhas = coortes.estado === "ok" ? prepararCoortes(coortes.corpo.dados, gran) : [];
  const variacao = resumoVariacao(linhas);
  const pequenas = linhas.filter((l) => !l.amostraOk).length;
  const imaturas = linhas.filter((l) => !l.madura).length;

  return (
    <section className="cartao space-y-3 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <p className="max-w-md text-sm text-slate-800">
          {variacao ? t(gran === "mes" ? "detalhe.taxaFraseMes" : "detalhe.taxaFrase", { min: formatarPct(variacao.min, 0), max: formatarPct(variacao.max, 0) }) : t("retencao.tituloGraficoCarregando")}
        </p>
        <div role="group" aria-label="Granularidade" className="flex overflow-hidden rounded-lg border border-[#cfc9ee] text-sm">
          {(["semana", "mes"] as const).map((g) => (
            <button key={g} type="button" aria-pressed={gran === g} onClick={() => setGran(g)} className={`min-h-10 px-3 sm:min-h-0 sm:py-1 ${gran === g ? "bg-violeta text-papel" : "bg-white text-slate-800"}`}>
              {t(g === "semana" ? "retencao.alternarSemana" : "retencao.alternarMes")}
            </button>
          ))}
        </div>
      </div>
      {coortes.estado === "carregando" ? <Estado tipo="carregando" /> : null}
      {coortes.estado === "erro" ? <Estado tipo="erro" mensagem={coortes.mensagem} requestId={coortes.requestId} /> : null}
      {coortes.estado === "ok" && linhas.length === 0 ? <Estado tipo="vazio" /> : null}
      {coortes.estado === "ok" && linhas.length > 0 ? (
        <>
          <GraficoRetencao linhas={linhas} eras={epocas ? eras : []} granularidade={gran} simples />
          {eras.length > 0 ? (
            <button type="button" aria-pressed={epocas} onClick={() => setEpocas(!epocas)} className="alvo text-sm font-medium text-violeta hover:underline">
              {t(epocas ? "detalhe.esconderEpocas" : "detalhe.mostrarEpocas")}
            </button>
          ) : null}
          <Tecnico titulo={t("detalhe.comoLer")}>
            {pequenas > 0 ? <p role="note" className="text-xs text-slate-700">{t("retencao.notaPequena", { k: pequenas, total: linhas.length })}</p> : null}
            {imaturas > 0 ? <p role="note" className="text-xs text-slate-700">{t("retencao.notaImatura", { k: imaturas, total: linhas.length })}</p> : null}
            <GraficoRetencao linhas={linhas} eras={eras} granularidade={gran} soApoio />
          </Tecnico>
          <Tecnico titulo={t("retencao.tabelaResumo")}>
            <div className="max-h-96 overflow-auto">
              <TabelaCoortes linhas={linhas} unidade={t(gran === "mes" ? "retencao.unidadeMes" : "retencao.unidadeSemana")} />
            </div>
          </Tecnico>
        </>
      ) : null}
    </section>
  );
}
