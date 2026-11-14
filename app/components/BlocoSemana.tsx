"use client";

import { useState } from "react";
import { Estado } from "@/components/Estado";
import { Cascata } from "@/components/graficos/Cascata";
import { Tecnico } from "@/components/painel/Blocos";
import { conclusaoSemana, deCadaCem } from "@/lib/painel";
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
export function BlocoSemana({ inicial = SEMANAS[0] }: { inicial?: string }) {
  const [semana, setSemana] = useState<string>(inicial);
  const r = useApi<Decomposicao>(`/api/semana/decomposicao?semana=${semana}`);
  const dados = r.estado === "ok" ? r.corpo.dados : null;
  const resumo = dados?.resumo ?? null;
  const cascata = resumo ? montarCascata(resumo) : null;

  const concl = resumo ? conclusaoSemana(resumo) : null;

  return (
    <section className="cartao space-y-3 p-4" aria-label={t("painel.tela1.detalheSemana")}>
      <div role="group" aria-label={t("semana.escolha")} className="flex flex-wrap gap-2 text-sm">
        {SEMANAS.map((s) => (
          <button key={s} type="button" aria-pressed={semana === s} onClick={() => setSemana(s)} className={`min-h-10 rounded-full px-3 sm:min-h-0 sm:py-1 ${semana === s ? "bg-laranja font-medium text-tinta" : "bg-[#f1effc] text-slate-800 hover:bg-[#e6e2fa]"}`}>
            {dataBr(s)}
          </button>
        ))}
      </div>

      {r.estado === "carregando" ? <Estado tipo="carregando" /> : null}
      {r.estado === "erro" ? <Estado tipo="erro" mensagem={r.mensagem} requestId={r.requestId} /> : null}
      {r.estado === "ok" && !resumo ? <Estado tipo="vazio" mensagem={t("semana.semResumo")} /> : null}

      {resumo && cascata ? (
        <>
          <p className="text-sm text-slate-800" data-testid="conclusao">
            {t("detalhe.semanaFrase", { semana: deCadaCem(resumo.taxa_semana ?? 0), base: deCadaCem(resumo.taxa_base ?? 0) })}
            {concl ? ` ${concl.frase}` : ""}
          </p>
          <Cascata degraus={cascata.degraus} />
          <p className="text-xs text-slate-700">{t("detalhe.semanaComparada", { nBase: formatarInt(resumo.n_base), nSemana: formatarInt(resumo.n_semana) })}</p>
          <p className="text-sm text-slate-800">
            {resumo.p_valor !== null ? t("detalhe.semanaAcaso", { p: formatarInt(Math.round(resumo.p_valor * 100)) }) : t("detalhe.semanaSemP")}
          </p>

          <Tecnico>
            {!cascata.fecha ? <p role="note" className="text-xs text-slate-700">{t("semana.naoFecha", { dif: formatarPP(cascata.diferenca).replace(" pontos", "") })}</p> : null}
            <p className="text-xs text-slate-700">
              {t("semana.tituloGrafico", {
                base: formatarPct(resumo.taxa_base),
                semana: formatarPct(resumo.taxa_semana),
                delta: formatarPP(resumo.delta_pp),
                mix: formatarPP(resumo.mix_pp),
                taxa: formatarPP(resumo.taxa_pp),
              })}
            </p>
            <p className="text-xs text-slate-700">{t("semana.legenda")}</p>
            {resumo.base_descricao ? <p className="text-xs text-slate-700">{t("semana.base", { descricao: resumo.base_descricao })}</p> : null}
            {resumo.conclusao ? <p className="text-xs text-slate-700">{resumo.conclusao}</p> : null}
            {resumo.p_valor !== null ? <p className="text-xs text-slate-700">{t("semana.detalheP", { p: formatarPct(resumo.p_valor, 1) })}</p> : null}
            {dados && dados.segmentos.length > 0 ? (
              <div className="overflow-x-auto text-xs text-slate-700">
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
              </div>
            ) : null}
          </Tecnico>
        </>
      ) : null}
    </section>
  );
}
