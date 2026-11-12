"use client";

import { useState } from "react";
import { Estado } from "@/components/Estado";
import { Cascata } from "@/components/graficos/Cascata";
import { montarCascata, type ResumoSemanaApi } from "@/lib/graficos";
import { t } from "@/lib/mensagens";
import { formatarInt, formatarPP, formatarPct } from "@/lib/regras";
import { useApi } from "@/lib/useApi";

// Semanas oferecidas (decisão do planejador): a principal (20/11/2023, abre selecionada) e a outra (01/05/2023) como contraponto, por decisão atualizada do planejador.
export const SEMANAS = ["2023-11-20", "2023-05-01"] as const;

interface SegmentoSemanaApi {
  segmento: string;
  peso_base: number | null;
  peso_semana: number | null;
  taxa_base: number | null;
  taxa_semana: number | null;
  efeito_mix_pp: number | null;
  efeito_taxa_pp: number | null;
}

interface Decomposicao {
  resumo: ResumoSemanaApi | null;
  segmentos: SegmentoSemanaApi[];
}

const dataBr = (iso: string) => iso.split("-").reverse().join("/");

/** Cascata base → quem chegou → comportamento → semana, com a frase de conclusão vinda da API. */
export function BlocoSemana() {
  const [semana, setSemana] = useState<string>(SEMANAS[0]);
  const r = useApi<Decomposicao>(`/api/semana/decomposicao?semana=${semana}`);
  const dados = r.estado === "ok" ? r.corpo.dados : null;
  const resumo = dados?.resumo ?? null;
  const cascata = resumo ? montarCascata(resumo) : null;

  return (
    <section className="rounded border border-slate-200 bg-white p-4" aria-labelledby="semana-titulo">
      <h2 id="semana-titulo" className="text-base font-semibold text-slate-900">{t("semana.titulo", { semana: dataBr(semana) })}</h2>
      <p className="mt-1 text-sm text-slate-700">{t("semana.intro")}</p>

      <div role="group" aria-label={t("semana.escolha")} className="mt-3 flex flex-wrap gap-2 text-sm">
        {SEMANAS.map((s) => (
          <button key={s} type="button" aria-pressed={semana === s} onClick={() => setSemana(s)} className={`rounded border px-3 py-1 ${semana === s ? "border-azul bg-azul text-white" : "border-slate-300 bg-white text-slate-800"}`}>
            {t("semana.chip", { data: dataBr(s) })}
          </button>
        ))}
      </div>

      {r.estado === "carregando" ? <Estado tipo="carregando" /> : null}
      {r.estado === "erro" ? <Estado tipo="erro" mensagem={r.mensagem} requestId={r.requestId} /> : null}
      {r.estado === "ok" && !resumo ? <Estado tipo="vazio" mensagem={t("semana.semResumo")} /> : null}

      {resumo && cascata ? (
        <div className="mt-3">
          <h3 className="mb-2 text-sm font-medium text-slate-800">
            {t("semana.tituloGrafico", {
              base: formatarPct(resumo.taxa_base),
              semana: formatarPct(resumo.taxa_semana),
              delta: formatarPP(resumo.delta_pp),
              mix: formatarPP(resumo.mix_pp),
              taxa: formatarPP(resumo.taxa_pp),
            })}
          </h3>
          <Cascata degraus={cascata.degraus} />
          {!cascata.fecha ? <p role="note" className="text-xs text-slate-700">{t("semana.naoFecha", { dif: formatarPP(cascata.diferenca).replace(" p.p.", "") })}</p> : null}
          <p className="mt-2 text-xs text-slate-600">{t("semana.legenda")}</p>
          {resumo.conclusao ? <p className="mt-3 rounded bg-slate-50 p-3 text-sm text-slate-900" data-testid="conclusao">{resumo.conclusao}</p> : null}
          <p className="mt-2 text-xs text-slate-600">
            {resumo.base_descricao ? <>{t("semana.base", { descricao: resumo.base_descricao })}. </> : null}
            {t("semana.n", { nBase: formatarInt(resumo.n_base), nSemana: formatarInt(resumo.n_semana) })}
          </p>

          <details className="mt-3">
            <summary className="cursor-pointer text-sm text-azul">{t("semana.detalhe")}</summary>
            <div className="mt-2 space-y-2 text-xs text-slate-700">
              {resumo.p_valor !== null ? <p>{t("semana.detalheP", { p: formatarPct(resumo.p_valor, 1) })}</p> : null}
              {dados && dados.segmentos.length > 0 ? (
                <table className="w-full text-left">
                  <caption className="sr-only">{t("semana.porGrupo")}</caption>
                  <thead>
                    <tr className="border-b border-slate-300">
                      <th scope="col" className="py-1 pr-2 font-medium">{t("semana.colGrupo")}</th>
                      <th scope="col" className="py-1 pr-2 font-medium">{t("semana.colPesoBase")}</th>
                      <th scope="col" className="py-1 pr-2 font-medium">{t("semana.colPesoSemana")}</th>
                      <th scope="col" className="py-1 pr-2 font-medium">{t("semana.colTaxaBase")}</th>
                      <th scope="col" className="py-1 pr-2 font-medium">{t("semana.colTaxaSemana")}</th>
                      <th scope="col" className="py-1 pr-2 font-medium">{t("semana.colMix")}</th>
                      <th scope="col" className="py-1 font-medium">{t("semana.colTaxa")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dados.segmentos.map((s) => (
                      <tr key={s.segmento} className="border-b border-slate-100">
                        <th scope="row" className="py-1 pr-2 font-normal">{s.segmento}</th>
                        <td className="py-1 pr-2">{formatarPct(s.peso_base)}</td>
                        <td className="py-1 pr-2">{formatarPct(s.peso_semana)}</td>
                        <td className="py-1 pr-2">{formatarPct(s.taxa_base)}</td>
                        <td className="py-1 pr-2">{formatarPct(s.taxa_semana)}</td>
                        <td className="py-1 pr-2">{formatarPP(s.efeito_mix_pp, 2)}</td>
                        <td className="py-1">{formatarPP(s.efeito_taxa_pp, 2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : null}
            </div>
          </details>
        </div>
      ) : null}
    </section>
  );
}
