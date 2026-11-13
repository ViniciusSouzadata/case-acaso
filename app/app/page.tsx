"use client";

import { useState } from "react";
import { BlocoSemana, SEMANAS } from "@/components/BlocoSemana";
import { BlocoSensibilidade } from "@/components/BlocoSensibilidade";
import { CartaoKpi } from "@/components/CartaoKpi";
import { DetalheTaxa } from "@/components/DetalheTaxa";
import { Estado } from "@/components/Estado";
import { Glossario } from "@/components/Glossario";
import { Cascata } from "@/components/graficos/Cascata";
import { GraficoTaxa } from "@/components/graficos/GraficoTaxa";
import { PainelLateral } from "@/components/PainelLateral";
import { montarCascata, prepararCoortes, resumoSensibilidade, type CoorteApi, type ResumoSemanaApi, type SensibilidadeApi } from "@/lib/graficos";
import { t } from "@/lib/mensagens";
import { useContagem } from "@/lib/movimento";
import { conclusaoSemana, deCadaCem } from "@/lib/painel";
import { formatarInt, formatarPct } from "@/lib/regras";
import { useApi } from "@/lib/useApi";

interface Resumo {
  usuarios: number;
  voltaram_7d: number;
  taxa: number;
  ic_inf: number;
  ic_sup: number;
}

type Detalhe = null | "grafico" | "semana" | "definicoes";

const dataBr = (iso: string) => iso.split("-").reverse().join("/");

