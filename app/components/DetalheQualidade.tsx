"use client";

import { useState } from "react";
import { Estado } from "@/components/Estado";
import { CampoTecnico, Destaque, Frases, Tecnico, frasesDe } from "@/components/painel/Blocos";
import type { LoteQualidade, Reconciliacao, Validacao } from "@/lib/consultas/qualidade";
import { t } from "@/lib/mensagens";
import { acertoIA } from "@/lib/painel";
import { nomeLegivel, tipoClassificador } from "@/lib/qualidade";
import { formatarDataHora, formatarInt, formatarPct } from "@/lib/regras";
import { useApi } from "@/lib/useApi";

interface Indicador {
  indicador: string;
  nome_exibicao: string;
  definicao: string;
  formula: string;
  denominador: string;
  periodo_referencia: string;
  fonte: string;
  sql_referencia: string;
  limitacoes: string;
}

/** Nome em linguagem comum de um número conferido; sem tradução cadastrada, cai no nome interno sem sublinhados. */
export function nomeConferencia(metrica: string): string {
  const chave = `painel.tela3.nomesConferencia.${metrica}`;
  const r = t(chave);
  return r === chave ? nomeLegivel(metrica) : r;
}

/** Dicionário dos números: uma lista em que só um termo fica aberto por vez; cada um mostra a definição e, recolhido, o técnico. */
export function Dicionario() {
  const r = useApi<Indicador[]>("/api/dicionario");
  const [aberto, setAberto] = useState<string | null>(null);
  const itens = r.estado === "ok" ? r.corpo.dados : [];
  return (
    <section className="cartao p-4" data-testid="dicionario">
      {r.estado === "carregando" ? <Estado tipo="carregando" /> : null}
      {r.estado === "erro" ? <Estado tipo="erro" mensagem={r.mensagem} requestId={r.requestId} /> : null}
      <ul className="divide-y divide-[#efedf8]">
        {itens.map((i) => {
          const aqui = aberto === i.indicador;
          return (
            <li key={i.indicador}>
              <button type="button" aria-expanded={aqui} onClick={() => setAberto(aqui ? null : i.indicador)} className="flex min-h-10 w-full items-center justify-between gap-2 rounded-lg px-1 py-1.5 text-left text-sm font-medium text-tinta hover:bg-[#ece8fc]">
                <span>{i.nome_exibicao}</span>
                <span aria-hidden className="text-slate-400">{aqui ? "−" : "+"}</span>
              </button>
              {aqui ? (
                <div className="space-y-2 px-1 pb-3">
                  <Frases itens={[i.definicao]} />
                  <Tecnico>
                    <CampoTecnico rotulo={t("glossario.denominador")}>{i.denominador}</CampoTecnico>
                    <CampoTecnico rotulo={t("glossario.periodo")}>{i.periodo_referencia}</CampoTecnico>
                    <CampoTecnico rotulo={t("glossario.limitacoes")}>{i.limitacoes}</CampoTecnico>
                    <CampoTecnico rotulo={t("glossario.formula")}>{i.formula}</CampoTecnico>
                    <CampoTecnico rotulo={t("glossario.fonte")}>{i.fonte}</CampoTecnico>
                    <CampoTecnico rotulo={t("glossario.sql")}>
                      <pre className="overflow-x-auto rounded bg-slate-100 p-2 text-xs">{i.sql_referencia}</pre>
                    </CampoTecnico>
                  </Tecnico>
                </div>
              ) : null}
            </li>
          );
        })}
      </ul>
    </section>
  );
}

/** Cada cartão da Tela 3 abre o seu pedaço: conferências, carga, a conferência da IA (recusa ou assunto) e o dicionário. */
export type SecaoQualidade = "conf" | "carga" | "recusa" | "assunto" | "dicionario";

