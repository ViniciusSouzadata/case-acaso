"use client";

import { useState } from "react";
import { BlocoSemana, SEMANAS } from "@/components/BlocoSemana";
import { BlocoSensibilidade } from "@/components/BlocoSensibilidade";
import { CartaoKpi } from "@/components/CartaoKpi";
import { DetalheTaxa } from "@/components/DetalheTaxa";
import { Estado } from "@/components/Estado";
import { DestacaNumeros } from "@/components/DestacaNumeros";
import { DetalheIndicador } from "@/components/DetalheIndicador";
import { BlocoBlur, BlurTexto } from "@/components/movimento/BlurTexto";
import { GrupoEntrada, ItemEntrada } from "@/components/movimento/Entrada";
import { DiferencaSemana } from "@/components/graficos/DiferencaSemana";
import { GraficoTaxa } from "@/components/graficos/GraficoTaxa";
import { PainelLateral } from "@/components/PainelLateral";
import { montarCascata, prepararCoortes, resumoSensibilidade, type CoorteApi, type Granularidade, type ResumoSemanaApi, type SensibilidadeApi } from "@/lib/graficos";
import { t } from "@/lib/mensagens";
import { conclusaoSemana, deCadaCem, periodoBase } from "@/lib/painel";
import { formatarInt, formatarPct } from "@/lib/regras";
import { useApi } from "@/lib/useApi";

interface Resumo {
  usuarios: number;
  voltaram_7d: number;
  taxa: number;
  ic_inf: number;
  ic_sup: number;
  periodo_inicio: string;
  periodo_fim: string;
}

type Detalhe = null | "grafico" | "semana" | "definicoes" | "taxa" | "pessoas" | "voltaram";

const INDICADOR: Partial<Record<NonNullable<Detalhe>, string>> = { taxa: "taxa_retorno_7d", pessoas: "novos_usuarios", voltaram: "voltaram_7d" };

const dataBr = (iso: string) => iso.split("-").reverse().join("/");

