"use client";

import { CampoTecnico, Frases, Tecnico } from "@/components/painel/Blocos";
import type { Estimativa, LinhaFloresta } from "@/lib/floresta";
import { t } from "@/lib/mensagens";
import { fraseResultado, fraseVeredito, rotulosGrupos } from "@/lib/painel";
import { formatarInt, formatarPP } from "@/lib/regras";

const faixaTecnica = (e: Estimativa) => `${formatarPP(e.efeito)} (${t("numero.ic", { inf: formatarPP(e.inf), sup: formatarPP(e.sup) })})`;
const aCemInt = (x: number) => String(Math.round(x * 100));

/** Duas barras: quantos de cada 100 voltaram em cada grupo, com o tamanho dos grupos embaixo. Monta dos números da rota, não de texto pronto. */
function DuasBarras({ l }: { l: LinhaFloresta }) {
  if (l.taxaNivel === null || l.taxaReferencia === null) return null;
  const [a, b] = rotulosGrupos(l);
  const maximo = Math.max(l.taxaNivel, l.taxaReferencia, 0.0001);
  const linhas = [
    { nome: a, taxa: l.taxaNivel, n: l.nNivel, cor: "bg-laranja" },
    { nome: b, taxa: l.taxaReferencia, n: l.nReferencia, cor: "bg-violeta" },
  ];
  return (
    <div className="space-y-2" data-testid="duas-barras">
      {linhas.map((x) => (
        <div key={x.nome}>
          <div className="text-sm font-medium text-tinta">{t("detalhe.barra", { grupo: x.nome, n: aCemInt(x.taxa) })}</div>
          <div className="mt-1 h-3 rounded bg-[#f1effc]" aria-hidden>
            <div className={`h-3 rounded ${x.cor}`} style={{ width: `${Math.max(2, (x.taxa / maximo) * 100)}%` }} />
          </div>
          <div className="mt-0.5 text-xs text-slate-600">{t("detalhe.pessoasGrupo", { n: formatarInt(x.n) })}</div>
        </div>
      ))}
    </div>
  );
}

/** Painel de uma linha do ranking: duas barras, a frase do resultado, o veredito e, recolhido, o técnico. */
export function DetalheFator({ l }: { l: LinhaFloresta }) {
  const resultado = fraseResultado(l);
  return (
    <section className="cartao space-y-3 p-4" data-testid="detalhe-fator">
      {l.pequena ? null : <DuasBarras l={l} />}
      <Frases itens={[...(resultado ? [resultado] : []), fraseVeredito(l)]} />
      <Tecnico>
        {l.bruto ? <CampoTecnico rotulo={t("fatores.bruto")}>{faixaTecnica(l.bruto)}</CampoTecnico> : null}
        {l.ajustado ? <CampoTecnico rotulo={t("fatores.ajustado")}>{faixaTecnica(l.ajustado)}</CampoTecnico> : null}
        {l.entreParecidas ? <CampoTecnico rotulo={t("detalhe.tecnicoParecidas")}>{faixaTecnica(l.entreParecidas)} {t("detalhe.parecidasAviso")}</CampoTecnico> : null}
        {l.segundo ? (
          <CampoTecnico rotulo={t("detalhe.tecnicoOutraForma")}>
            {l.segundo.ajustado
              ? t("fatores.segundoMetodoCom", { n: formatarInt(l.segundo.nNivel), nRef: formatarInt(l.segundo.nReferencia), faixa: faixaTecnica(l.segundo.ajustado) })
              : t("fatores.segundoMetodoSem")}
          </CampoTecnico>
        ) : null}
        <CampoTecnico rotulo={t("detalhe.tecnicoTamanhos")}>{t("fatores.n", { n: formatarInt(l.nNivel), nRef: formatarInt(l.nReferencia) })}</CampoTecnico>
      </Tecnico>
    </section>
  );
}
