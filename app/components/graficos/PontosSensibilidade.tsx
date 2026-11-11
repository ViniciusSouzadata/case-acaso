import { pontosSensibilidade, type SensibilidadeApi } from "@/lib/graficos";
import { t } from "@/lib/mensagens";
import { formatarInt, formatarPP, formatarPct } from "@/lib/regras";

/** Pontos com barra de intervalo, uma linha por definição; linha tracejada = definição oficial. */
export function PontosSensibilidade({ linhas }: { linhas: SensibilidadeApi[] }) {
  const { pontos } = pontosSensibilidade(linhas);
  return (
    <div>
      <ul className="space-y-3">
        {pontos.map((p) => {
          const nome = t(`sens.nomes.${p.definicao}`);
          const rotulo = nome === `sens.nomes.${p.definicao}` ? p.definicao : nome;
          return (
            <li key={p.definicao} className="grid gap-1 sm:grid-cols-[14rem_1fr] sm:items-center sm:gap-3" data-definicao={p.definicao}>
              <div>
                <div className="text-sm font-medium text-slate-900">{rotulo}</div>
                <div className="text-xs text-slate-600">{p.descricao}</div>
              </div>
              <div>
                <div className="relative h-6" role="img" aria-label={`${rotulo}: ${formatarPct(p.taxa)}, de ${formatarPct(p.ic_inf)} a ${formatarPct(p.ic_sup)}`}>
                  <div className="absolute top-1/2 h-px w-full bg-slate-200" />
                  <div className="absolute top-0 h-6 border-l border-dashed border-slate-500" style={{ left: `${p.posOficial}%` }} />
                  <div className="absolute top-1/2 h-1.5 -translate-y-1/2 rounded bg-azul/40" style={{ left: `${p.posInf}%`, width: `${Math.max(0.5, p.posSup - p.posInf)}%` }} />
                  <div className="absolute top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-azul" style={{ left: `${p.posTaxa}%` }} />
                </div>
                <div className="text-xs text-slate-700">
                  <strong>{formatarPct(p.taxa)}</strong> ({t("numero.ic", { inf: formatarPct(p.ic_inf), sup: formatarPct(p.ic_sup) })}) · {t("sens.pessoas", { n: formatarInt(p.usuarios) })} ·{" "}
                  {p.oficial ? t("sens.igualOficial") : t("sens.vsOficial", { delta: formatarPP(p.delta_vs_oficial) })}
                </div>
              </div>
            </li>
          );
        })}
      </ul>
      <p className="mt-3 text-xs text-slate-600">{t("sens.legenda")}</p>
    </div>
  );
}