/** Tela 1 — Retenção, em formato de painel: números grandes, um gráfico, a semana em compacto. Explicações ficam atrás de "Ver detalhes". */
export default function PaginaRetencao() {
  const [detalhe, setDetalhe] = useState<Detalhe>(null);
  const [glossario, setGlossario] = useState(false);
  const resumo = useApi<Resumo | null>("/api/retencao/resumo");
  const coortes = useApi<CoorteApi[]>("/api/retencao/coortes?granularidade=semana");
  const sens = useApi<SensibilidadeApi[]>("/api/retencao/sensibilidade");
  const semana = useApi<{ resumo: ResumoSemanaApi | null }>(`/api/semana/decomposicao?semana=${SEMANAS[0]}`);

  const r = resumo.estado === "ok" ? resumo.corpo.dados : null;
  const linhas = coortes.estado === "ok" ? prepararCoortes(coortes.corpo.dados, "semana") : [];
  const faixa = sens.estado === "ok" ? resumoSensibilidade(sens.corpo.dados) : null;
  const rs = semana.estado === "ok" ? semana.corpo.dados.resumo : null;
  const cascata = rs ? montarCascata(rs) : null;
  const concl = rs ? conclusaoSemana(rs) : null;
  const taxaAnimada = useContagem(r ? r.taxa * 100 : null, true);

  const frase = r
    ? faixa
      ? t("painel.tela1.conclusao", { n: deCadaCem(r.taxa), min: `${deCadaCem(faixa.min)}` })
      : t("retencao.respostaSemDados")
    : resumo.estado === "ok"
      ? t("retencao.respostaSemDados")
      : "";

  return (
    <div className="space-y-4">
      <header>
        <h1 className="titulo-painel">{t("painel.tela1.titulo")}</h1>
        <p className="mt-1 max-w-3xl text-base text-slate-700" data-testid="frase-resposta">{frase}</p>
      </header>

      <section aria-label="Números principais" className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {resumo.estado === "carregando" ? <Estado tipo="carregando" /> : null}
        {resumo.estado === "erro" ? <Estado tipo="erro" mensagem={resumo.mensagem} requestId={resumo.requestId} /> : null}
        {r ? (
          <>
            <CartaoKpi
              escuro
              rotulo={t("painel.tela1.cartaoTaxa")}
              valor={formatarPct(taxaAnimada !== null ? taxaAnimada / 100 : r.taxa)}
              apoio={t("painel.tela1.cartaoTaxaSub", { inf: formatarPct(r.ic_inf), sup: formatarPct(r.ic_sup) })}
              testid="valor"
              extra={
                <button type="button" aria-label={`${t("numero.info")} (${t("painel.tela1.cartaoTaxa")})`} onClick={() => setGlossario(true)} className="flex h-5 w-5 items-center justify-center rounded-full border border-violeta-claro text-xs font-semibold text-violeta-claro hover:bg-violeta-claro hover:text-tinta">
                  i
                </button>
              }
            />
            <CartaoKpi rotulo={t("painel.tela1.cartaoPessoas")} valor={formatarInt(r.usuarios)} apoio={t("painel.tela1.cartaoPessoasSub")} />
            <CartaoKpi rotulo={t("painel.tela1.cartaoVoltaram")} valor={formatarInt(r.voltaram_7d)} apoio={t("painel.tela1.cartaoVoltaramSub")} />
            <CartaoKpi
              rotulo={t("painel.tela1.cartaoDefinicao")}
              valor={faixa ? `${formatarPct(faixa.min)}–${formatarPct(faixa.max)}` : "—"}
              apoio={sens.estado === "ok" ? t("painel.tela1.cartaoDefinicaoSub", { n: sens.corpo.dados.length }) : undefined}
              onAbrir={faixa ? () => setDetalhe("definicoes") : undefined}
            />
          </>
        ) : null}
      </section>

      <div className="grid gap-3 lg:grid-cols-[minmax(0,1.7fr)_minmax(0,1fr)]">
        <section className="cartao p-4" aria-labelledby="g-titulo">
          <div className="flex items-start justify-between gap-3">
            <h2 id="g-titulo" className="text-base font-semibold text-tinta">{t("painel.tela1.graficoTitulo")}</h2>
            <button type="button" onClick={() => setDetalhe("grafico")} className="shrink-0 text-sm font-medium text-violeta hover:underline">{t("painel.verDetalhes")}</button>
          </div>
          {coortes.estado === "carregando" ? <Estado tipo="carregando" /> : null}
          {coortes.estado === "erro" ? <Estado tipo="erro" mensagem={coortes.mensagem} requestId={coortes.requestId} /> : null}
          {coortes.estado === "ok" && linhas.length === 0 ? <Estado tipo="vazio" /> : null}
          {linhas.length > 0 ? <GraficoTaxa linhas={linhas} altura="h-[17rem]" /> : null}
        </section>

        <section className="cartao p-4" aria-labelledby="s-titulo">
          <div className="flex items-start justify-between gap-3">
            <h2 id="s-titulo" className="text-base font-semibold text-tinta">{t("painel.tela1.semanaTitulo", { data: dataBr(SEMANAS[0]) })}</h2>
            <button type="button" onClick={() => setDetalhe("semana")} className="shrink-0 text-sm font-medium text-violeta hover:underline">{t("painel.verDetalhes")}</button>
          </div>
          {semana.estado === "carregando" ? <Estado tipo="carregando" /> : null}
          {semana.estado === "erro" ? <Estado tipo="erro" mensagem={semana.mensagem} requestId={semana.requestId} /> : null}
          {semana.estado === "ok" && !rs ? <Estado tipo="vazio" mensagem={t("semana.semResumo")} /> : null}
          {rs && cascata ? (
            <>
              <p className="text-xs text-slate-600">{t("painel.tela1.semanaSub", { base: formatarPct(rs.taxa_base), semana: formatarPct(rs.taxa_semana) })}</p>
              <Cascata degraus={cascata.degraus} altura="h-52" semJargao />
              {concl ? (
                <p className="text-sm text-slate-800" data-testid="conclusao-semana">
                  {concl.frase}{" "}
                  {concl.normal !== null ? (
                    <span className={`whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ${concl.normal ? "bg-[#ece9fd] text-violeta-escuro" : "bg-[#ffe9db] text-[#8a3a00]"}`}>
                      {t(concl.normal ? "painel.semana.normal" : "painel.semana.foraNormal")}
                    </span>
                  ) : null}
                </p>
              ) : null}
            </>
          ) : null}
        </section>
      </div>

      {glossario ? <Glossario indicador="taxa_retorno_7d" onFechar={() => setGlossario(false)} /> : null}
      {detalhe ? (
        <PainelLateral
          titulo={t(detalhe === "grafico" ? "painel.tela1.detalheGrafico" : detalhe === "semana" ? "painel.tela1.detalheSemana" : "painel.tela1.detalheDefinicoes")}
          onFechar={() => setDetalhe(null)}
        >
          {detalhe === "grafico" ? <DetalheTaxa /> : null}
          {detalhe === "semana" ? <BlocoSemana /> : null}
          {detalhe === "definicoes" ? <BlocoSensibilidade /> : null}
        </PainelLateral>
      ) : null}
    </div>
  );
}
