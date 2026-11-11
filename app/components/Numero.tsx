"use client";

import { useState } from "react";
import { amostraPequena, cruzaZero, formatar, formatarInt, imatura, type FormatoNumero } from "@/lib/regras";
import { t } from "@/lib/mensagens";
import { AvisoAmostra } from "./AvisoAmostra";
import { Glossario } from "./Glossario";

export interface PropsNumero {
  rotulo: string;
  valor: number | null;
  formato: FormatoNumero;
  icInf?: number | null;
  icSup?: number | null;
  n: number | null;
  amostraSuficiente?: boolean;
  /** coorte ainda dentro dos 7 dias (REQ-405) */
  madura?: boolean;
  /** chave do indicador em /api/dicionario; sem ela não há ícone "i" */
  indicador?: string;
}

/** REQ-402..406: valor com intervalo e n; o "i" abre o glossário; amostra pequena e coorte imatura seguem a regra única. */
export function Numero({ rotulo, valor, formato, icInf, icSup, n, amostraSuficiente = true, madura = true, indicador }: PropsNumero) {
  const [aberto, setAberto] = useState(false);
  const pequena = amostraPequena(amostraSuficiente);
  const ainda = imatura(madura);
  const mostrarValor = !pequena && !ainda && valor !== null;

  return (
    <div className="rounded border border-slate-200 bg-white p-4">
      <div className="flex items-center gap-2 text-sm text-slate-600">
        <span>{rotulo}</span>
        {indicador ? (
          <button
            type="button"
            aria-label={`${t("numero.info")} (${rotulo})`}
            onClick={() => setAberto(true)}
            className="flex h-5 w-5 items-center justify-center rounded-full border border-azul text-xs font-semibold text-azul"
          >
            i
          </button>
        ) : null}
      </div>

      <div className="mt-1 text-3xl font-semibold text-slate-900" data-testid="valor">
        {ainda ? t("imatura.rotulo") : pequena ? t("numero.amostraPequena", { n: formatarInt(n) }) : mostrarValor ? formatar(valor, formato) : t("numero.semValor")}
      </div>

      {mostrarValor && icInf != null && icSup != null ? (
        <div className="mt-1 text-xs text-slate-600">
          {t("numero.ic", { inf: formatar(icInf, formato), sup: formatar(icSup, formato) })}
          {formato === "pp" && cruzaZero(icInf, icSup) ? (
            <span className="ml-2 font-medium text-slate-800">· {t("zero.rotulo")}</span>
          ) : null}
        </div>
      ) : null}
      {n !== null && !pequena ? <div className="text-xs text-slate-600">{t("numero.n", { n: formatarInt(n) })}</div> : null}

      {pequena ? <AvisoAmostra n={n} /> : null}
      {ainda ? <p className="mt-1 text-xs text-slate-700">{t("imatura.explicacao")}</p> : null}

      {aberto && indicador ? <Glossario indicador={indicador} onFechar={() => setAberto(false)} /> : null}
    </div>
  );
}
