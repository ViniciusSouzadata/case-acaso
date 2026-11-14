"use client";

import { useState } from "react";
import { CartaoKpi } from "@/components/CartaoKpi";
import { BarraCrescente } from "@/components/movimento/Barra";
import { BlocoBlur, BlurTexto } from "@/components/movimento/BlurTexto";
import { GrupoEntrada, ItemEntrada } from "@/components/movimento/Entrada";
import { DestacaNumeros } from "@/components/DestacaNumeros";
import { DetalheQualidade, type SecaoQualidade } from "@/components/DetalheQualidade";
import { Estado } from "@/components/Estado";
import { PainelLateral } from "@/components/PainelLateral";
import type { LoteQualidade, Problema, Reconciliacao, Validacao } from "@/lib/consultas/qualidade";
import { t, todasAsMensagens } from "@/lib/mensagens";
import { acertoIA, fraseConfianca, nomeProblema, unidadeProblema } from "@/lib/painel";
import { traduzirTermos, veredicto } from "@/lib/qualidade";
import { formatarInt, formatarPct } from "@/lib/regras";
import { useApi } from "@/lib/useApi";

interface Qualidade {
  lote: LoteQualidade | null;
  reconciliacao: Reconciliacao[];
  problemas: Problema[];
  validacao: Validacao[];
}

const TERMOS = (todasAsMensagens.dados as { termosTecnicos: Record<string, { inline: string; nota: string }> }).termosTecnicos;
const LINHAS_INICIAIS = 5;
const ITENS = ["1", "2", "3"];
const TITULOS: Record<SecaoQualidade, string> = {
  conf: t("painel.tela3.detalheConf"),
  carga: t("painel.tela3.detalheCarga"),
  recusa: t("painel.tela3.cartaoRecusa"),
  assunto: t("painel.tela3.cartaoTema"),
  dicionario: t("painel.tela3.dicionarioTitulo"),
};