/** Tela 1 — Retenção, em formato de painel: números grandes, um gráfico, a semana em compacto. Explicações ficam atrás de "Ver detalhes". */
export default function PaginaRetencao() {
  const [detalhe, setDetalhe] = useState<Detalhe>(null);
  const [gran, setGran] = useState<Granularidade>("mes");
  const [semanaSel, setSemanaSel] = useState<string>(SEMANAS[0]);
  const resumo = useApi<Resumo | null>("/api/retencao/resumo");
  const coortes = useApi<CoorteApi[]>(`/api/retencao/coortes?granularidade=${gran}`);
  const sens = useApi<SensibilidadeApi[]>("/api/retencao/sensibilidade");
  const semana = useApi<{ resumo: ResumoSemanaApi | null }>(`/api/semana/decomposicao?semana=${semanaSel}`);

  const r = resumo.estado === "ok" ? resumo.corpo.dados : null;
  const linhas = coortes.estado === "ok" ? prepararCoortes(coortes.corpo.dados, gran) : [];
  const faixa = sens.estado === "ok" ? resumoSensibilidade(sens.corpo.dados) : null;
  const rs = semana.estado === "ok" ? semana.corpo.dados.resumo : null;
  const cascata = rs ? montarCascata(rs) : null;
  const concl = rs ? conclusaoSemana(rs) : null;

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
        <BlurTexto className="titulo-painel" texto={t("painel.tela1.titulo")} />
        <BlocoBlur className="mt-1 max-w-3xl text-base text-slate-700" data-testid="frase-resposta"><DestacaNumeros texto={frase} /></BlocoBlur>
      </header>

      <GrupoEntrada tag="section" aria-label="Números principais" className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {resumo.estado === "carregando" ? <Estado tipo="carregando" /> : null}
        {resumo.estado === "erro" ? <Estado tipo="erro" mensagem={resumo.mensagem} requestId={resumo.requestId} /> : null}
        {r ? (
          <>
            <CartaoKpi
              escuro
              rotulo={t("painel.tela1.cartaoTaxa")}
              valor={formatarPct(r.taxa)}
              animar={{ valor: r.taxa * 100, formato: (n) => formatarPct(n / 100) }}
              apoio={t("painel.tela1.cartaoTaxaSub", { voltaram: formatarInt(r.voltaram_7d), total: formatarInt(r.usuarios), inf: formatarPct(r.ic_inf), sup: formatarPct(r.ic_sup) })}
              testid="valor"
              onAbrir={() => setDetalhe("taxa")}
            />
            <CartaoKpi rotulo={t("painel.tela1.cartaoPessoas")} valor={formatarInt(r.usuarios)} animar={{ valor: r.usuarios, formato: (n) => formatarInt(Math.round(n)) }} apoio={t("painel.tela1.cartaoPessoasSub")} onAbrir={() => setDetalhe("pessoas")} />
            <CartaoKpi rotulo={t("painel.tela1.cartaoVoltaram")} valor={formatarInt(r.voltaram_7d)} animar={{ valor: r.voltaram_7d, formato: (n) => formatarInt(Math.round(n)) }} apoio={t("painel.tela1.cartaoVoltaramSub")} onAbrir={() => setDetalhe("voltaram")} />
            <CartaoKpi
              rotulo={t("painel.tela1.cartaoDefinicao")}
              valor={faixa ? `${formatarPct(faixa.min, 0)}–${formatarPct(faixa.max, 0)}` : "—"}
              apoio={sens.estado === "ok" ? t("painel.tela1.cartaoDefinicaoSub", { n: sens.corpo.dados.length }) : undefined}
             
              onAbrir={faixa ? () => setDetalhe("definicoes") : undefined}
            />
          </>
        ) : null}
      </GrupoEntrada>

      <div className="grid gap-3 lg:grid-cols-[minmax(0,1.7fr)_minmax(0,1fr)]">
        <ItemEntrada atraso={0.45} tag="section" className="cartao p-4" aria-labelledby="g-titulo">
          <div className="flex items-start justify-between gap-3">
            <h2 id="g-titulo" className="text-base font-semibold text-tinta">{t(gran === "mes" ? "painel.tela1.graficoTituloMes" : "painel.tela1.graficoTitulo")}</h2>
            <div className="flex shrink-0 items-center gap-3">
              <div role="group" aria-label="Granularidade" className="flex overflow-hidden rounded-lg border border-[#cfc9ee] text-sm">
                {(["mes", "semana"] as const).map((g) => (
                  <button key={g} type="button" aria-pressed={gran === g} onClick={() => setGran(g)} className={`min-h-[2.5rem] px-3 sm:min-h-0 sm:py-0.5 ${gran === g ? "bg-violeta text-papel" : "bg-white text-slate-800 hover:bg-[#f6f4fd]"}`}>
                    {t(g === "semana" ? "painel.tela1.granSemana" : "painel.tela1.granMes")}
                  </button>
                ))}
              </div>
              <button type="button" onClick={() => setDetalhe("grafico")} className="alvo text-sm font-medium text-violeta hover:underline">{t("painel.verDetalhes")}</button>
            </div>
          </div>
          {coortes.estado === "carregando" ? <Estado tipo="carregando" /> : null}
          {coortes.estado === "erro" ? <Estado tipo="erro" mensagem={coortes.mensagem} requestId={coortes.requestId} /> : null}
          {coortes.estado === "ok" && linhas.length === 0 ? <Estado tipo="vazio" /> : null}
          {linhas.length > 0 ? <GraficoTaxa linhas={linhas} altura="h-[17.25rem]" granularidade={gran} marcadas={gran === "semana" ? [...SEMANAS] : []} selecionada={semanaSel} onEscolher={setSemanaSel} /> : null}
          {r && r.periodo_inicio && r.periodo_fim ? <p className="mt-1 text-[11px] text-slate-500" data-testid="fonte-grafico">{t("painel.tela1.fonte", { n: formatarInt(r.usuarios), fonte: t("painel.fonteNome"), periodo: periodoBase(r.periodo_inicio, r.periodo_fim) })}</p> : null}
        </ItemEntrada>

        <ItemEntrada atraso={0.52} tag="section" className="cartao p-4" aria-labelledby="s-titulo">
          <div className="flex items-start justify-between gap-3">
            <h2 id="s-titulo" className="text-base font-semibold text-tinta">{t("painel.tela1.semanasTitulo")}</h2>
            <button type="button" onClick={() => setDetalhe("semana")} className="alvo shrink-0 text-sm font-medium text-violeta hover:underline">{t("painel.verDetalhes")}</button>
          </div>
          <div role="group" aria-label={t("painel.tela1.semanaEscolha")} className="mt-1 flex flex-wrap gap-2">
            {SEMANAS.map((d) => (
              <button key={d} type="button" aria-pressed={semanaSel === d} onClick={() => setSemanaSel(d)} className={`min-h-[2.5rem] rounded-full px-3 text-xs sm:min-h-0 sm:py-0.5 ${semanaSel === d ? "bg-violeta font-medium text-papel" : "bg-[#f1effc] text-slate-800 hover:bg-[#e6e2fa]"}`}>
                {dataBr(d)} · {t(`painel.tela1.semanaMotivo.${d}`)}
              </button>
            ))}
          </div>
          {semana.estado === "carregando" ? <Estado tipo="carregando" /> : null}
          {semana.estado === "erro" ? <Estado tipo="erro" mensagem={semana.mensagem} requestId={semana.requestId} /> : null}
          {semana.estado === "ok" && !rs ? <Estado tipo="vazio" mensagem={t("semana.semResumo")} /> : null}
          {rs && cascata ? (
            <div className="mt-2 space-y-3">
              <DiferencaSemana resumo={rs} />
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
            </div>
          ) : null}
        </ItemEntrada>
      </div>

      {detalhe ? (
        <PainelLateral
          titulo={
            detalhe === "taxa" ? t("painel.tela1.cartaoTaxa")
            : detalhe === "pessoas" ? t("painel.tela1.cartaoPessoas")
            : detalhe === "voltaram" ? t("painel.tela1.cartaoVoltaram")
            : t(detalhe === "grafico" ? "painel.tela1.detalheGrafico" : detalhe === "semana" ? "painel.tela1.detalheSemana" : "painel.tela1.detalheDefinicoes")
          }
          onFechar={() => setDetalhe(null)}
        >
          {INDICADOR[detalhe] && r ? (
            <DetalheIndicador
              indicador={INDICADOR[detalhe]!}
              destaque={{ valor: detalhe === "taxa" ? formatarPct(r.taxa) : formatarInt(detalhe === "pessoas" ? r.usuarios : r.voltaram_7d), rotulo: t(`detalhe.rotulo.${INDICADOR[detalhe]!}`) }}
            />
          ) : null}
          {detalhe === "grafico" ? <DetalheTaxa /> : null}
          {detalhe === "semana" ? <BlocoSemana inicial={semanaSel} /> : null}
          {detalhe === "definicoes" ? <BlocoSensibilidade /> : null}
        </PainelLateral>
      ) : null}
    </div>
  );
}
