"use client";

import { useState } from "react";
import { BlocoBlur, BlurTexto } from "@/components/movimento/BlurTexto";
import { CartoesAchados } from "@/components/CartoesAchados";
import { DestacaNumeros } from "@/components/DestacaNumeros";
import { Estado } from "@/components/Estado";
import { Ranking } from "@/components/Ranking";
import { grupoEfetivo, type EfeitoApi } from "@/lib/floresta";
import { t } from "@/lib/mensagens";
import { conclusaoFatores, fraseFator } from "@/lib/painel";
import { useApi } from "@/lib/useApi";

/** Tela 2 — O que faz voltar, em formato de painel: um ranking e três cartões. Método e detalhes ficam atrás de cliques. */
export default function PaginaFatores() {
  const [realce, setRealce] = useState<{ fator: string; nivel: string } | null>(null);
  const r = useApi<EfeitoApi[]>("/api/fatores/efeitos");
  const resumo = useApi<{ usuarios: number } | null>("/api/retencao/resumo");
  const base = resumo.estado === "ok" && resumo.corpo.dados ? resumo.corpo.dados.usuarios : null;
  const efeitos = r.estado === "ok" ? r.corpo.dados : [];
  // Só o ajuste pelo perfil conta (o segundo método repete fatores); engajamento e tema são descrição.
  const validos = efeitos.filter((e) => e.metodo === "logit_ame" && grupoEfetivo(e) !== "engajamento" && grupoEfetivo(e) !== "descritivo" && e.amostra_suficiente && e.efeito_ajustado_pp !== null);
  const sustentam = validos.filter((e) => e.significativo_fdr === true).map((e) => fraseFator(e.fator, e.nivel));

  return (
    <div className="space-y-3">
      <header>
        <BlurTexto className="titulo-painel" texto={t("painel.tela2.titulo")} />
        <BlocoBlur className="mt-1 max-w-3xl text-base text-slate-700" data-testid="frase-resposta">
          {r.estado === "ok" ? <DestacaNumeros texto={conclusaoFatores(sustentam, validos.length)} /> : ""}
        </BlocoBlur>
      </header>

      {r.estado === "carregando" ? <Estado tipo="carregando" /> : null}
      {r.estado === "erro" ? <Estado tipo="erro" mensagem={r.mensagem} requestId={r.requestId} /> : null}
      {r.estado === "ok" && efeitos.length === 0 ? <Estado tipo="vazio" mensagem={t("fatores.tituloGrupoVazio")} /> : null}
      {efeitos.length > 0 ? <Ranking efeitos={efeitos} realce={realce} base={base} /> : null}
      {r.estado === "ok" ? <CartoesAchados onRealcar={setRealce} /> : null}
    </div>
  );
}
