"use client";

import { Estado } from "@/components/Estado";
import type { LoteQualidade, Reconciliacao, Validacao } from "@/lib/consultas/qualidade";
import { t } from "@/lib/mensagens";
import { nomeCapitalizado, nomeLegivel, tipoClassificador } from "@/lib/qualidade";
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

/** Dicionário de indicadores (definição, fórmula, denominador, período, fonte e SQL), carregado só quando o painel abre. */
function Dicionario() {
  const r = useApi<Indicador[]>("/api/dicionario");
  const itens = r.estado === "ok" ? r.corpo.dados : [];
  return (
    <section className="cartao p-4">
      <h3 className="text-base font-semibold text-tinta">{t("painel.tela3.detalheDicionario")}</h3>
      {r.estado === "carregando" ? <Estado tipo="carregando" /> : null}
      {r.estado === "erro" ? <Estado tipo="erro" mensagem={r.mensagem} requestId={r.requestId} /> : null}
      <ul className="mt-2 divide-y divide-[#efedf8]">
        {itens.map((i) => (
          <li key={i.indicador} className="py-1.5">
            <details>
              <summary className="cursor-pointer text-sm font-medium text-slate-900">{i.nome_exibicao}</summary>
              <dl className="mt-2 space-y-2 text-sm">
                <Campo rotulo={t("glossario.definicao")}>{i.definicao}</Campo>
                <Campo rotulo={t("glossario.denominador")}>{i.denominador}</Campo>
                <Campo rotulo={t("glossario.periodo")}>{i.periodo_referencia}</Campo>
                <Campo rotulo={t("glossario.limitacoes")}>{i.limitacoes}</Campo>
                <Campo rotulo={t("glossario.formula")}>{i.formula}</Campo>
                <Campo rotulo={t("glossario.fonte")}>{i.fonte}</Campo>
                <Campo rotulo={t("glossario.sql")}>
                  <pre className="overflow-x-auto rounded bg-slate-100 p-2 text-xs">{i.sql_referencia}</pre>
                </Campo>
              </dl>
            </details>
          </li>
        ))}
      </ul>
    </section>
  );
}

function Campo({ rotulo, children }: { rotulo: string; children: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wide text-violeta-escuro">{rotulo}</dt>
      <dd className="mt-0.5 text-slate-900">{children}</dd>
    </div>
  );
}

/** Tudo o que saiu da tela principal e continua acessível: conferências, carga, validação da classificação e dicionário. */
export type SecaoQualidade = "conf" | "carga" | "validacao" | "tudo";

export function DetalheQualidade({ lote, reconciliacao, validacao, secao = "tudo" }: { lote: LoteQualidade | null; reconciliacao: Reconciliacao[]; validacao: Validacao[]; secao?: SecaoQualidade }) {
  const ver = (s: SecaoQualidade) => secao === "tudo" || secao === s;
  return (
    <>
      {ver("conf") ? (
      <section className="cartao p-4">
        <h3 className="text-base font-semibold text-tinta">{t("painel.tela3.detalheConf")}</h3>
        <p className="mt-1 text-sm text-slate-700">{t("dados.confAjuda")}</p>
        {reconciliacao.length === 0 ? (
          <Estado tipo="vazio" mensagem={t("dados.confVazia")} />
        ) : (
          <table className="mt-2 w-full text-left text-sm">
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
                    <span className={c.ok ? "text-[#047857]" : "text-[#8a3a00]"} aria-label={c.ok ? t("dados.confOk") : t("dados.confFalha")}>{c.ok ? "✓" : "✗"}</span> {nomeLegivel(c.metrica)}
                  </th>
                  <td className="py-1 pr-2 text-right">{formatarInt(c.valor_bruto)}</td>
                  <td className="py-1 pr-2 text-right">{formatarInt(c.valor_mart)}</td>
                  <td className="py-1 text-right">{formatarInt(c.diferenca)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
      ) : null}

      {ver("carga") ? (
      <section className="cartao p-4">
        <h3 className="text-base font-semibold text-tinta">{t("painel.tela3.detalheCarga")}</h3>
        {lote ? (
          <ul className="mt-2 space-y-1 text-sm text-slate-800">
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
      ) : null}

      {ver("validacao") ? (
      <section className="cartao p-4">
        <h3 className="text-base font-semibold text-tinta">{t("painel.tela3.detalheValidacao")}</h3>
        <p className="mt-1 text-sm text-slate-700">{t("dados.validacaoAjuda")}</p>
        {validacao.length === 0 ? (
          <Estado tipo="vazio" mensagem={t("dados.validacaoVazia")} />
        ) : (
          <ul className="mt-2 space-y-1 text-sm text-slate-800">
            {validacao.map((v) => {
              const tipo = tipoClassificador(v.modelo);
              const kappa = v.kappa === null ? "—" : v.kappa.toLocaleString("pt-BR", { maximumFractionDigits: 2 });
              const comum = { nome: nomeCapitalizado(v.classificador), acuracia: formatarPct(v.acuracia), n: formatarInt(v.n), kappa };
              return (
                <li key={`${v.classificador}|${v.modelo ?? ""}|${v.versao_prompt ?? ""}`}>
                  {tipo === null
                    ? t("dados.validacaoLinhaSemTipo", comum)
                    : t("dados.validacaoLinha", { ...comum, tipo: tipo === "ia" ? t("dados.validacaoTipoIa") : t("dados.validacaoTipoRegras"), usado: tipo === "ia" ? t("dados.validacaoUsado") : "" })}
                </li>
              );
            })}
          </ul>
        )}
      </section>
      ) : null}

      {secao === "tudo" ? <Dicionario /> : null}
    </>
  );
}
