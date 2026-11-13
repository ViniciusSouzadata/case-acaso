"use client";

import { useState } from "react";
import { Estado } from "@/components/Estado";
import { PainelLateral } from "@/components/PainelLateral";
import { frases } from "@/lib/achados";
import type { EfeitoApi } from "@/lib/floresta";
import type { ResumoSemanaApi } from "@/lib/graficos";
import { t } from "@/lib/mensagens";
import { numeroGrande } from "@/lib/painel";
import { useApi } from "@/lib/useApi";

interface Achado {
  ordem: number;
  titulo: string;
  evidencia: string;
  decisao: string;
  limite: string;
}

const SEMANA_ACHADO = "2023-11-20";

/** Número grande de cada achado, tirado dos mesmos dados da tela (o texto do achado não é reescrito). */
function numeroDoAchado(ordem: number, efeitos: EfeitoApi[], semana: ResumoSemanaApi | null): { valor: string; legenda: string } {
  const efeito = (fator: string, nivel: string) => efeitos.find((e) => e.fator === fator && e.nivel === nivel && e.metodo === "logit_ame")?.efeito_ajustado_pp ?? null;
  if (ordem === 1) return { valor: numeroGrande(efeito("recusa", "sim")), legenda: t("painel.tela2.cap1") };
  if (ordem === 2) return { valor: numeroGrande(efeito("modelo_familia", "gpt-4")), legenda: t("painel.tela2.cap2") };
  return { valor: numeroGrande(semana?.delta_pp ?? null), legenda: t("painel.tela2.cap3") };
}

/** Três cartões curtos: número grande, uma frase e "o que fazer" em uma linha. O resto fica em "Ver detalhes". */
export function CartoesAchados({ efeitos }: { efeitos: EfeitoApi[] }) {
  const r = useApi<Achado[]>("/api/achados");
  const sem = useApi<{ resumo: ResumoSemanaApi | null }>(`/api/semana/decomposicao?semana=${SEMANA_ACHADO}`);
  const [aberto, setAberto] = useState<Achado | null>(null);
  const achados = r.estado === "ok" ? r.corpo.dados : [];
  const semana = sem.estado === "ok" ? sem.corpo.dados.resumo : null;

  return (
    <section aria-labelledby="achados-titulo">
      <h2 id="achados-titulo" className="sr-only">{t("painel.tela2.achadosTitulo")}</h2>
      {r.estado === "carregando" ? <Estado tipo="carregando" /> : null}
      {r.estado === "erro" ? <Estado tipo="erro" mensagem={r.mensagem} requestId={r.requestId} /> : null}
      {r.estado === "ok" && achados.length === 0 ? <Estado tipo="vazio" mensagem={t("fatores.achadosVazio")} /> : null}
      <div className="grid gap-3 md:grid-cols-3">
        {achados.map((a) => {
          const n = numeroDoAchado(a.ordem, efeitos, semana);
          const fazer = frases(a.decisao)[0] ?? a.decisao;
          return (
            <article key={a.ordem} className="cartao flex flex-col p-4">
              <div className="flex items-baseline gap-2">
                <span className="font-display text-3xl font-semibold leading-none text-tinta">{n.valor}</span>
                <span className="text-xs text-slate-600">{n.legenda}</span>
              </div>
              <h3 className="mt-2 line-clamp-2 text-sm font-semibold text-tinta">{a.titulo}</h3>
              <p className="mt-1 line-clamp-2 text-xs text-slate-700">
                <span className="font-medium text-violeta-escuro">{t("painel.tela2.oQueFazer")}:</span> {fazer}
              </p>
              <button type="button" onClick={() => setAberto(a)} className="mt-auto self-start pt-2 text-sm font-medium text-violeta hover:underline">
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
