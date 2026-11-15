"use client";

import { useEffect, useState } from "react";
import { Bar, BarChart, Cell, CartesianGrid, LabelList, ResponsiveContainer, XAxis, YAxis } from "recharts";
import type { DegrauCascata } from "@/lib/graficos";
import { t } from "@/lib/mensagens";
import { useMovimentoReduzido } from "@/lib/movimento";
import { numeroGrande } from "@/lib/painel";
import { formatarPP, formatarPct } from "@/lib/regras";

const CINZA = "#8a8f98"; // semana base
const VIOLETA = "#6a48eb"; // semana analisada
const VIOLETA_CLARO = "#978df8"; // causa que soma
const LARANJA = "#ff6c0e"; // causa que tira (destaque)
const PASSO_MS = 260;

const NOMES: Record<DegrauCascata["chave"], string> = {
  base: "semana.degrauBase",
  mix: "semana.degrauMix",
  taxa: "semana.degrauTaxa",
  semana: "semana.degrauSemana",
};

function corDoDegrau(d: DegrauCascata): string {
  if (d.total) return d.chave === "base" ? CINZA : VIOLETA;
  return d.valor >= 0 ? VIOLETA_CLARO : LARANJA;
}

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

/** Cascata: barras flutuantes (base invisível + altura). Monta em etapas (base → quem chegou → comportamento → final); sem animação com movimento reduzido. */
export function Cascata({ degraus, altura = "h-64", semJargao = false }: { degraus: DegrauCascata[]; altura?: string; semJargao?: boolean }) {
  const reduzido = useMovimentoReduzido();
  const [etapa, setEtapa] = useState(degraus.length);

  useEffect(() => {
    if (reduzido) {
      setEtapa(degraus.length);
      return;
    }
    setEtapa(1);
    const ids = degraus.slice(1).map((_, i) => window.setTimeout(() => setEtapa(i + 2), (i + 1) * PASSO_MS));
    return () => ids.forEach((id) => window.clearTimeout(id));
  }, [degraus, reduzido]);

  const visivel = reduzido ? degraus.length : etapa;
  // sem jargão: "−4,4" em vez de "−4,4 p.p." (a unidade vai no eixo e na frase)
  const fmtDelta = (v: number) => (semJargao ? numeroGrande(v) : formatarPP(v));
  const dados = degraus.map((d, i) => ({
    rotulo: t(NOMES[d.chave]),
    inicio: i < visivel ? Math.min(d.de, d.ate) : 0,
    altura: i < visivel ? Math.abs(d.ate - d.de) : 0,
    cor: corDoDegrau(d),
    texto: i < visivel ? (d.total ? formatarPct(d.valor / 100) : fmtDelta(d.valor)) : "",
    textoFinal: d.total ? formatarPct(d.valor / 100) : fmtDelta(d.valor),
  }));
  return (
    <div role="img" aria-label={dados.map((d) => `${d.rotulo}: ${d.textoFinal}`).join("; ")} className={`${altura} w-full`}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={dados} margin={{ top: 22, right: 16, bottom: 4, left: 8 }}>
          <CartesianGrid stroke="#e2e8f0" vertical={false} />
          <XAxis dataKey="rotulo" tick={<TickQuebrado />} interval={0} height={40} />
          <YAxis width={52} unit="%" tick={{ fontSize: 11 }} domain={[0, "auto"]} label={{ value: t("semana.eixo"), angle: -90, position: "insideLeft", fontSize: 11, dx: 4 }} />
          <Bar dataKey="inicio" stackId="c" fill="transparent" isAnimationActive={false} />
          <Bar dataKey="altura" stackId="c" isAnimationActive={!reduzido} animationDuration={240} radius={[3, 3, 0, 0]}>
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
