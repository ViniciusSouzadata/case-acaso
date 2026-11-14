"use client";

import { useState } from "react";
import { Estado } from "@/components/Estado";
import { PainelLateral } from "@/components/PainelLateral";
import { frases } from "@/lib/achados";
import { ALVO_ACHADO } from "@/lib/painel";
import { t } from "@/lib/mensagens";
import { useApi } from "@/lib/useApi";

interface Achado {
  ordem: number;
  titulo: string;
  evidencia: string;
  decisao: string;
  limite: string;
  numero_destaque: string | null;
  rotulo_destaque: string | null;
  acao_curta: string | null;
}

/** Três cartões curtos: número grande, uma frase e "o que fazer" em uma linha. O resto fica em "Ver detalhes". */
export function CartoesAchados({ onRealcar }: { onRealcar?: (alvo: { fator: string; nivel: string } | null) => void }) {
  const r = useApi<Achado[]>("/api/achados");
  const [aberto, setAberto] = useState<Achado | null>(null);
  const achados = r.estado === "ok" ? r.corpo.dados : [];

  return (
    <section aria-labelledby="achados-titulo">
      <h2 id="achados-titulo" className="sr-only">{t("painel.tela2.achadosTitulo")}</h2>
      {r.estado === "carregando" ? <Estado tipo="carregando" /> : null}
      {r.estado === "erro" ? <Estado tipo="erro" mensagem={r.mensagem} requestId={r.requestId} /> : null}
      {r.estado === "ok" && achados.length === 0 ? <Estado tipo="vazio" mensagem={t("fatores.achadosVazio")} /> : null}
      <div className="grid gap-3 md:grid-cols-3">
        {achados.map((a) => {
          // número, rótulo e ação curta vêm de resultado.achado (migração 012); sem eles o cartão cai na 1ª frase da decisão
          const fazer = a.acao_curta ?? frases(a.decisao)[0] ?? a.decisao;
          return (
            <article
              key={a.ordem}
              data-achado={a.ordem}
              className="cartao entra flex flex-col p-3"
              style={{ animationDelay: `${(a.ordem - 1) * 60}ms` }}
              onMouseEnter={() => onRealcar?.(ALVO_ACHADO[a.ordem] ?? null)}
              onMouseLeave={() => onRealcar?.(null)}
              onFocus={() => onRealcar?.(ALVO_ACHADO[a.ordem] ?? null)}
              onBlur={() => onRealcar?.(null)}
            >
              {a.numero_destaque ? (
                <div className="flex items-baseline gap-2">
                  <span className="shrink-0 whitespace-nowrap font-display text-3xl font-semibold leading-none text-tinta">{a.numero_destaque}</span>
                  {a.rotulo_destaque ? <span className="text-xs text-slate-600">{a.rotulo_destaque}</span> : null}
                </div>
              ) : null}
              <h3 className="mt-1.5 text-[13px] font-semibold leading-snug text-tinta">{a.titulo}</h3>
              <p className="mt-1 text-xs text-slate-700">
                <span className="font-medium text-violeta-escuro">{t("painel.tela2.oQueFazer")}:</span> {fazer}
              </p>
              <button type="button" onClick={() => setAberto(a)} className="alvo mt-auto self-start pt-1.5 text-sm font-medium text-violeta hover:underline">
                {t("painel.verDetalhes")}
              </button>
            </article>
          );
        })}
      </div>
      {aberto ? (
        <PainelLateral titulo={aberto.titulo} onFechar={() => setAberto(null)}>
          <div className="cartao space-y-3 p-4 text-sm text-slate-800">
            <p><span className="font-medium">{t("fatores.achadoEvidencia")}:</span> {aberto.evidencia}</p>
            <p><span className="font-medium">{t("fatores.achadoDecisao")}:</span> {aberto.decisao}</p>
            <p className="text-slate-700"><span className="font-medium">{t("fatores.achadoLimite")}:</span> {aberto.limite}</p>
          </div>
        </PainelLateral>
      ) : null}
    </section>
  );
}
