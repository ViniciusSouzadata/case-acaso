import type { LinhaGrafico } from "@/lib/graficos";
import { formatarInt, formatarPct } from "@/lib/regras";
import { t } from "@/lib/mensagens";
import { amostraPequena, imatura } from "@/lib/regras";

/** Os mesmos dados do gráfico em tabela (acessível, REQ-411). Aplica a regra única de amostra e de coorte imatura. */
export function TabelaCoortes({ linhas, unidade }: { linhas: LinhaGrafico[]; unidade: string }) {
  return (
    <div className="overflow-x-auto">
    <table className="w-full text-left text-xs">
      <caption className="mb-1 text-left text-slate-600">{t("retencao.tabelaLegenda", { unidade })}</caption>
      <thead>
        <tr className="border-b border-slate-300 text-slate-700">
          <th scope="col" className="py-1 pr-2 font-medium">{t("retencao.colPeriodo")}</th>
          <th scope="col" className="py-1 pr-2 font-medium">{t("retencao.colNovos")}</th>
          <th scope="col" className="py-1 pr-2 font-medium">{t("retencao.colVoltaram")}</th>
          <th scope="col" className="py-1 pr-2 font-medium">{t("retencao.colTaxa")}</th>
          <th scope="col" className="py-1 font-medium">{t("retencao.colIc")}</th>
        </tr>
      </thead>
      <tbody>
        {linhas.map((l) => {
          const ainda = imatura(l.madura);
          const pequena = amostraPequena(l.amostraOk);
          return (
            <tr key={l.periodo} className="border-b border-slate-100" data-periodo={l.periodo}>
              <th scope="row" className="py-1 pr-2 font-normal">{l.rotulo}</th>
              <td className="py-1 pr-2">{formatarInt(l.novos)}</td>
              <td className="py-1 pr-2">{ainda ? "—" : formatarInt(l.voltaram)}</td>
              <td className="py-1 pr-2">
                {ainda
                  ? t("imatura.rotulo")
                  : pequena
                    ? t("numero.amostraPequena", { n: formatarInt(l.novos) })
                    : formatarPct(l.taxaFracao)}
                {l.inicioColeta ? <span className="block text-slate-700">{t("retencao.inicioColeta")}</span> : null}
              </td>
              <td className="py-1">
                {ainda || pequena ? "—" : `${formatarPct(l.icInf)} a ${formatarPct(l.icSup)}`}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
    </div>
  );
}
