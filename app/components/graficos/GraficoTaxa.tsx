"use client";

import { Area, CartesianGrid, ComposedChart, Line, ReferenceArea, ReferenceDot, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { faixasImaturas, type LinhaGrafico } from "@/lib/graficos";
import { t } from "@/lib/mensagens";
import { useMovimentoReduzido } from "@/lib/movimento";
import { DicaCoorte } from "./DicaCoorte";

const VIOLETA = "#6a48eb";
const LARANJA = "#ff6c0e";
const CINZA = "#8a8f98";
const GRAFITE = "#475569"; // média de 4 semanas: cinza escuro, contínua e fina (laranja fica para "diferença real")
const TETO = 60; // a linha vive entre 0 e ~55%; a faixa que passar do teto é cortada na borda

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
export function GraficoTaxa({
  linhas,
  altura = "h-60",
  marcadas = [],
  selecionada,
  onEscolher,
}: {
  linhas: LinhaGrafico[];
  altura?: string;
  /** semanas que a decomposição explica: marcadas no gráfico e clicáveis (só com amostra suficiente) */
  marcadas?: string[];
  selecionada?: string;
  onEscolher?: (periodo: string) => void;
}) {
  const anima = !useMovimentoReduzido();
  // só desenha o "em andamento" quando há área visível (pelo menos dois pontos); um período solto não tem onde ficar
  const imaturas = faixasImaturas(linhas).filter((f) => f.x1 !== f.x2);
  const temMedia = linhas.some((l) => l.mm4 !== null);
  const temPoucaGente = linhas.some((l) => l.taxa !== null && (!l.amostraOk || l.inicioColeta));
  // amostra pequena nunca vira ponto clicável "firme"
  const clicaveis = linhas.filter((l) => marcadas.includes(l.periodo) && l.amostraOk && l.taxa !== null);
  const escolher = (p: string | undefined) => {
    if (p && onEscolher && clicaveis.some((l) => l.periodo === p)) onEscolher(p);
  };
  return (
    <div>
      <div role="img" aria-label={t("painel.tela1.graficoTitulo")} className={`${altura} w-full`}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={linhas} margin={{ top: 14, right: 12, bottom: 0, left: 0 }} onClick={(e) => escolher(typeof e?.activeLabel === "string" ? e.activeLabel : undefined)} style={clicaveis.length > 0 ? { cursor: "pointer" } : undefined}>
            <defs>
              <pattern id="hachura-painel" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
                <rect width="6" height="6" fill="#fff" />
                <line x1="0" y1="0" x2="0" y2="6" stroke={CINZA} strokeWidth="2" />
              </pattern>
            </defs>
            {imaturas.map((f) => (
              <ReferenceArea key={`im-${f.x1}`} x1={f.x1} x2={f.x2} fill="url(#hachura-painel)" fillOpacity={0.9} stroke="none" label={{ value: t("painel.tela1.emAndamento"), position: "insideTopRight", fontSize: 10, fill: "#475569" }} />
            ))}
            <CartesianGrid stroke="#eef0f4" vertical={false} />
            <XAxis dataKey="periodo" tickFormatter={(p: string) => linhas.find((l) => l.periodo === p)?.rotulo ?? p} interval="preserveStartEnd" minTickGap={48} tick={{ fontSize: 11, fill: "#475569" }} tickLine={false} axisLine={{ stroke: "#cbd5e1" }} />
            <YAxis width={40} unit="%" tick={{ fontSize: 11, fill: "#475569" }} domain={[0, TETO]} ticks={[0, 20, 40, 60]} allowDataOverflow tickLine={false} axisLine={false} />
            <Tooltip cursor={{ stroke: VIOLETA }} content={({ payload }) => (payload && payload[0] ? <DicaCoorte linha={payload[0].payload as LinhaGrafico} clicavel={clicaveis.some((l) => l.periodo === (payload[0]!.payload as LinhaGrafico).periodo)} /> : null)} />
            <Area type="monotone" dataKey="icBase" stackId="ic" stroke="none" fill="transparent" isAnimationActive={false} connectNulls={false} legendType="none" />
            <Area type="monotone" dataKey="icAltura" stackId="ic" stroke="none" fill={VIOLETA} fillOpacity={0.16} isAnimationActive={anima} animationDuration={400} connectNulls={false} legendType="none" />
            <Line type="monotone" dataKey="mm4" stroke={GRAFITE} strokeWidth={1.5} dot={false} isAnimationActive={anima} animationDuration={400} connectNulls />
            <Line type="monotone" dataKey="taxa" stroke={VIOLETA} strokeWidth={2} dot={<Ponto />} activeDot={<PontoAtivo />} isAnimationActive={anima} animationDuration={400} connectNulls={false} />
            {clicaveis.map((l) => (
              <ReferenceDot
                key={`m-${l.periodo}`}
                x={l.periodo}
                y={l.taxa!}
                r={l.periodo === selecionada ? 7 : 6}
                fill={l.periodo === selecionada ? VIOLETA : "#fff"}
                stroke={VIOLETA}
                strokeWidth={3}
                ifOverflow="visible"
                label={{ value: t("painel.tela1.rotuloMarca"), position: "top", fontSize: 10, fill: "#583ecb" }}
                style={{ cursor: "pointer" }}
                onClick={() => escolher(l.periodo)}
              />
            ))}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <ul className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-700" aria-label="Legenda">
        <li className="flex items-center gap-1.5"><span aria-hidden className="inline-block h-0.5 w-4 bg-violeta" />{t(temPoucaGente ? "painel.tela1.legTaxa" : "painel.tela1.legTaxaSimples")}</li>
        <li className="flex items-center gap-1.5"><span aria-hidden className="inline-block h-3 w-4 rounded-sm bg-violeta/20" />{t("painel.tela1.legFaixa")}</li>
        {temMedia ? <li className="flex items-center gap-1.5"><span aria-hidden className="inline-block w-4 border-t-[1.5px] border-slate-600" />{t("painel.tela1.legMedia")}</li> : null}
        {clicaveis.length > 0 ? <li className="flex items-center gap-1.5"><span aria-hidden className="inline-block h-3 w-3 rounded-full border-[3px] border-violeta bg-white" />{t("painel.tela1.legMarcada")}</li> : null}
      </ul>
    </div>
  );
}
