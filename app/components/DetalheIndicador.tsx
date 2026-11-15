"use client";

import { Estado } from "@/components/Estado";
import { CampoTecnico, Destaque, Frases, Tecnico, frasesDe } from "@/components/painel/Blocos";
import { t } from "@/lib/mensagens";
import { useApi } from "@/lib/useApi";

interface Indicador {
  indicador: string;
  nome_exibicao: string;
  definicao: string;
  formula: string;
  denominador: string;
  periodo_referencia: string;
  fonte: string;
  limitacoes: string;
}

/**
 * Conteúdo do painel de um cartão: número em destaque, até 3 frases curtas e o resto (definição completa, fórmula, fonte) no bloco técnico.
 * As frases vêm de `detalhe.indicador.<id>` (arquivo de mensagens); o dicionário só alimenta o técnico.
 */
export function DetalheIndicador({ indicador, destaque }: { indicador: string; destaque?: { valor: string; rotulo: string } }) {
  const r = useApi<Indicador[]>(`/api/dicionario?indicador=${encodeURIComponent(indicador)}`);
  const item = r.estado === "ok" ? r.corpo.dados[0] : undefined;
  const frases = frasesDe(`detalhe.indicador.${indicador}`);
  return (
    <section className="cartao space-y-3 p-4" data-testid="detalhe-indicador">
      {destaque ? <Destaque valor={destaque.valor} rotulo={destaque.rotulo} /> : null}
      {frases.length > 0 ? <Frases itens={frases} /> : item ? <Frases itens={[item.definicao]} /> : null}
      {r.estado === "carregando" ? <Estado tipo="carregando" /> : null}
      {r.estado === "erro" ? <Estado tipo="erro" mensagem={r.mensagem} requestId={r.requestId} /> : null}
      {r.estado === "ok" && !item ? <Estado tipo="vazio" mensagem={t("glossario.naoEncontrado")} /> : null}
      {item ? (
        <Tecnico>
          <CampoTecnico rotulo={t("glossario.definicao")}>{item.definicao}</CampoTecnico>
          <CampoTecnico rotulo={t("glossario.denominador")}>{item.denominador}</CampoTecnico>
          <CampoTecnico rotulo={t("glossario.periodo")}>{item.periodo_referencia}</CampoTecnico>
          <CampoTecnico rotulo={t("glossario.limitacoes")}>{item.limitacoes}</CampoTecnico>
          <CampoTecnico rotulo={t("glossario.formula")}>{item.formula}</CampoTecnico>
          <CampoTecnico rotulo={t("glossario.fonte")}>{item.fonte}</CampoTecnico>
        </Tecnico>
      ) : null}
    </section>
  );
}
