"use client";

import { Estado } from "@/components/Estado";
import type { LoteQualidade, Problema, Reconciliacao, Validacao } from "@/lib/consultas/qualidade";
import { t, todasAsMensagens } from "@/lib/mensagens";
import { nomeCapitalizado, nomeLegivel, tipoClassificador, traduzirTermos, veredicto } from "@/lib/qualidade";
import { formatarDataHora, formatarInt, formatarPct } from "@/lib/regras";
import { useApi } from "@/lib/useApi";

interface Qualidade {
  lote: LoteQualidade | null;
  reconciliacao: Reconciliacao[];
  problemas: Problema[];
  validacao: Validacao[];
}

const ITENS = ["1", "2", "3"];
const TERMOS = (todasAsMensagens.dados as { termosTecnicos: Record<string, { inline: string; nota: string }> }).termosTecnicos;

/** Tela 3 — Confiança nos dados. */
export default function PaginaDados() {
  const r = useApi<Qualidade>("/api/qualidade");
  const q = r.estado === "ok" ? r.corpo.dados : null;
  const ver = q ? veredicto(q.lote !== null, q.reconciliacao) : null;
  const frase =
    ver === null
      ? ""
      : ver.v === "ok"
        ? t("dados.respostaOk")
        : ver.v === "falha"
          ? t("dados.respostaFalha", { k: ver.falhas, m: ver.total })
          : ver.v === "sem_conferencia"
            ? t("dados.respostaSemConf")
            : t("dados.respostaSemLote");

  return (
    <div className="space-y-6">
      <header>
        <h1 className="titulo-tela">{t("dados.pergunta")}</h1>
        <p className="mt-3 max-w-3xl text-lg leading-snug text-slate-700" data-testid="frase-confianca">{frase}</p>
      </header>

      {r.estado === "carregando" ? <Estado tipo="carregando" /> : null}
      {r.estado === "erro" ? <Estado tipo="erro" mensagem={r.mensagem} requestId={r.requestId} /> : null}

      {q ? (
        <>
          <section className="cartao p-4" aria-labelledby="h-carga">
            <h2 id="h-carga" className="text-base font-semibold text-slate-900">{t("dados.cargaTitulo")}</h2>
            {q.lote ? (
              <ul className="mt-2 space-y-1 text-sm text-slate-800">
                <li>{t("dados.cargaQuando", { data: formatarDataHora(q.lote.terminado_em) ?? "—" })}</li>
                <li>{t("dados.cargaLinhas", { n: formatarInt(q.lote.linhas_lidas) })}</li>
                <li>{t("dados.cargaGravadas", { n: formatarInt(q.lote.linhas_gravadas) })}</li>
                <li>{t("dados.cargaRejeitadas", { n: formatarInt(q.lote.linhas_rejeitadas) })}</li>
                <li className="text-xs text-slate-600">{t("dados.cargaRejeitadasAjuda")}</li>
              </ul>
            ) : (
              <Estado tipo="vazio" mensagem={t("dados.cargaVazia")} />
            )}
          </section>

          <section className="cartao p-4" aria-labelledby="h-conf">
            <h2 id="h-conf" className="text-base font-semibold text-slate-900">{t("dados.confTitulo")}</h2>
            <p className="mt-1 text-sm text-slate-700">{t("dados.confAjuda")}</p>
            {q.reconciliacao.length === 0 ? (
              <Estado tipo="vazio" mensagem={t("dados.confVazia")} />
            ) : (
              <ul className="mt-2 divide-y divide-slate-100">
                {q.reconciliacao.map((c) => (
                  <li key={c.metrica} className="py-2 text-sm" data-ok={c.ok}>
                    <span className={`mr-2 rounded px-2 py-0.5 text-xs font-medium ${c.ok ? "bg-emerald-50 text-slate-900" : "bg-red-50 text-slate-900"}`}>
                      {c.ok ? `✓ ${t("dados.confOk")}` : `✗ ${t("dados.confFalha")}`}
                    </span>
                    <span className="font-medium text-slate-900">{nomeLegivel(c.metrica)}</span>
                    <span className="block text-xs text-slate-600">
                      {t("dados.confLinha", { bruto: formatarInt(c.valor_bruto), mart: formatarInt(c.valor_mart), dif: formatarInt(c.diferenca) })}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="cartao p-4" aria-labelledby="h-prob">
            <h2 id="h-prob" className="text-base font-semibold text-slate-900">{t("dados.problemasTitulo")}</h2>
            <p className="mt-1 text-sm text-slate-700">{t("dados.problemasAjuda")}</p>
            {q.problemas.length === 0 ? (
              <Estado tipo="vazio" mensagem={t("dados.problemasVazio")} />
            ) : (
              <ul className="mt-2 divide-y divide-slate-100">
                {q.problemas.map((p) => {
                  const prob = traduzirTermos(p.problema, TERMOS);
                  const trat = traduzirTermos(p.tratamento ?? "", TERMOS);
                  const tecnicos = [...prob.tecnicos, ...trat.tecnicos];
                  return (
                  <li key={p.problema} className="py-2 text-sm">
                    <div className="font-medium text-slate-900">{prob.texto}</div>
                    <div className="text-xs text-slate-700">{t("dados.problemaContagem", { n: formatarInt(p.contagem), pct: formatarPct(p.percentual) })}</div>
                    {p.tratamento ? (
                      <div className="mt-0.5 text-xs text-slate-800">
                        <span className="font-medium">{t("dados.tratamento")}:</span> {trat.texto}
                      </div>
                    ) : null}
                    {tecnicos.length > 0 ? (
                      <details className="mt-0.5 text-xs text-slate-600">
                        <summary className="cursor-pointer">{t("dados.nomesTecnicosTitulo")}</summary>
                        <ul className="mt-1 list-disc pl-5">
                          {tecnicos.map((x) => <li key={x.termo}><code>{x.termo}</code>: {x.nota}</li>)}
                        </ul>
                      </details>
                    ) : null}
                  </li>
                  );
                })}
              </ul>
            )}
          </section>

          <section className="cartao p-4" aria-labelledby="h-val">
            <h2 id="h-val" className="text-base font-semibold text-slate-900">{t("dados.validacaoTitulo")}</h2>
            <p className="mt-1 text-sm text-slate-700">{t("dados.validacaoAjuda")}</p>
            {q.validacao.length === 0 ? (
              <Estado tipo="vazio" mensagem={t("dados.validacaoVazia")} />
            ) : (
              <ul className="mt-2 space-y-1 text-sm text-slate-800">
                {q.validacao.map((v) => {
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
        </>
      ) : null}

      <section className="cartao p-4" aria-labelledby="h-painel">
        <h2 id="h-painel" className="text-base font-semibold text-slate-900">{t("dados.painelTitulo")}</h2>
        <div className="mt-2 grid gap-4 sm:grid-cols-2">
          <div>
            <h3 className="text-sm font-semibold text-slate-900">{t("dados.mostra")}</h3>
            <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-slate-800">
              {ITENS.map((i) => <li key={i}>{t(`dados.mostraItens.${i}`)}</li>)}
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-900">{t("dados.nunca")}</h3>
            <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-slate-800">
              {ITENS.map((i) => <li key={i}>{t(`dados.nuncaItens.${i}`)}</li>)}
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}
