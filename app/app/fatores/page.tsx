"use client";

import { useState } from "react";
import { Achados } from "@/components/Achados";
import { DetalheBalanco } from "@/components/DetalheBalanco";
import { Estado } from "@/components/Estado";
import { Floresta } from "@/components/graficos/Floresta";
import { contarDistinguiveis, contarDoGrupo, fraseResposta, prepararFloresta, type EfeitoApi, type GrupoFator } from "@/lib/floresta";
import { t } from "@/lib/mensagens";
import { useApi } from "@/lib/useApi";

const GRUPOS: GrupoFator[] = ["assistente", "perfil", "engajamento", "descritivo"];

/** Tela 2 — O que faz voltar. */
export default function PaginaFatores() {
  const [grupo, setGrupo] = useState<GrupoFator>("assistente");
  const r = useApi<EfeitoApi[]>("/api/fatores/efeitos");
  const efeitos = r.estado === "ok" ? r.corpo.dados : [];
  const { k, m, f } = contarDistinguiveis(efeitos);
  const { linhas, limite } = prepararFloresta(efeitos, grupo);
  const doGrupo = contarDoGrupo(linhas);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-xl font-semibold text-slate-900">{t("fatores.pergunta")}</h1>
        <p className="mt-2 text-base text-slate-800" data-testid="frase-resposta">
          {r.estado === "ok" ? fraseResposta(k, m, f) : ""}
        </p>
      </header>

      <section className="rounded-xl border border-slate-200 bg-papel shadow-sm p-4">
        <div role="tablist" aria-label="Grupos de fatores" className="flex flex-wrap gap-1 border-b border-slate-200">
          {GRUPOS.map((g) => (
            <button key={g} role="tab" type="button" aria-selected={grupo === g} onClick={() => setGrupo(g)} className={`border-b-2 px-3 py-2 text-sm ${grupo === g ? "border-azul font-semibold text-azul" : "border-transparent text-slate-700"}`}>
              {t(`fatores.abas.${g}`)}
            </button>
          ))}
        </div>
        <p className="mt-2 text-sm text-slate-700">{t(`fatores.abasAjuda.${grupo}`)}</p>

        <details className="mt-2 text-sm">
          <summary className="cursor-pointer text-azul">{t("fatores.explicaTitulo")}</summary>
          <p className="mt-1 text-slate-800">{t("fatores.explica")}</p>
        </details>

        {r.estado === "carregando" ? <Estado tipo="carregando" /> : null}
        {r.estado === "erro" ? <Estado tipo="erro" mensagem={r.mensagem} requestId={r.requestId} /> : null}
        {r.estado === "ok" && linhas.length === 0 ? <Estado tipo="vazio" mensagem={t("fatores.tituloGrupoVazio")} /> : null}
        {linhas.length > 0 ? (
          <div role="tabpanel" className="mt-3">
            <h2 className="mb-1 text-base font-semibold text-slate-900">
              {grupo === "engajamento" ? t("fatores.tituloGrupoEng") : grupo === "descritivo" ? t("fatores.tituloGrupoDesc") : t("fatores.tituloGrupo", { k: doGrupo.k, m: doGrupo.m, tem: t(doGrupo.k === 1 ? "fatores.concordancia.tem1" : "fatores.concordancia.temN") })}
            </h2>
            <Floresta linhas={linhas} limite={limite} />
          </div>
        ) : null}
      </section>

      <Achados />
      <DetalheBalanco />
    </div>
  );
}