/** Tela 3 — Confiança nos dados, em formato de painel: 4 cartões, barras de problemas e o que o painel mostra e nunca mostra. */
export default function PaginaDados() {
  const r = useApi<Qualidade>("/api/qualidade");
  const q = r.estado === "ok" ? r.corpo.dados : null;
  const [detalhe, setDetalhe] = useState<SecaoQualidade | null>(null);
  const [problema, setProblema] = useState<Problema | null>(null);
  const [todos, setTodos] = useState(false);

  const ver = q ? veredicto(q.lote !== null, q.reconciliacao) : null;
  const resposta = ver ? fraseConfianca(ver.v, ver.total, ver.falhas, q?.lote?.linhas_rejeitadas ?? null) : null;
  const batem = q ? q.reconciliacao.filter((c) => c.ok).length : 0;
  const recusa = q ? acertoIA(q.validacao, "recusa") : null;
  const tema = q ? acertoIA(q.validacao, "tema") : null;

  // Barras: só problemas medidos em % de conversas, do maior para o menor.
  const barras = q ? q.problemas.filter((p) => unidadeProblema(p.problema) === "conversas").sort((a, b) => (b.percentual ?? 0) - (a.percentual ?? 0)) : [];
  const visiveis = todos ? barras : barras.slice(0, LINHAS_INICIAIS);
  const maximo = Math.max(...barras.map((p) => p.percentual ?? 0), 0.0001);
  const outros = q ? q.problemas.filter((p) => unidadeProblema(p.problema) === "semanas") : [];

  return (
    <div className="space-y-4">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <BlurTexto className="titulo-painel" texto={t("painel.tela3.titulo")} />
          <BlocoBlur className={`mt-1 max-w-3xl text-base ${resposta && !resposta.ok ? "font-medium text-[#8a3a00]" : "text-slate-700"}`} data-testid="frase-confianca">
            {resposta ? <DestacaNumeros texto={resposta.frase} /> : ""}
          </BlocoBlur>
        </div>
        {q ? (
          <button type="button" onClick={() => setDetalhe("dicionario")} className="alvo text-sm font-medium text-violeta hover:underline">
            {t("painel.tela3.dicionarioLink")}
          </button>
        ) : null}
      </header>

      {r.estado === "carregando" ? <Estado tipo="carregando" /> : null}
      {r.estado === "erro" ? <Estado tipo="erro" mensagem={r.mensagem} requestId={r.requestId} /> : null}

      {q ? (
        <>
          <GrupoEntrada tag="section" aria-label="Números principais" className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <CartaoKpi
              escuro
              rotulo={t("painel.tela3.cartaoConf")}
              valor={ver && ver.total > 0 ? `${batem} de ${ver.total}` : "—"}
              apoio={t("painel.tela3.cartaoConfSub")}
              testid="conferencias"
              onAbrir={() => setDetalhe("conf")}
              extra={ver && ver.total > 0 ? <span className="text-lg font-semibold text-papel" aria-label={ver.falhas === 0 ? t("dados.confOk") : t("dados.confFalha")}>{ver.falhas === 0 ? "✓" : "✗"}</span> : null}
            />
            <CartaoKpi
              rotulo={t("painel.tela3.cartaoLidas")}
              valor={q.lote ? formatarInt(q.lote.linhas_lidas) : "—"}
              apoio={q.lote ? t("painel.tela3.cartaoLidasSub", { n: formatarInt(q.lote.linhas_rejeitadas) }) : undefined}
              animar={q.lote && q.lote.linhas_lidas !== null ? { valor: q.lote.linhas_lidas, formato: (n) => formatarInt(Math.round(n)) } : undefined}
              onAbrir={() => setDetalhe("carga")}
            />
            <CartaoKpi
              rotulo={t("painel.tela3.cartaoRecusa")}
              valor={recusa ? formatarPct(recusa.acuracia, 0) : "—"}
              apoio={recusa ? t("painel.tela3.cartaoAcertoSub", { n: formatarInt(recusa.n) }) : undefined}
              onAbrir={() => setDetalhe("recusa")}
            />
            <CartaoKpi
              rotulo={t("painel.tela3.cartaoTema")}
              valor={tema ? formatarPct(tema.acuracia, 0) : "—"}
              apoio={tema ? t("painel.tela3.cartaoAcertoSub", { n: formatarInt(tema.n) }) : undefined}
              onAbrir={() => setDetalhe("assunto")}
              selo={tema ? <span className="inline-block rounded-full bg-[#ffe9db] px-2 py-0.5 text-xs font-medium text-[#8a3a00]">{t("painel.tela3.seloTema")}</span> : null}
            />
          </GrupoEntrada>

          <div className="grid gap-3 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
            <ItemEntrada atraso={0.45} tag="section" className="cartao p-4" aria-labelledby="barras-titulo">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <h2 id="barras-titulo" className="text-base font-semibold text-tinta">{t("painel.tela3.barrasTitulo")}</h2>
                <span className="text-xs text-slate-600">{t("painel.tela3.barrasSub")}</span>
              </div>
              {barras.length === 0 ? <Estado tipo="vazio" mensagem={t("dados.problemasVazio")} /> : null}
              <ul className={`mt-2 ${todos ? "max-h-56 overflow-y-auto pr-1" : ""}`}>
                {visiveis.map((p, i) => (
                  <li key={p.problema} data-problema={nomeProblema(p.problema)}>
                    <button type="button" onClick={() => setProblema(p)} className="group grid min-h-[2.5rem] w-full grid-cols-[minmax(0,9rem)_minmax(0,1fr)_3.5rem] items-center gap-x-3 rounded-lg px-2 py-2 text-left transition-colors hover:bg-[#ece8fc] focus-visible:outline focus-visible:outline-2 focus-visible:outline-violeta sm:grid-cols-[11rem_minmax(0,1fr)_3.5rem]">
                      <span className="truncate text-sm font-medium text-tinta">{nomeProblema(p.problema)}</span>
                      <span className="relative block h-4 rounded bg-[#f1effc]" aria-hidden>
                        <BarraCrescente indice={i} className="absolute inset-y-0 left-0 rounded bg-violeta transition-colors group-hover:bg-violeta-escuro" style={{ width: `${Math.max((p.percentual ?? 0) > 0 ? 1.5 : 0, ((p.percentual ?? 0) / maximo) * 100)}%` }} />
                      </span>
                      <span className="text-right font-display text-sm font-semibold text-slate-800">{formatarPct(p.percentual)}</span>
                    </button>
                  </li>
                ))}
                {outros.map((p) => (
                  <li key={p.problema} data-problema={nomeProblema(p.problema)}>
                    <button type="button" onClick={() => setProblema(p)} className="grid min-h-[2.5rem] w-full grid-cols-[minmax(0,1fr)_auto] items-center gap-x-3 rounded-lg px-2 py-2 text-left transition-colors hover:bg-[#ece8fc] focus-visible:outline focus-visible:outline-2 focus-visible:outline-violeta">
                      <span className="text-sm font-medium text-tinta">{nomeProblema(p.problema)}</span>
                      <span className="text-right font-display text-sm font-semibold text-slate-800">{t("painel.tela3.semanasLinha", { n: formatarInt(p.contagem) })}</span>
                    </button>
                  </li>
                ))}
              </ul>
              {barras.length > LINHAS_INICIAIS ? (
                <button type="button" onClick={() => setTodos(!todos)} className="alvo mt-1 px-2 text-sm font-medium text-violeta hover:underline">
                  {todos ? t("painel.tela3.mostrarMenos") : t("painel.tela3.mostrarTodos", { n: barras.length })}
                </button>
              ) : null}
            </ItemEntrada>

            <ItemEntrada atraso={0.52} tag="section" className="cartao p-4" aria-labelledby="painel-titulo">
              <h2 id="painel-titulo" className="sr-only">{t("dados.painelTitulo")}</h2>
              <h3 className="text-sm font-semibold text-tinta">{t("painel.tela3.mostraTitulo")}</h3>
              <ul className="mt-1 space-y-1 text-sm text-slate-800">
                {ITENS.map((i) => (
                  <li key={i} className="flex gap-2"><span aria-hidden className="font-semibold text-[#047857]">✓</span>{t(`painel.tela3.mostra${i}`)}</li>
                ))}
              </ul>
              <h3 className="mt-4 text-sm font-semibold text-tinta">{t("painel.tela3.nuncaTitulo")}</h3>
              <ul className="mt-1 space-y-1 text-sm text-slate-800">
                {ITENS.map((i) => (
                  <li key={i} className="flex gap-2"><span aria-hidden className="font-semibold text-[#8a3a00]">✕</span>{t(`painel.tela3.nunca${i}`)}</li>
                ))}
              </ul>
            </ItemEntrada>
          </div>
        </>
      ) : null}

      {problema ? (
        <PainelLateral titulo={nomeProblema(problema.problema)} onFechar={() => setProblema(null)}>
          {(() => {
            const prob = traduzirTermos(problema.problema, TERMOS);
            const trat = traduzirTermos(problema.tratamento ?? "", TERMOS);
            const tecnicos = [...prob.tecnicos, ...trat.tecnicos];
            return (
              <div className="cartao space-y-2 p-4 text-sm text-slate-800">
                <p className="font-medium text-tinta">{prob.texto}</p>
                <p>{t(unidadeProblema(problema.problema) === "semanas" ? "painel.tela3.semanasContagem" : "painel.tela3.problemaContagem", { n: formatarInt(problema.contagem), pct: formatarPct(problema.percentual) })}</p>
                {problema.tratamento ? <p><span className="font-medium">{t("painel.tela3.oQueFizemos")}:</span> {trat.texto}</p> : null}
                {tecnicos.length > 0 ? (
                  <details>
                    <summary className="cursor-pointer text-xs text-slate-700">{t("dados.nomesTecnicosTitulo")}</summary>
                    <ul className="mt-1 list-disc pl-5 text-xs text-slate-700">
                      {tecnicos.map((x) => <li key={x.termo}><code>{x.termo}</code>: {x.nota}</li>)}
                    </ul>
                  </details>
                ) : null}
              </div>
            );
          })()}
        </PainelLateral>
      ) : null}

      {detalhe && q ? (
        <PainelLateral titulo={TITULOS[detalhe]} onFechar={() => setDetalhe(null)}>
          <DetalheQualidade lote={q.lote} reconciliacao={q.reconciliacao} validacao={q.validacao} secao={detalhe} />
        </PainelLateral>
      ) : null}
    </div>
  );
}
