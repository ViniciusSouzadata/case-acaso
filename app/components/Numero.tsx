"use client";

import { useState } from "react";
import { useContagem } from "@/lib/movimento";
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
  /** contagem animada do número de destaque (só Tela 1) */
  contar?: boolean;
}

/** REQ-402..406: valor com intervalo e n; o "i" abre o glossário; amostra pequena e coorte imatura seguem a regra única. */
export function Numero({ rotulo, valor, formato, icInf, icSup, n, amostraSuficiente = true, madura = true, indicador, contar = false }: PropsNumero) {
  const [aberto, setAberto] = useState(false);
  const pequena = amostraPequena(amostraSuficiente);
  const ainda = imatura(madura);
  const mostrarValor = !pequena && !ainda && valor !== null;
  const animado = useContagem(valor, contar);

  return (
    <div className={`${contar ? "cartao-escuro" : "cartao"} p-4`}>
      <div className={`flex items-center gap-2 text-sm ${contar ? "text-white/80" : "text-slate-600"}`}>
        <span>{rotulo}</span>
        {indicador ? (
          <button
            type="button"
            aria-label={`${t("numero.info")} (${rotulo})`}
            onClick={() => setAberto(true)}
            className={`flex h-5 w-5 items-center justify-center rounded-full border ${contar ? "border-violeta-claro text-violeta-claro hover:bg-violeta-claro hover:text-tinta" : "border-azul text-azul hover:bg-azul hover:text-white"} text-xs font-semibold`}
          >
            i
          </button>
        ) : null}
      </div>

      <div className={`mt-1 font-display text-4xl font-semibold tracking-tight ${contar ? "text-papel" : "text-slate-900"}`} data-testid="valor">
        {ainda ? t("imatura.rotulo") : pequena ? t("numero.amostraPequena", { n: formatarInt(n) }) : mostrarValor ? formatar(contar && animado !== null ? animado : valor, formato) : t("numero.semValor")}
      </div>

      {mostrarValor && icInf != null && icSup != null ? (
        <div className={`mt-1 text-xs ${contar ? "text-white/80" : "text-slate-600"}`}>
          {t("numero.ic", { inf: formatar(icInf, formato), sup: formatar(icSup, formato) })}
          {formato === "pp" && cruzaZero(icInf, icSup) ? (
            <span className={`ml-2 font-medium ${contar ? "text-papel" : "text-slate-800"}`}>· {t("zero.rotulo")}</span>
          ) : null}
        </div>
      ) : null}
      {n !== null && !pequena ? <div className={`text-xs ${contar ? "text-white/80" : "text-slate-600"}`}>{t("numero.n", { n: formatarInt(n) })}</div> : null}

      {pequena ? <AvisoAmostra n={n} /> : null}
      {ainda ? <p className="mt-1 text-xs text-slate-700">{t("imatura.explicacao")}</p> : null}

      {aberto && indicador ? <Glossario indicador={indicador} onFechar={() => setAberto(false)} /> : null}
    </div>
  );
}
