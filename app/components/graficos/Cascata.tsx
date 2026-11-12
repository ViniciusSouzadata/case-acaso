"use client";

import { Bar, BarChart, Cell, CartesianGrid, LabelList, ResponsiveContainer, XAxis, YAxis } from "recharts";
import type { DegrauCascata } from "@/lib/graficos";
import { t } from "@/lib/mensagens";
import { formatarPP, formatarPct } from "@/lib/regras";

const AZUL = "#0072b2";
const VERDE = "#009e73";
const VERMELHO = "#d55e00";

const NOMES: Record<DegrauCascata["chave"], string> = {
  base: "semana.degrauBase",
  mix: "semana.degrauMix",
  taxa: "semana.degrauTaxa",
  semana: "semana.degrauSemana",
};

/** Nome da categoria quebrado por palavra, para caber em telas estreitas (390 px). */
function TickQuebrado({ x, y, payload }: { x?: number; y?: number; payload?: { value: string } }) {
  const partes = String(payload?.value ?? "").split(" ");
  return (
    <text x={x} y={y} textAnchor="middle" fontSize={10} fill="#475569">
      {partes.map((p, i) => (
        <tspan key={i} x={x} dy={i === 0 ? 12 : 11}>{p}</tspan>
      ))}
    </text>
  );
}

/** Cascata: barras flutuantes (base invisível + altura). */
export function Cascata({ degraus }: { degraus: DegrauCascata[] }) {
  const dados = degraus.map((d) => ({
    rotulo: t(NOMES[d.chave]),
    inicio: Math.min(d.de, d.ate),
    altura: Math.abs(d.ate - d.de),
    cor: d.total ? AZUL : d.valor >= 0 ? VERDE : VERMELHO,
    texto: d.total ? formatarPct(d.valor / 100) : formatarPP(d.valor),
  }));
  return (
    <div role="img" aria-label={dados.map((d) => `${d.rotulo}: ${d.texto}`).join("; ")} className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={dados} margin={{ top: 22, right: 16, bottom: 4, left: 8 }}>
          <CartesianGrid stroke="#e2e8f0" vertical={false} />
          <XAxis dataKey="rotulo" tick={<TickQuebrado />} interval={0} height={40} />
          <YAxis width={52} unit="%" tick={{ fontSize: 11 }} domain={[0, "auto"]} label={{ value: t("semana.eixo"), angle: -90, position: "insideLeft", fontSize: 11, dx: 4 }} />
          <Bar dataKey="inicio" stackId="c" fill="transparent" isAnimationActive={false} />
          <Bar dataKey="altura" stackId="c" isAnimationActive={false}>
            {dados.map((d) => (
              <Cell key={d.rotulo} fill={d.cor} />
            ))}
            <LabelList dataKey="texto" position="top" style={{ fontSize: 11, fill: "#0f172a" }} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
