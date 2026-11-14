"use client";

import { useState } from "react";
import { pontosSensibilidade, type SensibilidadeApi } from "@/lib/graficos";
import { t } from "@/lib/mensagens";
import { formatarPct } from "@/lib/regras";

/** Pontos com barra de margem de erro, uma linha por forma de contar; linha tracejada = forma oficial. Clicar na linha mostra o que muda. */
export function PontosSensibilidade({ linhas }: { linhas: SensibilidadeApi[] }) {
  const { pontos } = pontosSensibilidade(linhas);
  const [aberta, setAberta] = useState<string | null>(null);
  return (
    <div>
      <ul className="divide-y divide-[#efedf8]" title={t("sens.clique")}>
        {pontos.map((p) => {
          const nome = t(`sens.nomes.${p.definicao}`);
          const rotulo = nome === `sens.nomes.${p.definicao}` ? p.definicao : nome;
          const leigo = t(`sens.leigo.${p.definicao}`);
          const aberto = aberta === p.definicao;
          return (
            <li key={p.definicao} data-definicao={p.definicao}>
              <button
                type="button"
                aria-expanded={aberto}
                onClick={() => setAberta(aberto ? null : p.definicao)}
                className="grid min-h-10 w-full grid-cols-[minmax(0,1fr)_3.5rem] items-center gap-x-3 gap-y-1 rounded-lg px-2 py-1.5 text-left hover:bg-[#ece8fc] focus-visible:outline focus-visible:outline-2 focus-visible:outline-violeta sm:grid-cols-[14rem_minmax(0,1fr)_3.5rem]"
              >
                <span className="text-sm font-medium text-tinta">{rotulo}</span>
                <span className="relative order-last col-span-2 block h-5 sm:order-none sm:col-span-1" role="img" aria-label={`${rotulo}: ${formatarPct(p.taxa)}, ${t("numero.ic", { inf: formatarPct(p.ic_inf), sup: formatarPct(p.ic_sup) })}`}>
                  <span className="absolute top-1/2 block h-px w-full bg-slate-200" />
                  <span className="absolute top-0 block h-5 border-l border-dashed border-slate-500" style={{ left: `${p.posOficial}%` }} />
                  <span className="absolute top-1/2 block h-1.5 -translate-y-1/2 rounded bg-violeta/40" style={{ left: `${p.posInf}%`, width: `${Math.max(0.5, p.posSup - p.posInf)}%` }} />
                  <span className="absolute top-1/2 block h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-violeta" style={{ left: `${p.posTaxa}%` }} />
                </span>
                <span className="text-right font-display text-sm font-semibold text-slate-800">{formatarPct(p.taxa)}</span>
              </button>
              {aberto && leigo !== `sens.leigo.${p.definicao}` ? <p className="px-2 pb-2 text-sm text-slate-700">{leigo}</p> : null}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
