"use client";

import { Estado } from "@/components/Estado";
import { PontosSensibilidade } from "@/components/graficos/PontosSensibilidade";
import { resumoSensibilidade, type SensibilidadeApi } from "@/lib/graficos";
import { t } from "@/lib/mensagens";
import { formatarPct } from "@/lib/regras";
import { useApi } from "@/lib/useApi";

const quando = (def: string) => {
  const chave = `sens.maior.${def}`;
  const f = t(chave);
  return f === chave ? "em uma das formas de contar" : f;
};

/** "E se mudarmos a forma de contar?": uma frase no topo e as 10 formas em pontos, cada uma explicada ao clicar na linha. */
export function BlocoSensibilidade() {
  const r = useApi<SensibilidadeApi[]>("/api/retencao/sensibilidade");
  const linhas = r.estado === "ok" ? r.corpo.dados : [];
  const v = resumoSensibilidade(linhas);
  // a forma que mais se afasta da oficial (em módulo) é a que a frase cita
  const maior = linhas.filter((l) => l.definicao !== "oficial").sort((a, b) => Math.abs(b.delta_vs_oficial ?? 0) - Math.abs(a.delta_vs_oficial ?? 0))[0];

  return (
    <section className="cartao space-y-3 p-4" aria-label={t("painel.tela1.detalheDefinicoes")}>
      {r.estado === "carregando" ? <Estado tipo="carregando" /> : null}
      {r.estado === "erro" ? <Estado tipo="erro" mensagem={r.mensagem} requestId={r.requestId} /> : null}
      {r.estado === "ok" && linhas.length === 0 ? <Estado tipo="vazio" /> : null}
      {v ? (
        <>
          <p className="text-sm text-slate-800">
            {t("sens.frase", { min: formatarPct(v.min, 0), max: formatarPct(v.max, 0), quando: maior ? quando(maior.definicao) : "em uma das formas de contar" })}
          </p>
          <PontosSensibilidade linhas={linhas} />
        </>
      ) : null}
    </section>
  );
}
