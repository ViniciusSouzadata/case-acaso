"use client";

import {
  Area,
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { faixasEras, faixasImaturas, type EraApi, type Granularidade, type LinhaGrafico } from "@/lib/graficos";
import { t } from "@/lib/mensagens";
import { useMovimentoReduzido } from "@/lib/movimento";
import { DicaCoorte } from "./DicaCoorte";

const AZUL = "#6a48eb"; // violeta de marca: série principal
const LARANJA = "#ff6c0e"; // laranja: destaque pontual (média móvel)
const CINZA = "#8a8f98";
const MARGEM = { top: 10, right: 16, bottom: 4, left: 8 };
const LARGURA_Y = 52;

interface PontoProps {
  cx?: number;
  cy?: number;
  payload?: LinhaGrafico;
}

/** Ponto cheio violeta; cinza vazado quando a amostra é pequena (REQ-404). */
function Ponto({ cx, cy, payload }: PontoProps) {
  if (cx === undefined || cy === undefined || !payload || payload.taxa === null) return <g />;
  return payload.amostraOk && !payload.inicioColeta ? (
    <circle cx={cx} cy={cy} r={3.5} fill={AZUL} stroke="#fff" strokeWidth={1} />
  ) : (
    <circle cx={cx} cy={cy} r={4} fill="#fff" stroke={CINZA} strokeWidth={1.5} />
  );
}

/** Ponto sob o mouse: anel maior, para destacar o período cujo intervalo e n aparecem na dica. */
function PontoAtivo({ cx, cy, payload }: PontoProps) {
  if (cx === undefined || cy === undefined || !payload || payload.taxa === null) return <g />;
  return <circle cx={cx} cy={cy} r={6.5} fill="#fff" stroke={payload.amostraOk && !payload.inicioColeta ? AZUL : CINZA} strokeWidth={3} />;
}

export function GraficoRetencao({
  linhas,
  eras,
  granularidade,
}: {
  linhas: LinhaGrafico[];
  eras: EraApi[];
  granularidade: Granularidade;
}) {
  const faixas = faixasEras(linhas, eras);
  const imaturas = faixasImaturas(linhas);
  const reduzido = useMovimentoReduzido();
  const anima = !reduzido;
  const eixoX = t(granularidade === "mes" ? "retencao.eixoXMes" : "retencao.eixoXSemana");

  return (
    <div>
      <div role="img" aria-label={t("retencao.eixoY")} className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={linhas} margin={MARGEM}>
            <defs>
              <pattern id="hachura" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
                <rect width="6" height="6" fill="#fff" />
                <line x1="0" y1="0" x2="0" y2="6" stroke={CINZA} strokeWidth="2" />
              </pattern>
            </defs>
            <CartesianGrid stroke="#e2e8f0" vertical={false} />
            {faixas.map((f) => (
              <ReferenceArea key={f.era} x1={f.x1} x2={f.x2} fill={f.cor} fillOpacity={0.14} stroke="none" ifOverflow="extendDomain" />
            ))}
            {imaturas.map((f) => (
              <ReferenceArea
                key={`im-${f.x1}`}
                x1={f.x1}
                x2={f.x2}
                fill="url(#hachura)"
                fillOpacity={0.9}
                stroke={CINZA}
                strokeDasharray="3 3"
                label={{ value: t("imatura.rotulo"), position: "insideTopRight", fontSize: 11, fill: "#334155" }}
              />
            ))}
            <XAxis dataKey="periodo" tickFormatter={(p: string) => linhas.find((l) => l.periodo === p)?.rotulo ?? p} interval="preserveStartEnd" minTickGap={16} tick={{ fontSize: 11 }} />
            <YAxis width={LARGURA_Y} unit="%" tick={{ fontSize: 11 }} domain={[0, "auto"]} label={{ value: t("retencao.eixoY"), angle: -90, position: "insideLeft", fontSize: 11, dx: 4 }} />
            <Tooltip cursor={{ stroke: AZUL, strokeDasharray: "3 3" }} content={({ payload }) => (payload && payload[0] ? <DicaCoorte linha={payload[0].payload as LinhaGrafico} /> : null)} />
            <Area type="monotone" dataKey="icBase" stackId="ic" stroke="none" fill="transparent" isAnimationActive={false} connectNulls={false} legendType="none" />
            <Area type="monotone" dataKey="icAltura" stackId="ic" stroke="none" fill={AZUL} fillOpacity={0.16} isAnimationActive={anima} animationDuration={400} connectNulls={false} legendType="none" />
            <Line type="monotone" dataKey="mm4" stroke={LARANJA} strokeWidth={2} strokeDasharray="6 4" dot={false} isAnimationActive={anima} animationDuration={400} connectNulls />
            <Line type="monotone" dataKey="taxa" stroke={AZUL} strokeWidth={2} dot={<Ponto />} activeDot={<PontoAtivo />} isAnimationActive={anima} animationDuration={400} connectNulls={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <h3 className="mt-3 text-sm font-medium text-slate-800">{t("retencao.tituloBarras")}</h3>
      <div role="img" aria-label={t("retencao.eixoYBarras")} className="h-36 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={linhas} margin={MARGEM}>
            <CartesianGrid stroke="#e2e8f0" vertical={false} />
            <XAxis dataKey="periodo" tickFormatter={(p: string) => linhas.find((l) => l.periodo === p)?.rotulo ?? p} interval="preserveStartEnd" minTickGap={16} tick={{ fontSize: 11 }} label={{ value: eixoX, position: "insideBottom", offset: -2, fontSize: 11 }} height={34} />
            <YAxis width={LARGURA_Y} tick={{ fontSize: 11 }} label={{ value: t("retencao.eixoYBarras"), angle: -90, position: "insideLeft", fontSize: 11, dx: 4 }} />
            <Tooltip content={({ payload }) => (payload && payload[0] ? <DicaCoorte linha={payload[0].payload as LinhaGrafico} /> : null)} />
            <Bar dataKey="novos" fill={AZUL} fillOpacity={0.55} isAnimationActive={anima} animationDuration={300} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <ul className="mt-3 space-y-1 text-xs text-slate-700" aria-label={t("retencao.legendaTitulo")}>
        <li className="font-medium">{t("retencao.legendaTitulo")}</li>
        <li>{t("retencao.legTaxa")}</li>
        <li>{t("retencao.legFaixa")}</li>
        <li>{t("retencao.legMedia")}</li>
        <li>{t("retencao.legPequena")}</li>
        {linhas.some((l) => l.inicioColeta) ? <li>{t("retencao.legInicioColeta")}</li> : null}
        <li>{t("retencao.legImatura")}</li>
        {faixas.length > 0 ? <li>{t("retencao.legEras")}:</li> : null}
        {faixas.map((f) => (
          <li key={f.era} className="flex items-center gap-2 pl-3">
            <span aria-hidden className="inline-block h-3 w-3 rounded-sm border border-slate-300" style={{ background: f.cor, opacity: 0.5 }} />
            <span>{f.descricao}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
