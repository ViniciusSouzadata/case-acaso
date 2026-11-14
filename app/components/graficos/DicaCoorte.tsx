import type { LinhaGrafico } from "@/lib/graficos";
import { amostraPequena, formatarInt, formatarPct, imatura } from "@/lib/regras";
import { t } from "@/lib/mensagens";

/** Texto da dica (hover) de um ponto: a dica também explica amostra pequena e coorte imatura (REQ-404/405). */
export function DicaCoorte({ linha, clicavel = false }: { linha: LinhaGrafico; clicavel?: boolean }) {
  const ainda = imatura(linha.madura);
  const pequena = amostraPequena(linha.amostraOk);
  return (
    <div className="max-w-[240px] rounded-lg border border-slate-200 bg-papel p-2 text-xs shadow-md">
      <div className="font-medium">{linha.rotulo}</div>
      <div>{t("numero.n", { n: formatarInt(linha.novos) })}</div>
      {ainda ? (
        <div>{t("imatura.rotulo")}. {t("imatura.explicacao")}</div>
      ) : pequena ? (
        <div>
          {t("numero.amostraPequena", { n: formatarInt(linha.novos) })}. {t("amostra.explicacao", { n: formatarInt(linha.novos) })}
        </div>
      ) : (
        <div>
          {formatarPct(linha.taxaFracao)} ({t("painel.margemErro", { inf: formatarPct(linha.icInf), sup: formatarPct(linha.icSup) })})
        </div>
      )}
      {clicavel ? <div className="mt-1 font-medium text-violeta-escuro">{t("painel.tela1.cliqueSemana")}</div> : null}
      {linha.inicioColeta ? <div className="mt-1 font-medium">{t("retencao.inicioColeta")}</div> : null}
    </div>
  );
}