/** Frases da conferência manual de um classificador de IA (recusa ou assunto) e, recolhido, o resultado de cada versão. */
function ConferenciaIA({ validacao, qual }: { validacao: Validacao[]; qual: "recusa" | "tema" }) {
  const ia = acertoIA(validacao, qual);
  const deste = validacao.filter((v) => v.classificador === qual);
  if (!ia) return <Estado tipo="vazio" mensagem={t("dados.validacaoVazia")} />;
  const rotulo = qual === "recusa" ? "recusa" : "assunto";
  return (
    <section className="cartao space-y-3 p-4">
      <Destaque valor={formatarPct(ia.acuracia, 0)} rotulo={t(`painel.tela3.acerto.${rotulo}`)} />
      <Frases itens={frasesDe(`painel.tela3.validacao.${rotulo}`, { n: formatarInt(ia.n), pct: formatarPct(ia.acuracia, 0) })} />
      <Tecnico>
        {deste.map((v) => {
          const tipo = tipoClassificador(v.modelo);
          const kappa = v.kappa === null ? "—" : v.kappa.toLocaleString("pt-BR", { maximumFractionDigits: 2 });
          return (
            <p key={`${v.modelo ?? ""}|${v.versao_prompt ?? ""}`}>
              {t(tipo === "regras" ? "painel.tela3.validacaoTecnicoRegras" : "painel.tela3.validacaoTecnicoIa", { pct: formatarPct(v.acuracia), n: formatarInt(v.n), kappa })}
            </p>
          );
        })}
      </Tecnico>
    </section>
  );
}

export function DetalheQualidade({ lote, reconciliacao, validacao, secao }: { lote: LoteQualidade | null; reconciliacao: Reconciliacao[]; validacao: Validacao[]; secao: SecaoQualidade }) {
  if (secao === "dicionario") return <Dicionario />;
  if (secao === "recusa") return <ConferenciaIA validacao={validacao} qual="recusa" />;
  if (secao === "assunto") return <ConferenciaIA validacao={validacao} qual="tema" />;

  if (secao === "conf") {
    return (
      <section className="cartao space-y-3 p-4">
        <p className="text-sm text-slate-800">{t("dados.confAjuda")}</p>
        {reconciliacao.length === 0 ? (
          <Estado tipo="vazio" mensagem={t("dados.confVazia")} />
        ) : (
          <>
            <table className="w-full text-left text-sm">
              <caption className="sr-only">{t("painel.tela3.detalheConf")}</caption>
              <thead>
                <tr className="border-b border-slate-300 text-xs text-slate-700">
                  <th scope="col" className="py-1 pr-2 font-medium">{t("painel.tela3.colMetrica")}</th>
                  <th scope="col" className="py-1 pr-2 text-right font-medium">{t("painel.tela3.colOrigem")}</th>
                  <th scope="col" className="py-1 pr-2 text-right font-medium">{t("painel.tela3.colPainel")}</th>
                  <th scope="col" className="py-1 text-right font-medium">{t("painel.tela3.colDif")}</th>
                </tr>
              </thead>
              <tbody>
                {reconciliacao.map((c) => (
                  <tr key={c.metrica} data-ok={c.ok} className="border-b border-slate-100">
                    <th scope="row" className="py-1 pr-2 font-normal">
                      <span className={c.ok ? "text-[#047857]" : "text-[#8a3a00]"} aria-label={c.ok ? t("dados.confOk") : t("dados.confFalha")}>{c.ok ? "✓" : "✗"}</span> {nomeConferencia(c.metrica)}
                    </th>
                    <td className="py-1 pr-2 text-right">{formatarInt(c.valor_bruto)}</td>
                    <td className="py-1 pr-2 text-right">{formatarInt(c.valor_mart)}</td>
                    <td className="py-1 text-right">{formatarInt(c.diferenca)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <Tecnico>
              <ul className="text-xs text-slate-800">
                {reconciliacao.map((c) => (
                  <li key={c.metrica}>
                    {nomeConferencia(c.metrica)}: <code>{c.metrica}</code> (tolerância {formatarInt(c.tolerancia)})
                  </li>
                ))}
              </ul>
            </Tecnico>
          </>
        )}
      </section>
    );
  }

  // carga
  return (
    <section className="cartao p-4">
      {lote ? (
        <ul className="space-y-1 text-sm text-slate-800">
          <li>{t("dados.cargaQuando", { data: formatarDataHora(lote.terminado_em) ?? "—" })}</li>
          <li>{t("dados.cargaLinhas", { n: formatarInt(lote.linhas_lidas) })}</li>
          <li>{t("dados.cargaGravadas", { n: formatarInt(lote.linhas_gravadas) })}</li>
          <li>{t("dados.cargaRejeitadas", { n: formatarInt(lote.linhas_rejeitadas) })}</li>
          <li className="text-xs text-slate-600">{t("dados.cargaRejeitadasAjuda")}</li>
        </ul>
      ) : (
        <Estado tipo="vazio" mensagem={t("dados.cargaVazia")} />
      )}
    </section>
  );
}
