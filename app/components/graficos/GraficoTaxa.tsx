"use client";

import { Area, ComposedChart, Line, ReferenceArea, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { faixasImaturas, type LinhaGrafico } from "@/lib/graficos";
import { t } from "@/lib/mensagens";
import { useMovimentoReduzido } from "@/lib/movimento";
import { DicaCoorte } from "./DicaCoorte";

const VIOLETA = "#6a48eb";
const LARANJA = "#ff6c0e";
const CINZA = "#8a8f98";

interface PontoProps {
  cx?: number;
  cy?: number;
  payload?: LinhaGrafico;
}

/** Só marca o que precisa de aviso: amostra pequena (ou início da coleta) vira círculo cinza vazado; os demais pontos ficam limpos. */
function Ponto({ cx, cy, payload }: PontoProps) {
  if (cx === undefined || cy === undefined || !payload || payload.taxa === null) return <g />;
  if (payload.amostraOk && !payload.inicioColeta) return <g />;
  return <circle cx={cx} cy={cy} r={3.5} fill="#fff" stroke={CINZA} strokeWidth={1.5} />;
}

function PontoAtivo({ cx, cy, payload }: PontoProps) {
  if (cx === undefined || cy === undefined || !payload || payload.taxa === null) return <g />;
  return <circle cx={cx} cy={cy} r={6} fill="#fff" stroke={payload.amostraOk && !payload.inicioColeta ? VIOLETA : CINZA} strokeWidth={3} />;
}

/** Gráfico principal da Tela 1: taxa por semana com a margem de erro e a média de 4 semanas. Sem faixas de fundo, sem grade vertical, legenda de 3 itens. */
export function GraficoTaxa({ linhas, altura = "h-60" }: { linhas: LinhaGrafico[]; altura?: string }) {
  const anima = !useMovimentoReduzido();
  const imaturas = faixasImaturas(linhas);
  return (
    <div>
      <div role="img" aria-label={t("painel.tela1.graficoTitulo")} className={`${altura} w-full`}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={linhas} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
            <defs>
              <pattern id="hachura-painel" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
                <rect width="6" height="6" fill="#fff" />
                <line x1="0" y1="0" x2="0" y2="6" stroke={CINZA} strokeWidth="2" />
              </pattern>
            </defs>
            {imaturas.map((f) => (
              <ReferenceArea key={`im-${f.x1}`} x1={f.x1} x2={f.x2} fill="url(#hachura-painel)" fillOpacity={0.9} stroke="none" label={{ value: t("painel.tela1.emAndamento"), position: "insideTopRight", fontSize: 10, fill: "#475569" }} />
            ))}
            <XAxis dataKey="periodo" tickFormatter={(p: string) => linhas.find((l) => l.periodo === p)?.rotulo ?? p} interval="preserveStartEnd" minTickGap={48} tick={{ fontSize: 11, fill: "#475569" }} tickLine={false} axisLine={{ stroke: "#cbd5e1" }} />
            <YAxis width={40} unit="%" tick={{ fontSize: 11, fill: "#475569" }} domain={[0, "auto"]} tickCount={4} tickLine={false} axisLine={false} />
            <Tooltip cursor={{ stroke: VIOLETA, strokeDasharray: "3 3" }} content={({ payload }) => (payload && payload[0] ? <DicaCoorte linha={payload[0].payload as LinhaGrafico} /> : null)} />
            <Area type="monotone" dataKey="icBase" stackId="ic" stroke="none" fill="transparent" isAnimationActive={false} connectNulls={false} legendType="none" />
            <Area type="monotone" dataKey="icAltura" stackId="ic" stroke="none" fill={VIOLETA} fillOpacity={0.16} isAnimationActive={anima} animationDuration={400} connectNulls={false} legendType="none" />
            <Line type="monotone" dataKey="mm4" stroke={LARANJA} strokeWidth={2} strokeDasharray="6 4" dot={false} isAnimationActive={anima} animationDuration={400} connectNulls />
            <Line type="monotone" dataKey="taxa" stroke={VIOLETA} strokeWidth={2} dot={<Ponto />} activeDot={<PontoAtivo />} isAnimationActive={anima} animationDuration={400} connectNulls={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <ul className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-700" aria-label="Legenda">
        <li className="flex items-center gap-1.5"><span aria-hidden className="inline-block h-0.5 w-4 bg-violeta" />{t("painel.tela1.legTaxa")}</li>
        <li className="flex items-center gap-1.5"><span aria-hidden className="inline-block h-3 w-4 rounded-sm bg-violeta/20" />{t("painel.tela1.legFaixa")}</li>
        <li className="flex items-center gap-1.5"><span aria-hidden className="inline-block w-4 border-t-2 border-dashed border-laranja" />{t("painel.tela1.legMedia")}</li>
      </ul>
    </div>
  );
}
