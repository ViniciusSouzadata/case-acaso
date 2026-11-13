"use client";

import { CartoesAchados } from "@/components/CartoesAchados";
import { Estado } from "@/components/Estado";
import { Ranking } from "@/components/Ranking";
import { grupoEfetivo, type EfeitoApi } from "@/lib/floresta";
import { t } from "@/lib/mensagens";
import { conclusaoFatores, nomeCurto } from "@/lib/painel";
import { useApi } from "@/lib/useApi";

/** Tela 2 — O que faz voltar, em formato de painel: um ranking e três cartões. Método e detalhes ficam atrás de cliques. */
export default function PaginaFatores() {
  const r = useApi<EfeitoApi[]>("/api/fatores/efeitos");
  const efeitos = r.estado === "ok" ? r.corpo.dados : [];
  // Só o ajuste pelo perfil conta (o segundo método repete fatores); engajamento e tema são descrição.
  const validos = efeitos.filter((e) => e.metodo === "logit_ame" && grupoEfetivo(e) !== "engajamento" && grupoEfetivo(e) !== "descritivo" && e.amostra_suficiente && e.efeito_ajustado_pp !== null);
  const sustentam = validos.filter((e) => e.significativo_fdr === true).map((e) => nomeCurto(e.fator, e.nivel));

  return (
    <div className="space-y-3">
      <header>
        <h1 className="titulo-painel">{t("painel.tela2.titulo")}</h1>
        <p className="mt-1 max-w-3xl text-base text-slate-700" data-testid="frase-resposta">
          {r.estado === "ok" ? conclusaoFatores(sustentam, validos.length) : ""}
        </p>
      </header>

      {r.estado === "carregando" ? <Estado tipo="carregando" /> : null}
      {r.estado === "erro" ? <Estado tipo="erro" mensagem={r.mensagem} requestId={r.requestId} /> : null}
      {r.estado === "ok" && efeitos.length === 0 ? <Estado tipo="vazio" mensagem={t("fatores.tituloGrupoVazio")} /> : null}
      {efeitos.length > 0 ? <Ranking efeitos={efeitos} /> : null}
      {r.estado === "ok" ? <CartoesAchados /> : null}
    </div>
  );
}
