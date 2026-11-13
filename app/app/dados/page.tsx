"use client";

import { useState } from "react";
import { CartaoKpi } from "@/components/CartaoKpi";
import { DetalheQualidade } from "@/components/DetalheQualidade";
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
const LINHAS_INICIAIS = 6;
const ITENS = ["1", "2", "3"];

/** Tela 3 — Confiança nos dados, em formato de painel: 4 cartões, barras de problemas e o que o painel mostra e nunca mostra. */
export default function PaginaDados() {
  const r = useApi<Qualidade>("/api/qualidade");
  const q = r.estado === "ok" ? r.corpo.dados : null;
  const [detalhe, setDetalhe] = useState(false);
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
          <h1 className="titulo-painel">{t("painel.tela3.titulo")}</h1>
          <p className={`mt-1 max-w-3xl text-base ${resposta && !resposta.ok ? "font-medium text-[#8a3a00]" : "text-slate-700"}`} data-testid="frase-confianca">
            {resposta?.frase ?? ""}
          </p>
        </div>
        {q ? (
          <button type="button" onClick={() => setDetalhe(true)} className="rounded-lg border border-violeta px-3 py-1.5 text-sm font-medium text-violeta hover:bg-violeta hover:text-papel">
            {t("painel.verDetalhes")}
          </button>
        ) : null}
      </header>

      {r.estado === "carregando" ? <Estado tipo="carregando" /> : null}
      {r.estado === "erro" ? <Estado tipo="erro" mensagem={r.mensagem} requestId={r.requestId} /> : null}

      {q ? (
        <>
          <section aria-label="Números principais" className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <CartaoKpi
              rotulo={t("painel.tela3.cartaoConf")}
              valor={ver && ver.total > 0 ? `${batem} de ${ver.total}` : "—"}
              apoio={t("painel.tela3.cartaoConfSub")}
              testid="conferencias"
              extra={ver && ver.total > 0 ? <span className={`text-lg font-semibold ${ver.falhas === 0 ? "text-[#047857]" : "text-[#8a3a00]"}`} aria-label={ver.falhas === 0 ? t("dados.confOk") : t("dados.confFalha")}>{ver.falhas === 0 ? "✓" : "✗"}</span> : null}
            />
            <CartaoKpi
              rotulo={t("painel.tela3.cartaoLidas")}
              valor={q.lote ? formatarInt(q.lote.linhas_lidas) : "—"}
              apoio={q.lote ? t("painel.tela3.cartaoLidasSub", { n: formatarInt(q.lote.linhas_rejeitadas) }) : undefined}
            />
            <CartaoKpi
              rotulo={t("painel.tela3.cartaoRecusa")}
              valor={recusa ? formatarPct(recusa.acuracia, 0) : "—"}
              apoio={recusa ? t("painel.tela3.cartaoAcertoSub", { n: formatarInt(recusa.n) }) : undefined}
            />
            <CartaoKpi
              rotulo={t("painel.tela3.cartaoTema")}
              valor={tema ? formatarPct(tema.acuracia, 0) : "—"}
              apoio={tema ? t("painel.tela3.cartaoAcertoSub", { n: formatarInt(tema.n) }) : undefined}
              selo={tema ? <span className="inline-block rounded-full bg-[#ffe9db] px-2 py-0.5 text-xs font-medium text-[#8a3a00]">{t("painel.tela3.seloTema")}</span> : null}
            />
          </section>

          <div className="grid gap-3 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
            <section className="cartao p-4" aria-labelledby="barras-titulo">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <h2 id="barras-titulo" className="text-base font-semibold text-tinta">{t("painel.tela3.barrasTitulo")}</h2>
                <span className="text-xs text-slate-600">{t("painel.tela3.barrasSub")}</span>
              </div>
              {barras.length === 0 ? <Estado tipo="vazio" mensagem={t("dados.problemasVazio")} /> : null}
              <ul className={`mt-2 ${todos ? "max-h-56 overflow-y-auto pr-1" : ""}`}>
                {visiveis.map((p) => (
                  <li key={p.problema} className="entra" data-problema={nomeProblema(p.problema)}>
                    <button type="button" onClick={() => setProblema(p)} className="grid w-full grid-cols-[minmax(0,9rem)_minmax(0,1fr)_3.5rem] items-center gap-x-3 rounded-lg px-2 py-1 text-left hover:bg-[#f6f4fd] sm:grid-cols-[11rem_minmax(0,1fr)_3.5rem]">
                      <span className="truncate text-sm font-medium text-tinta">{nomeProblema(p.problema)}</span>
                      <span className="relative block h-3 rounded bg-[#f1effc]" aria-hidden>
                        <span className="absolute inset-y-0 left-0 rounded bg-violeta" style={{ width: `${Math.max((p.percentual ?? 0) > 0 ? 1.5 : 0, ((p.percentual ?? 0) / maximo) * 100)}%` }} />
                      </span>
                      <span className="text-right font-display text-sm font-semibold text-slate-800">{formatarPct(p.percentual)}</span>
                    </button>
                  </li>
                ))}
              </ul>
              {barras.length > LINHAS_INICIAIS ? (
                <button type="button" onClick={() => setTodos(!todos)} className="mt-1 px-2 text-sm font-medium text-violeta hover:underline">
                  {todos ? t("painel.tela3.mostrarMenos") : t("painel.tela3.mostrarTodos", { n: barras.length })}
                </button>
              ) : null}
            </section>

            <section className="cartao p-4" aria-labelledby="painel-titulo">
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
            </section>
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
                <p>{t("painel.tela3.problemaContagem", { n: formatarInt(problema.contagem), pct: formatarPct(problema.percentual) })}</p>
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
        <PainelLateral titulo={t("painel.tela3.detalheTitulo")} onFechar={() => setDetalhe(false)}>
          <DetalheQualidade lote={q.lote} reconciliacao={q.reconciliacao} validacao={q.validacao} />
          {outros.length > 0 ? (
            <section className="cartao p-4 text-sm text-slate-800">
              {outros.map((p) => (
                <p key={p.problema}>
                  <span className="font-medium">{nomeProblema(p.problema)}:</span> {t("painel.tela3.semanasContagem", { n: formatarInt(p.contagem), pct: formatarPct(p.percentual) })}. {p.tratamento}
                </p>
              ))}
            </section>
          ) : null}
        </PainelLateral>
      ) : null}
    </div>
  );
}
