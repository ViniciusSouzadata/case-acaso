import type { Estimativa, LinhaFloresta } from "@/lib/floresta";
import { t } from "@/lib/mensagens";
import { formatarInt, formatarPP } from "@/lib/regras";

const nomeFator = (f: string) => {
  const chave = `fatores.rotulos.${f}`;
  const r = t(chave);
  return r === chave ? f : r;
};

const faixa = (e: Estimativa) => `${formatarPP(e.efeito)} (${t("numero.ic", { inf: formatarPP(e.inf), sup: formatarPP(e.sup) })})`;

/** Uma linha do gráfico de floresta: ponto + barra de intervalo, linha do zero, frase de leitura e rótulos. */
export function LinhaDaFloresta({ l }: { l: LinhaFloresta }) {
  const cor = l.pequena ? "#8a8f98" : "#0072b2";
  return (
    <li className="py-3" data-fator={l.fator} data-nivel={l.nivel}>
      <div className="grid gap-1 sm:grid-cols-[15rem_1fr] sm:gap-3">
        <div>
          <div className="text-sm font-medium text-slate-900">
            {nomeFator(l.fator)}: {t("fatores.contra", { nivel: l.nivel, ref: l.referencia })}
          </div>
          <div className="text-xs text-slate-600">
            {t("fatores.n", { n: formatarInt(l.nNivel), nRef: formatarInt(l.nReferencia) })}
            {l.grupo !== "engajamento" ? ` · ${t(l.metodo === "ipw" ? "fatores.metodoIpw" : "fatores.metodoLogit")}` : null}
          </div>
        </div>

        <div>
          <div className="relative h-8" role="img" aria-label={l.leitura ?? nomeFator(l.fator)}>
            <div className="absolute top-0 h-8 w-px bg-slate-500" style={{ left: `${l.pos.zero}%` }} />
            {l.bruto && l.pos.bruto ? (
              <>
                <div className="absolute top-2 h-0.5 -translate-y-1/2 rounded" style={{ left: `${l.pos.bruto[0]}%`, width: `${Math.max(0.5, l.pos.bruto[2] - l.pos.bruto[0])}%`, background: cor, opacity: 0.5 }} />
                <div data-ponto="bruto" className="absolute top-2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 bg-white" style={{ left: `${l.pos.bruto[1]}%`, borderColor: cor }} />
              </>
            ) : null}
            {l.ajustado && l.pos.ajustado ? (
              <>
                <div className="absolute top-6 h-1 -translate-y-1/2 rounded" style={{ left: `${l.pos.ajustado[0]}%`, width: `${Math.max(0.5, l.pos.ajustado[2] - l.pos.ajustado[0])}%`, background: cor, opacity: 0.6 }} />
                <div data-ponto="ajustado" className="absolute top-6 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white" style={{ left: `${l.pos.ajustado[1]}%`, background: l.pequena ? "#fff" : cor, outline: l.pequena ? `2px solid ${cor}` : undefined }} />
              </>
            ) : null}
          </div>

          {l.leitura ? <p className="mt-1 text-xs text-slate-800">{l.leitura}</p> : null}

          {l.pequena ? (
            <p role="note" className="mt-1 text-xs font-medium text-slate-800">
              {t("numero.amostraPequena", { n: formatarInt(l.nNivel) })}. {t("amostra.explicacao", { n: formatarInt(l.nNivel) })}
            </p>
          ) : (
            <p className="mt-1 text-xs text-slate-700">
              {l.bruto ? <span>{t("fatores.bruto")}: {faixa(l.bruto)}</span> : null}
              {l.ajustado ? <span> · {t("fatores.ajustado")}: {faixa(l.ajustado)}</span> : l.grupo === "engajamento" ? <span> · {t("fatores.semAjuste")}</span> : null}
            </p>
          )}

          <div className="mt-1 flex flex-wrap gap-2 text-xs">
            {l.naoDistingue ? <span className="rounded bg-slate-100 px-2 py-0.5 font-medium text-slate-900">{t("zero.rotulo")}</span> : null}
            {l.podeSerAcaso ? <span className="rounded bg-amber-50 px-2 py-0.5 text-slate-800">{t("fatores.naoResiste")}</span> : null}
            {l.resisteFdr && !l.naoDistingue ? <span className="rounded bg-emerald-50 px-2 py-0.5 text-slate-800">✓ {t("fatores.resiste")}</span> : null}
          </div>
        </div>
      </div>
    </li>
  );
}

export function Floresta({ linhas, limite }: { linhas: LinhaFloresta[]; limite: number }) {
  return (
    <div>
      <ul className="divide-y divide-slate-100">
        {linhas.map((l) => (
          <LinhaDaFloresta key={l.chave} l={l} />
        ))}
      </ul>
      <p className="mt-2 text-xs text-slate-600">
        {t("fatores.eixo")} (de {formatarPP(-limite, 0)} a {formatarPP(limite, 0)}). {t("fatores.legenda")}
      </p>
    </div>
  );
}
