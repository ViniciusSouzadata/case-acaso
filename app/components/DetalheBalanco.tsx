"use client";

import { useState } from "react";
import { Estado } from "@/components/Estado";
import { t } from "@/lib/mensagens";
import { LIMITE_BALANCO } from "@/lib/regras";
import { useApi } from "@/lib/useApi";

const TRATAMENTOS = ["recusa", "idioma_divergente", "modelo_familia"] as const;

interface Balanco {
  covariavel: string;
  dp_antes: number | null;
  dp_depois: number | null;
}

const num = (x: number | null) => (x === null ? "—" : x.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }));

/** Detalhe recolhível: balanço antes/depois (aqui os termos técnicos podem aparecer). */
export function DetalheBalanco() {
  const [tratamento, setTratamento] = useState<string>(TRATAMENTOS[0]);
  const [aberto, setAberto] = useState(false);
  const r = useApi<Balanco[]>(aberto ? `/api/fatores/balanco?tratamento=${encodeURIComponent(tratamento)}` : null);
  const linhas = r.estado === "ok" ? r.corpo.dados : [];

  return (
    <details className="rounded-xl border border-slate-200 bg-papel shadow-sm p-4" onToggle={(e) => setAberto((e.currentTarget as HTMLDetailsElement).open)}>
      <summary className="cursor-pointer text-sm font-medium text-azul">{t("fatores.balancoResumo")}</summary>
      <p className="mt-2 text-xs text-slate-700">{t("fatores.balancoIntro", { limite: String(LIMITE_BALANCO).replace(".", ",") })}</p>
      <label className="mt-2 block text-xs text-slate-700">
        {t("fatores.balancoEscolha")}{" "}
        <select value={tratamento} onChange={(e) => setTratamento(e.target.value)} className="ml-1 rounded border border-slate-300 bg-white px-2 py-1 text-sm">
          {TRATAMENTOS.map((x) => (
            <option key={x} value={x}>{t(`fatores.tratamentos.${x}`)}</option>
          ))}
        </select>
      </label>
      {aberto && r.estado === "carregando" ? <Estado tipo="carregando" /> : null}
      {r.estado === "erro" ? <Estado tipo="erro" mensagem={r.mensagem} requestId={r.requestId} /> : null}
      {r.estado === "ok" && linhas.length === 0 ? <Estado tipo="vazio" mensagem={t("fatores.balancoVazio")} /> : null}
      {linhas.length > 0 ? (
        <table className="mt-2 w-full text-left text-xs">
          <caption className="sr-only">{t("fatores.balancoResumo")}</caption>
          <thead>
            <tr className="border-b border-slate-300">
              <th scope="col" className="py-1 pr-2 font-medium">{t("fatores.colCovariavel")}</th>
              <th scope="col" className="py-1 pr-2 font-medium">{t("fatores.colAntes")}</th>
              <th scope="col" className="py-1 pr-2 font-medium">{t("fatores.colDepois")}</th>
              <th scope="col" className="py-1 font-medium">{t("fatores.colSituacao")}</th>
            </tr>
          </thead>
          <tbody>
            {linhas.map((b) => (
              <tr key={b.covariavel} className="border-b border-slate-100">
                <th scope="row" className="py-1 pr-2 font-normal">{b.covariavel}</th>
                <td className="py-1 pr-2">{num(b.dp_antes)}</td>
                <td className="py-1 pr-2">{num(b.dp_depois)}</td>
                <td className="py-1">{b.dp_depois !== null && Math.abs(b.dp_depois) < LIMITE_BALANCO ? t("fatores.parecidos") : t("fatores.aindaDiferem")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </details>
  );
}
